"""
Lambda function to check system status and statistics.
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
sources_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_DATA_SOURCES', 'data_sources'))
notifications_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NOTIFICATIONS', 'notifications'))
sync_state_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_SYNC_STATE', 'sync_state'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get system status and statistics.
    
    Routes:
    - GET /stats - Get statistics
    - GET /status - Get system status
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        headers = event.get('headers', {})
        
        # CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        }
        
        # Handle OPTIONS request
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Get user from token (simplified for MVP)
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Unauthorized'})
            }
        
        # TODO: Extract user_id from JWT token
        # For MVP, we'll get all stats (in production, filter by user_id)
        
        if path == '/stats' and http_method == 'GET':
            return handle_get_stats(cors_headers)
        elif path == '/status' and http_method == 'GET':
            return handle_get_status(cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Not found'})
            }
            
    except Exception as e:
        logger.error(f"Error in status-check: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers if 'cors_headers' in locals() else {},
            'body': json.dumps({'message': 'Internal server error'})
        }


def handle_get_stats(cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Get statistics."""
    try:
        # Count active sources
        sources_response = sources_table.scan(
            FilterExpression='status = :status',
            ExpressionAttributeValues={':status': 'active'}
        )
        active_sources = len(sources_response.get('Items', []))
        
        # Count total notifications (approximate)
        notifications_response = notifications_table.scan(Select='COUNT')
        total_emails = notifications_response.get('Count', 0)
        
        # Count delivered notifications
        delivered_response = notifications_table.scan(
            FilterExpression='attribute_exists(delivered_at)',
            Select='COUNT'
        )
        notifications_sent = delivered_response.get('Count', 0)
        
        # Get last sync time
        sync_response = sync_state_table.scan()
        last_sync = None
        if sync_response.get('Items'):
            sync_times = [item.get('last_sync_timestamp') for item in sync_response['Items'] if item.get('last_sync_timestamp')]
            if sync_times:
                last_sync = max(sync_times)
        
        stats = {
            'total_emails': total_emails,
            'active_sources': active_sources,
            'notifications_sent': notifications_sent,
            'last_sync': last_sync
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(stats)
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }


def handle_get_status(cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Get system status."""
    try:
        # Check processing status (active if recent syncs)
        sync_response = sync_state_table.scan()
        processing_active = False
        next_run = None
        
        if sync_response.get('Items'):
            sync_times = [item.get('last_sync_timestamp') for item in sync_response['Items'] if item.get('last_sync_timestamp')]
            if sync_times:
                last_sync = max(sync_times)
                try:
                    last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                    # Consider active if synced within last 20 minutes
                    time_diff = (datetime.utcnow() - last_sync_dt.replace(tzinfo=None)).total_seconds()
                    processing_active = time_diff < 1200  # 20 minutes
                except:
                    pass
        
        # Next run is approximately 15 minutes from now (EventBridge schedule)
        from datetime import timedelta
        next_run = (datetime.utcnow() + timedelta(minutes=15)).isoformat() + 'Z'
        
        # LLM status (simplified - assume connected if API key exists)
        llm_connected = bool(os.environ.get('LLM_API_KEY', ''))
        
        status = {
            'processing_active': processing_active,
            'next_run': next_run,
            'llm_connected': llm_connected
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(status)
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Error getting status'})
        }

