# DynamoDB Tables

resource "aws_dynamodb_table" "users" {
  name           = "${local.app_name}-users-${local.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "data_sources" {
  name           = "${local.app_name}-data-sources-${local.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "source_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "source_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "notifications" {
  name           = "${local.app_name}-notifications-${local.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "notification_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "notification_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "sync_state" {
  name           = "${local.app_name}-sync-state-${local.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "source_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "source_id"
    type = "S"
  }

  tags = local.common_tags
}

