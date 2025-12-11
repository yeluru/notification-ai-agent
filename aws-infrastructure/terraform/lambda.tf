# Lambda Functions

# IAM Role for Lambda functions
resource "aws_iam_role" "lambda_execution" {
  name = "${local.app_name}-lambda-execution-${local.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for Lambda functions
resource "aws_iam_role_policy" "lambda_execution" {
  name = "${local.app_name}-lambda-execution-${local.environment}"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          "${aws_dynamodb_table.users.arn}/*",
          aws_dynamodb_table.data_sources.arn,
          "${aws_dynamodb_table.data_sources.arn}/*",
          aws_dynamodb_table.notifications.arn,
          "${aws_dynamodb_table.notifications.arn}/*",
          aws_dynamodb_table.sync_state.arn,
          "${aws_dynamodb_table.sync_state.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:CreateSecret",
          "secretsmanager:UpdateSecret",
          "secretsmanager:DeleteSecret"
        ]
        Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:notification-agent/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.summarization.arn,
          aws_sqs_queue.delivery.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function: user-management
resource "aws_lambda_function" "user_management" {
  filename         = "${path.module}/../lambda-functions/user-management/deployment.zip"
  function_name    = "${local.app_name}-user-management-${local.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE_USERS = aws_dynamodb_table.users.name
      JWT_SECRET          = var.jwt_secret
    }
  }

  tags = local.common_tags
}

# Lambda function: data-source-config
resource "aws_lambda_function" "data_source_config" {
  filename         = "${path.module}/../lambda-functions/data-source-config/deployment.zip"
  function_name    = "${local.app_name}-data-source-config-${local.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60

  environment {
    variables = {
      DYNAMODB_TABLE_DATA_SOURCES = aws_dynamodb_table.data_sources.name
      AWS_REGION                  = var.aws_region
    }
  }

  tags = local.common_tags
}

# Lambda function: process-notifications
resource "aws_lambda_function" "process_notifications" {
  filename         = "${path.module}/../lambda-functions/process-notifications/deployment.zip"
  function_name    = "${local.app_name}-process-notifications-${local.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes for processing

  environment {
    variables = {
      DYNAMODB_TABLE_DATA_SOURCES = aws_dynamodb_table.data_sources.name
      DYNAMODB_TABLE_NOTIFICATIONS = aws_dynamodb_table.notifications.name
      DYNAMODB_TABLE_SYNC_STATE = aws_dynamodb_table.sync_state.name
      SUMMARIZATION_QUEUE_URL  = aws_sqs_queue.summarization.url
    }
  }

  tags = local.common_tags
}

# Lambda function: summarize
resource "aws_lambda_function" "summarize" {
  filename         = "${path.module}/../lambda-functions/summarize/deployment.zip"
  function_name    = "${local.app_name}-summarize-${local.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60

  environment {
    variables = {
      DYNAMODB_TABLE_NOTIFICATIONS = aws_dynamodb_table.notifications.name
      LLM_API_KEY                  = var.llm_api_key
      LLM_BASE_URL                 = var.llm_base_url
      LLM_MODEL                    = var.llm_model
      DELIVERY_QUEUE_URL           = aws_sqs_queue.delivery.url
    }
  }

  tags = local.common_tags
}

# Lambda function: deliver
resource "aws_lambda_function" "deliver" {
  filename         = "${path.module}/../lambda-functions/deliver/deployment.zip"
  function_name    = "${local.app_name}-deliver-${local.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE_USERS        = aws_dynamodb_table.users.name
      DYNAMODB_TABLE_NOTIFICATIONS = aws_dynamodb_table.notifications.name
      SES_FROM_EMAIL               = var.ses_from_email
      TWILIO_ACCOUNT_SID           = var.twilio_account_sid
      TWILIO_AUTH_TOKEN            = var.twilio_auth_token
      TWILIO_FROM_NUMBER           = var.twilio_from_number
      AWS_REGION                   = var.aws_region
    }
  }

  tags = local.common_tags
}

# Lambda function: status-check
resource "aws_lambda_function" "status_check" {
  filename         = "${path.module}/../lambda-functions/status-check/deployment.zip"
  function_name    = "${local.app_name}-status-check-${local.environment}"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE_DATA_SOURCES  = aws_dynamodb_table.data_sources.name
      DYNAMODB_TABLE_NOTIFICATIONS = aws_dynamodb_table.notifications.name
      DYNAMODB_TABLE_SYNC_STATE    = aws_dynamodb_table.sync_state.name
      LLM_API_KEY                  = var.llm_api_key
    }
  }

  tags = local.common_tags
}

# Note: Lambda deployment packages need to be created before running terraform apply
# Use the build script: scripts/build-lambda-packages.sh

