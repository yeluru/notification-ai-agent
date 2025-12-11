"""
Lambda function to summarize notifications using LLM.
Triggered by SQS queue when new notifications arrive.
"""

import json
import os
import logging
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
notifications_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NOTIFICATIONS', 'notifications'))
sqs = boto3.client('sqs')

# LLM configuration
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')

# SQS queue for delivery
DELIVERY_QUEUE_URL = os.environ.get('DELIVERY_QUEUE_URL', '')


def call_llm(messages: List[Dict[str, str]]) -> str:
    """
    Call LLM API to generate summary.
    """
    try:
        import httpx
        
        headers = {
            'Authorization': f'Bearer {LLM_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': LLM_MODEL,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 200
        }
        
        response = httpx.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            logger.error(f"LLM API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return None


def summarize_notifications(notifications: List[Dict[str, Any]]) -> str:
    """
    Summarize a list of notifications.
    """
    if not notifications:
        return "No new notifications."
    
    # Build prompt
    email_texts = []
    for notif in notifications:
        subject = notif.get('subject', 'No subject')
        from_addr = notif.get('from', 'Unknown')
        content = notif.get('content', '')[:200]  # Limit content
        email_texts.append(f"From: {from_addr}\nSubject: {subject}\n{content}")
    
    prompt = f"""Summarize the following emails concisely in 2-3 sentences each:

{chr(10).join(email_texts)}

Provide a brief summary for each email, focusing on key information."""

    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant that summarizes emails concisely.'},
        {'role': 'user', 'content': prompt}
    ]
    
    summary = call_llm(messages)
    return summary or "Unable to generate summary."


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Summarize notifications for a user.
    Triggered by SQS queue.
    """
    try:
        # Process SQS records
        records = event.get('Records', [])
        
        for record in records:
            try:
                body = json.loads(record['body'])
                user_id = body.get('user_id')
                source_id = body.get('source_id')
                
                if not user_id:
                    logger.warning("Missing user_id in SQS message")
                    continue
                
                # Get recent notifications for this user/source
                response = notifications_table.query(
                    KeyConditionExpression='user_id = :user_id',
                    FilterExpression='source_id = :source_id AND attribute_not_exists(summary)',
                    ExpressionAttributeValues={
                        ':user_id': user_id,
                        ':source_id': source_id
                    },
                    Limit=10,
                    ScanIndexForward=False  # Newest first
                )
                
                notifications = response.get('Items', [])
                
                if not notifications:
                    logger.info(f"No notifications to summarize for user {user_id}")
                    continue
                
                # Generate summary
                summary = summarize_notifications(notifications)
                
                # Update notifications with summary
                for notif in notifications:
                    notifications_table.update_item(
                        Key={
                            'user_id': notif['user_id'],
                            'notification_id': notif['notification_id']
                        },
                        UpdateExpression='SET summary = :summary',
                        ExpressionAttributeValues={':summary': summary}
                    )
                
                # Send to delivery queue
                if DELIVERY_QUEUE_URL:
                    sqs.send_message(
                        QueueUrl=DELIVERY_QUEUE_URL,
                        MessageBody=json.dumps({
                            'user_id': user_id,
                            'summary': summary,
                            'notification_count': len(notifications)
                        })
                    )
                
                logger.info(f"Summarized {len(notifications)} notifications for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error processing SQS record: {e}", exc_info=True)
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Summarization complete'})
        }
        
    except Exception as e:
        logger.error(f"Error in summarize: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Summarization failed'})
        }

