"""
Lambda function to deliver notifications via SMS or Email.
Triggered by SQS queue when summaries are ready.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_USERS', 'users'))
notifications_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NOTIFICATIONS', 'notifications'))
ses = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Configuration
SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', '')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')


def send_email_via_ses(to_email: str, subject: str, body: str) -> bool:
    """Send email via AWS SES."""
    try:
        response = ses.send_email(
            Source=SES_FROM_EMAIL,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        logger.info(f"Email sent to {to_email}: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Error sending email: {e}")
        return False


def send_sms_via_twilio(to_number: str, message: str) -> bool:
    """Send SMS via Twilio."""
    try:
        import httpx
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        
        response = httpx.post(
            url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data={
                'From': TWILIO_FROM_NUMBER,
                'To': to_number,
                'Body': message
            },
            timeout=30.0
        )
        
        if response.status_code == 201:
            logger.info(f"SMS sent to {to_number}")
            return True
        else:
            logger.error(f"Twilio error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Deliver notifications to users.
    Triggered by SQS queue.
    """
    try:
        # Process SQS records
        records = event.get('Records', [])
        
        for record in records:
            try:
                body = json.loads(record['body'])
                user_id = body.get('user_id')
                summary = body.get('summary', '')
                notification_count = body.get('notification_count', 0)
                
                if not user_id:
                    logger.warning("Missing user_id in SQS message")
                    continue
                
                # Get user preferences
                user_response = users_table.get_item(Key={'user_id': user_id})
                if 'Item' not in user_response:
                    logger.warning(f"User {user_id} not found")
                    continue
                
                user = user_response['Item']
                
                # Get notification preferences (from settings table or user defaults)
                notification_method = user.get('notification_method', 'email')
                notification_email = user.get('notification_email') or user.get('email')
                notification_phone = user.get('notification_phone') or user.get('phone')
                
                # Prepare message
                subject = f"Notification Summary ({notification_count} new items)"
                message = f"You have {notification_count} new notification(s):\n\n{summary}"
                
                # Deliver based on method
                delivered = False
                delivery_method = None
                
                if notification_method in ['email', 'both'] and notification_email:
                    delivered = send_email_via_ses(notification_email, subject, message)
                    delivery_method = 'email' if delivered else None
                
                if notification_method in ['sms', 'both'] and notification_phone and not delivered:
                    delivered = send_sms_via_twilio(notification_phone, message[:160])  # SMS limit
                    delivery_method = 'sms' if delivered else None
                
                if delivered:
                    # Update notification delivery status
                    # Get recent notifications for this user
                    response = notifications_table.query(
                        KeyConditionExpression='user_id = :user_id',
                        FilterExpression='attribute_not_exists(delivered_at)',
                        ExpressionAttributeValues={':user_id': user_id},
                        Limit=notification_count
                    )
                    
                    now = datetime.utcnow().isoformat() + 'Z'
                    for notif in response.get('Items', []):
                        notifications_table.update_item(
                            Key={
                                'user_id': notif['user_id'],
                                'notification_id': notif['notification_id']
                            },
                            UpdateExpression='SET delivered_at = :delivered_at, delivery_method = :delivery_method',
                            ExpressionAttributeValues={
                                ':delivered_at': now,
                                ':delivery_method': delivery_method
                            }
                        )
                    
                    logger.info(f"Notification delivered to user {user_id} via {delivery_method}")
                else:
                    logger.warning(f"Failed to deliver notification to user {user_id}")
                
            except Exception as e:
                logger.error(f"Error processing SQS record: {e}", exc_info=True)
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Delivery complete'})
        }
        
    except Exception as e:
        logger.error(f"Error in deliver: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Delivery failed'})
        }

