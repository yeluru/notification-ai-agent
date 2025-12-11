"""
Lambda function for data source configuration (add, update, delete email accounts).
"""

import json
import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sources_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_DATA_SOURCES', 'data_sources'))
secrets_manager = boto3.client('secretsmanager', config=Config(region_name=os.environ.get('AWS_REGION', 'us-east-1')))

# Get user from token (shared utility)
def get_user_from_token(headers: Dict[str, str]) -> Dict[str, Any]:
    """Extract user info from JWT token."""
    # In production, verify JWT token here
    # For now, we'll use a simple header check
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    # TODO: Verify JWT token and extract user_id
    # For now, extract from token (simplified)
    token = auth_header.replace('Bearer ', '')
    # In real implementation, decode JWT to get user_id
    # For MVP, we'll use email from token or require user_id in request
    return {'user_id': 'temp_user'}  # Placeholder


def encrypt_credentials(password: str, user_id: str) -> str:
    """
    Store credentials in AWS Secrets Manager.
    Returns the secret ARN.
    """
    secret_name = f"notification-agent/{user_id}/{uuid.uuid4()}"
    
    try:
        response = secrets_manager.create_secret(
            Name=secret_name,
            SecretString=password,
            Description=f"Email password for user {user_id}"
        )
        return response['ARN']
    except ClientError as e:
        logger.error(f"Error creating secret: {e}")
        raise


def decrypt_credentials(secret_arn: str) -> str:
    """Retrieve credentials from AWS Secrets Manager."""
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_arn)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle data source configuration requests.
    
    Routes:
    - GET /data-sources - List all data sources for user
    - POST /data-sources - Add new data source
    - PUT /data-sources/{id} - Update data source
    - DELETE /data-sources/{id} - Delete data source
    - POST /data-sources/{id}/test - Test data source connection
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        headers = event.get('headers', {})
        body = json.loads(event.get('body', '{}') or '{}')
        
        # CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }
        
        # Handle OPTIONS request
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Get user from token
        user = get_user_from_token(headers)
        if not user:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Unauthorized'})
            }
        
        user_id = user['user_id']
        
        # Route requests
        if path == '/data-sources' and http_method == 'GET':
            return handle_list_sources(user_id, cors_headers)
        elif path == '/data-sources' and http_method == 'POST':
            return handle_add_source(user_id, body, cors_headers)
        elif path.startswith('/data-sources/') and http_method == 'PUT':
            source_id = path_parameters.get('id') or path.split('/')[-1]
            return handle_update_source(user_id, source_id, body, cors_headers)
        elif path.startswith('/data-sources/') and http_method == 'DELETE':
            source_id = path_parameters.get('id') or path.split('/')[-1]
            return handle_delete_source(user_id, source_id, cors_headers)
        elif path.endswith('/test') and http_method == 'POST':
            source_id = path_parameters.get('id') or path.split('/')[-2]
            return handle_test_source(user_id, source_id, cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Not found'})
            }
            
    except Exception as e:
        logger.error(f"Error in data-source-config: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers if 'cors_headers' in locals() else {},
            'body': json.dumps({'message': 'Internal server error'})
        }


def handle_list_sources(user_id: str, cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """List all data sources for user."""
    try:
        response = sources_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        sources = []
        for item in response.get('Items', []):
            # Don't return password/credentials in list
            source = {
                'source_id': item['source_id'],
                'source_type': item.get('source_type', 'email'),
                'email': item.get('email'),
                'host': item.get('host'),
                'port': item.get('port', 993),
                'use_ssl': item.get('use_ssl', True),
                'status': item.get('status', 'active'),
                'last_sync_at': item.get('last_sync_at'),
                'created_at': item.get('created_at')
            }
            sources.append(source)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(sources)
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }


def handle_add_source(user_id: str, body: Dict[str, Any], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Add new data source."""
    source_type = body.get('source_type', 'email')
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    host = body.get('host', '').strip()
    port = int(body.get('port', 993))
    use_ssl = body.get('use_ssl', True)
    
    if not email or not password:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Email and password are required'})
        }
    
    # Auto-detect IMAP host if not provided
    if not host:
        if '@gmail.com' in email:
            host = 'imap.gmail.com'
        elif '@outlook.com' in email or '@hotmail.com' in email:
            host = 'imap-mail.outlook.com'
        elif '@yahoo.com' in email:
            host = 'imap.mail.yahoo.com'
        else:
            # Try to extract domain
            domain = email.split('@')[1] if '@' in email else ''
            host = f'imap.{domain}' if domain else 'imap.gmail.com'
    
    # Generate source ID
    source_id = str(uuid.uuid4())
    
    # Store password in Secrets Manager
    try:
        secret_arn = encrypt_credentials(password, user_id)
    except Exception as e:
        logger.error(f"Error storing credentials: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Failed to store credentials'})
        }
    
    # Store source configuration
    now = datetime.utcnow().isoformat() + 'Z'
    
    source_item = {
        'user_id': user_id,
        'source_id': source_id,
        'source_type': source_type,
        'email': email,
        'host': host,
        'port': port,
        'use_ssl': use_ssl,
        'credentials_secret_arn': secret_arn,
        'status': 'active',
        'created_at': now,
        'updated_at': now,
        'last_sync_at': None
    }
    
    try:
        sources_table.put_item(Item=source_item)
        
        # Return source (without password)
        source_response = {
            'source_id': source_id,
            'source_type': source_type,
            'email': email,
            'host': host,
            'port': port,
            'use_ssl': use_ssl,
            'status': 'active',
            'created_at': now
        }
        
        return {
            'statusCode': 201,
            'headers': cors_headers,
            'body': json.dumps(source_response)
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Failed to create data source'})
        }


def handle_update_source(user_id: str, source_id: str, body: Dict[str, Any], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Update data source."""
    try:
        # Get existing source
        response = sources_table.get_item(
            Key={'user_id': user_id, 'source_id': source_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Data source not found'})
            }
        
        # Build update expression
        update_expression_parts = []
        expression_attribute_values = {}
        
        if 'status' in body:
            update_expression_parts.append('status = :status')
            expression_attribute_values[':status'] = body['status']
        
        if 'host' in body:
            update_expression_parts.append('host = :host')
            expression_attribute_values[':host'] = body['host']
        
        if 'port' in body:
            update_expression_parts.append('port = :port')
            expression_attribute_values[':port'] = int(body['port'])
        
        if 'use_ssl' in body:
            update_expression_parts.append('use_ssl = :use_ssl')
            expression_attribute_values[':use_ssl'] = body['use_ssl']
        
        if 'password' in body:
            # Update password in Secrets Manager
            existing_item = response['Item']
            old_secret_arn = existing_item.get('credentials_secret_arn')
            
            if old_secret_arn:
                # Update existing secret
                secrets_manager.update_secret(
                    SecretId=old_secret_arn,
                    SecretString=body['password']
                )
            else:
                # Create new secret
                secret_arn = encrypt_credentials(body['password'], user_id)
                update_expression_parts.append('credentials_secret_arn = :secret_arn')
                expression_attribute_values[':secret_arn'] = secret_arn
        
        if not update_expression_parts:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'message': 'No fields to update'})
            }
        
        update_expression_parts.append('updated_at = :updated_at')
        expression_attribute_values[':updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        update_expression = 'SET ' + ', '.join(update_expression_parts)
        
        sources_table.update_item(
            Key={'user_id': user_id, 'source_id': source_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        # Get updated source
        response = sources_table.get_item(
            Key={'user_id': user_id, 'source_id': source_id}
        )
        item = response['Item']
        
        source_response = {
            'source_id': item['source_id'],
            'source_type': item.get('source_type', 'email'),
            'email': item.get('email'),
            'host': item.get('host'),
            'port': item.get('port', 993),
            'use_ssl': item.get('use_ssl', True),
            'status': item.get('status', 'active'),
            'last_sync_at': item.get('last_sync_at'),
            'created_at': item.get('created_at')
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(source_response)
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }


def handle_delete_source(user_id: str, source_id: str, cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Delete data source."""
    try:
        # Get source to delete secret
        response = sources_table.get_item(
            Key={'user_id': user_id, 'source_id': source_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Data source not found'})
            }
        
        # Delete secret from Secrets Manager
        secret_arn = response['Item'].get('credentials_secret_arn')
        if secret_arn:
            try:
                secrets_manager.delete_secret(
                    SecretId=secret_arn,
                    ForceDeleteWithoutRecovery=True
                )
            except ClientError as e:
                logger.warning(f"Error deleting secret: {e}")
        
        # Delete from DynamoDB
        sources_table.delete_item(
            Key={'user_id': user_id, 'source_id': source_id}
        )
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Data source deleted'})
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }


def handle_test_source(user_id: str, source_id: str, cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Test data source connection."""
    try:
        # Get source
        response = sources_table.get_item(
            Key={'user_id': user_id, 'source_id': source_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Data source not found'})
            }
        
        source = response['Item']
        
        # Get credentials
        secret_arn = source.get('credentials_secret_arn')
        if not secret_arn:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'message': 'No credentials found'})
            }
        
        password = decrypt_credentials(secret_arn)
        
        # Test IMAP connection
        try:
            import imaplib
            
            mail = imaplib.IMAP4_SSL(source.get('host'), source.get('port', 993)) if source.get('use_ssl', True) else imaplib.IMAP4(source.get('host'), source.get('port', 143))
            mail.login(source.get('email'), password)
            mail.logout()
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'success': True, 'message': 'Connection successful'})
            }
        except Exception as e:
            logger.error(f"IMAP connection error: {e}")
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'success': False, 'message': f'Connection failed: {str(e)}'})
            }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }

