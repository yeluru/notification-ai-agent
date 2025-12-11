# Terraform variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name (optional)"
  type        = string
  default     = ""
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "notification-agent"
}

variable "environment" {
  description = "Environment name (prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain (optional)"
  type        = string
  default     = ""
}

variable "llm_api_key" {
  description = "LLM API key"
  type        = string
  sensitive   = true
}

variable "llm_base_url" {
  description = "LLM API base URL"
  type        = string
  default     = "https://api.openai.com/v1"
}

variable "llm_model" {
  description = "LLM model name"
  type        = string
  default     = "gpt-3.5-turbo"
}

variable "ses_from_email" {
  description = "SES verified sender email"
  type        = string
}

variable "twilio_account_sid" {
  description = "Twilio account SID (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_auth_token" {
  description = "Twilio auth token (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_from_number" {
  description = "Twilio from phone number (optional)"
  type        = string
  default     = ""
}

variable "jwt_secret" {
  description = "JWT secret for token signing"
  type        = string
  sensitive   = true
}

variable "notification_frequency_minutes" {
  description = "Notification processing frequency in minutes"
  type        = number
  default     = 15
}

variable "use_parameter_store" {
  description = "Use Parameter Store instead of Secrets Manager for non-rotating secrets"
  type        = bool
  default     = true
}

