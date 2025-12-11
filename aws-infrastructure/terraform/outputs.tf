# Terraform outputs

output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = aws_s3_bucket.frontend.id
}

output "s3_bucket_website_url" {
  description = "S3 website URL"
  value       = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = var.domain_name != "" ? aws_cloudfront_distribution.frontend[0].id : null
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = var.domain_name != "" ? aws_cloudfront_distribution.frontend[0].domain_name : null
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_deployment.api.invoke_url
}

output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    users         = aws_dynamodb_table.users.name
    data_sources  = aws_dynamodb_table.data_sources.name
    notifications = aws_dynamodb_table.notifications.name
    sync_state    = aws_dynamodb_table.sync_state.name
  }
}

output "sqs_queue_urls" {
  description = "SQS queue URLs"
  value = {
    summarization = aws_sqs_queue.summarization.id
    delivery     = aws_sqs_queue.delivery.id
  }
}

