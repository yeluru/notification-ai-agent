"""
Lambda function for user management (signup, login, profile).
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any
import boto3
import bcrypt
import jwt
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_USERS', 'users'))

# JWT secret (should be in Secrets Manager in production)
JWT_SECRET = os.environ.get('JWT_SECRET', 'change-me-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def generate_token(user_id: str, email: str) -> str:
    """Generate JWT token for user."""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow().timestamp() + (JWT_EXPIRATION_HOURS * 3600),
        'iat': datetime.utcnow().timestamp()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user management requests.
    
    Routes:
    - POST /auth/signup - Create new user
    - POST /auth/login - Authenticate user
    - GET /users/me - Get current user profile
    - PUT /users/me - Update user profile
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
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
        
        # Route requests
        if path == '/auth/signup' and http_method == 'POST':
            return handle_signup(body, cors_headers)
        elif path == '/auth/login' and http_method == 'POST':
            return handle_login(body, cors_headers)
        elif path == '/auth/refresh' and http_method == 'POST':
            return handle_refresh(headers, cors_headers)
        elif path == '/users/me' and http_method == 'GET':
            return handle_get_user(headers, cors_headers)
        elif path == '/users/me' and http_method == 'PUT':
            return handle_update_user(headers, body, cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Not found'})
            }
            
    except Exception as e:
        logger.error(f"Error in user-management: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers if 'cors_headers' in locals() else {},
            'body': json.dumps({'message': 'Internal server error'})
        }


def handle_signup(body: Dict[str, Any], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle user signup."""
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    phone = body.get('phone', '').strip() or None
    
    if not email or not password:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Email and password are required'})
        }
    
    if len(password) < 8:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Password must be at least 8 characters'})
        }
    
    # Check if user exists
    try:
        response = users_table.get_item(Key={'user_id': email})
        if 'Item' in response:
            return {
                'statusCode': 409,
                'headers': cors_headers,
                'body': json.dumps({'message': 'User already exists'})
            }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }
    
    # Create user
    user_id = email
    hashed_password = hash_password(password)
    now = datetime.utcnow().isoformat() + 'Z'
    
    user_item = {
        'user_id': user_id,
        'email': email,
        'password_hash': hashed_password,
        'phone': phone,
        'created_at': now,
        'updated_at': now,
        'subscription_tier': 'free'
    }
    
    try:
        users_table.put_item(Item=user_item)
        
        # Generate token
        token = generate_token(user_id, email)
        
        # Return user (without password)
        user_response = {
            'user_id': user_id,
            'email': email,
            'phone': phone,
            'created_at': now,
            'subscription_tier': 'free'
        }
        
        return {
            'statusCode': 201,
            'headers': cors_headers,
            'body': json.dumps({
                'user': user_response,
                'token': token
            })
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Failed to create user'})
        }


def handle_login(body: Dict[str, Any], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle user login."""
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    
    if not email or not password:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Email and password are required'})
        }
    
    try:
        response = users_table.get_item(Key={'user_id': email})
        
        if 'Item' not in response:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Invalid credentials'})
            }
        
        user = response['Item']
        
        # Verify password
        if not verify_password(password, user.get('password_hash', '')):
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'message': 'Invalid credentials'})
            }
        
        # Generate token
        token = generate_token(user['user_id'], user['email'])
        
        # Return user (without password)
        user_response = {
            'user_id': user['user_id'],
            'email': user['email'],
            'phone': user.get('phone'),
            'created_at': user.get('created_at'),
            'subscription_tier': user.get('subscription_tier', 'free')
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'user': user_response,
                'token': token
            })
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }


def handle_refresh(headers: Dict[str, str], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle token refresh."""
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return {
            'statusCode': 401,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Missing or invalid token'})
        }
    
    token = auth_header.replace('Bearer ', '')
    
    try:
        payload = verify_token(token)
        new_token = generate_token(payload['user_id'], payload['email'])
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'token': new_token})
        }
    except ValueError as e:
        return {
            'statusCode': 401,
            'headers': cors_headers,
            'body': json.dumps({'message': str(e)})
        }


def handle_get_user(headers: Dict[str, str], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Get current user profile."""
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return {
            'statusCode': 401,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Unauthorized'})
        }
    
    token = auth_header.replace('Bearer ', '')
    
    try:
        payload = verify_token(token)
        user_id = payload['user_id']
        
        response = users_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'message': 'User not found'})
            }
        
        user = response['Item']
        user_response = {
            'user_id': user['user_id'],
            'email': user['email'],
            'phone': user.get('phone'),
            'created_at': user.get('created_at'),
            'subscription_tier': user.get('subscription_tier', 'free')
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(user_response)
        }
    except ValueError as e:
        return {
            'statusCode': 401,
            'headers': cors_headers,
            'body': json.dumps({'message': str(e)})
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }


def handle_update_user(headers: Dict[str, str], body: Dict[str, Any], cors_headers: Dict[str, str]) -> Dict[str, Any]:
    """Update user profile."""
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return {
            'statusCode': 401,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Unauthorized'})
        }
    
    token = auth_header.replace('Bearer ', '')
    
    try:
        payload = verify_token(token)
        user_id = payload['user_id']
        
        # Update allowed fields
        update_expression_parts = []
        expression_attribute_values = {}
        
        if 'phone' in body:
            update_expression_parts.append('phone = :phone')
            expression_attribute_values[':phone'] = body['phone']
        
        if not update_expression_parts:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'message': 'No fields to update'})
            }
        
        update_expression_parts.append('updated_at = :updated_at')
        expression_attribute_values[':updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        update_expression = 'SET ' + ', '.join(update_expression_parts)
        
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        # Get updated user
        response = users_table.get_item(Key={'user_id': user_id})
        user = response['Item']
        
        user_response = {
            'user_id': user['user_id'],
            'email': user['email'],
            'phone': user.get('phone'),
            'created_at': user.get('created_at'),
            'subscription_tier': user.get('subscription_tier', 'free')
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(user_response)
        }
    except ValueError as e:
        return {
            'statusCode': 401,
            'headers': cors_headers,
            'body': json.dumps({'message': str(e)})
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Database error'})
        }

