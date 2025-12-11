# SQS Queues

resource "aws_sqs_queue" "summarization" {
  name                      = "${local.app_name}-summarization-queue-${local.environment}"
  message_retention_seconds = 86400  # 24 hours
  visibility_timeout_seconds = 300   # 5 minutes (matches Lambda timeout)

  tags = local.common_tags
}

resource "aws_sqs_queue" "delivery" {
  name                      = "${local.app_name}-delivery-queue-${local.environment}"
  message_retention_seconds = 86400  # 24 hours
  visibility_timeout_seconds = 60   # 1 minute

  tags = local.common_tags
}

# Lambda event source mappings
resource "aws_lambda_event_source_mapping" "summarize_queue" {
  event_source_arn = aws_sqs_queue.summarization.arn
  function_name    = aws_lambda_function.summarize.arn
  batch_size       = 10
  maximum_batching_window_in_seconds = 5
}

resource "aws_lambda_event_source_mapping" "delivery_queue" {
  event_source_arn = aws_sqs_queue.delivery.arn
  function_name    = aws_lambda_function.deliver.arn
  batch_size       = 10
  maximum_batching_window_in_seconds = 5
}

