"""
Lambda function to process notifications from all active data sources.
Triggered by EventBridge every 10-15 minutes.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sources_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_DATA_SOURCES', 'data_sources'))
notifications_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NOTIFICATIONS', 'notifications'))
sync_state_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_SYNC_STATE', 'sync_state'))
secrets_manager = boto3.client('secretsmanager')
sqs = boto3.client('sqs')

# SQS queue for summarization
SUMMARIZATION_QUEUE_URL = os.environ.get('SUMMARIZATION_QUEUE_URL', '')


def decrypt_credentials(secret_arn: str) -> str:
    """Retrieve credentials from AWS Secrets Manager."""
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_arn)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise


def fetch_emails_imap(email: str, password: str, host: str, port: int, use_ssl: bool, since_date: datetime = None) -> List[Dict[str, Any]]:
    """
    Fetch unread emails from IMAP server.
    Returns list of email notifications.
    """
    try:
        import imaplib
        import email
        from email.header import decode_header
        
        # Connect to IMAP server
        if use_ssl:
            mail = imaplib.IMAP4_SSL(host, port)
        else:
            mail = imaplib.IMAP4(host, port)
        
        mail.login(email, password)
        mail.select('INBOX')
        
        # Search for unread emails
        search_criteria = ['UNSEEN']
        if since_date:
            date_str = since_date.strftime("%d-%b-%Y")
            search_criteria.append(f"SINCE {date_str}")
        
        status, message_numbers = mail.search(None, ' '.join(search_criteria))
        
        if status != 'OK':
            logger.warning(f"IMAP search failed for {email}")
            return []
        
        message_ids = message_numbers[0].split()
        message_ids.reverse()  # Newest first
        message_ids = message_ids[:10]  # Top 10 only
        
        notifications = []
        
        for msg_id in message_ids:
            try:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Parse headers
                subject = email_message['Subject']
                from_addr = email_message['From']
                date_str = email_message['Date']
                
                # Decode subject
                if subject:
                    decoded_subject = decode_header(subject)[0]
                    if isinstance(decoded_subject[0], bytes):
                        subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
                    else:
                        subject = decoded_subject[0]
                
                # Parse date
                try:
                    from email.utils import parsedate_to_datetime
                    received_at = parsedate_to_datetime(date_str) if date_str else datetime.utcnow()
                except:
                    received_at = datetime.utcnow()
                
                # Filter by exact timestamp if since_date provided
                if since_date and received_at.replace(tzinfo=None) <= since_date:
                    continue
                
                # Get email body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                notification = {
                    'source_type': 'email',
                    'source_id': email,
                    'subject': subject or '',
                    'from': from_addr or '',
                    'content': body[:500],  # Limit content size
                    'received_at': received_at.isoformat(),
                    'message_id': email_message.get('Message-ID', '')
                }
                
                notifications.append(notification)
                
            except Exception as e:
                logger.error(f"Error processing email {msg_id}: {e}")
                continue
        
        mail.logout()
        return notifications
        
    except Exception as e:
        logger.error(f"Error fetching emails from {email}: {e}")
        return []


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process notifications from all active data sources.
    Triggered by EventBridge schedule.
    """
    try:
        logger.info("Starting notification processing...")
        
        # Get all active data sources
        response = sources_table.scan(
            FilterExpression='status = :status',
            ExpressionAttributeValues={':status': 'active'}
        )
        
        active_sources = response.get('Items', [])
        logger.info(f"Found {len(active_sources)} active data sources")
        
        total_new_notifications = 0
        
        for source in active_sources:
            user_id = source['user_id']
            source_id = source['source_id']
            source_type = source.get('source_type', 'email')
            
            try:
                # Get last sync timestamp
                sync_response = sync_state_table.get_item(
                    Key={'user_id': user_id, 'source_id': source_id}
                )
                
                since_date = None
                if 'Item' in sync_response:
                    last_sync_str = sync_response['Item'].get('last_sync_timestamp')
                    if last_sync_str:
                        try:
                            since_date = datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))
                            since_date = since_date.replace(tzinfo=None)
                        except:
                            # Default to 15 minutes ago if parsing fails
                            since_date = datetime.utcnow() - timedelta(minutes=15)
                else:
                    # First sync - only get emails from last 15 minutes
                    since_date = datetime.utcnow() - timedelta(minutes=15)
                
                # Fetch notifications based on source type
                notifications = []
                if source_type == 'email':
                    email = source.get('email')
                    secret_arn = source.get('credentials_secret_arn')
                    host = source.get('host')
                    port = source.get('port', 993)
                    use_ssl = source.get('use_ssl', True)
                    
                    if not email or not secret_arn:
                        logger.warning(f"Missing email or credentials for source {source_id}")
                        continue
                    
                    password = decrypt_credentials(secret_arn)
                    notifications = fetch_emails_imap(email, password, host, port, use_ssl, since_date)
                
                logger.info(f"Found {len(notifications)} new notifications from {source_id}")
                
                # Store notifications in DynamoDB
                for notification in notifications:
                    notification_id = notification.get('message_id') or f"{source_id}_{datetime.utcnow().timestamp()}"
                    
                    notification_item = {
                        'user_id': user_id,
                        'notification_id': notification_id,
                        'source_type': source_type,
                        'source_id': source_id,
                        'content': notification.get('content', ''),
                        'subject': notification.get('subject', ''),
                        'from': notification.get('from', ''),
                        'created_at': notification.get('received_at', datetime.utcnow().isoformat() + 'Z'),
                        'delivered_at': None,
                        'delivery_method': None
                    }
                    
                    try:
                        notifications_table.put_item(Item=notification_item)
                        total_new_notifications += 1
                    except ClientError as e:
                        logger.error(f"Error storing notification: {e}")
                        continue
                
                # Update sync state
                now = datetime.utcnow().isoformat() + 'Z'
                sync_state_table.put_item(
                    Item={
                        'user_id': user_id,
                        'source_id': source_id,
                        'last_sync_timestamp': now,
                        'last_processed_item_id': notification_id if notifications else None,
                        'error_count': 0,
                        'last_error': None
                    }
                )
                
                # Trigger summarization if new notifications found
                if notifications:
                    # Send message to summarization queue
                    if SUMMARIZATION_QUEUE_URL:
                        sqs.send_message(
                            QueueUrl=SUMMARIZATION_QUEUE_URL,
                            MessageBody=json.dumps({
                                'user_id': user_id,
                                'source_id': source_id,
                                'notification_count': len(notifications)
                            })
                        )
                
            except Exception as e:
                logger.error(f"Error processing source {source_id}: {e}", exc_info=True)
                
                # Update sync state with error
                try:
                    sync_response = sync_state_table.get_item(
                        Key={'user_id': user_id, 'source_id': source_id}
                    )
                    error_count = 0
                    if 'Item' in sync_response:
                        error_count = sync_response['Item'].get('error_count', 0)
                    
                    sync_state_table.put_item(
                        Item={
                            'user_id': user_id,
                            'source_id': source_id,
                            'last_sync_timestamp': sync_response['Item'].get('last_sync_timestamp') if 'Item' in sync_response else None,
                            'error_count': error_count + 1,
                            'last_error': str(e)
                        }
                    )
                except:
                    pass
                continue
        
        logger.info(f"Processing complete. Total new notifications: {total_new_notifications}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processing complete',
                'total_new_notifications': total_new_notifications
            })
        }
        
    except Exception as e:
        logger.error(f"Error in process-notifications: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Processing failed'})
        }

