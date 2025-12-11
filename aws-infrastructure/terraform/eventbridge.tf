# EventBridge Schedule for Processing

resource "aws_cloudwatch_event_rule" "process_notifications" {
  name                = "${local.app_name}-process-notifications-${local.environment}"
  description         = "Trigger notification processing every ${var.notification_frequency_minutes} minutes"
  schedule_expression  = "rate(${var.notification_frequency_minutes} minutes)"
  state               = "ENABLED"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "process_notifications" {
  rule      = aws_cloudwatch_event_rule.process_notifications.name
  target_id = "ProcessNotificationsTarget"
  arn       = aws_lambda_function.process_notifications.arn
}

resource "aws_lambda_permission" "eventbridge_process_notifications" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_notifications.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.process_notifications.arn
}

