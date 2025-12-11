# Main Terraform configuration for Notification Agent

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Optional: Use S3 backend for state management
  # backend "s3" {
  #   bucket = "notification-agent-terraform-state"
  #   key    = "terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
  
  # Optional: Use AWS profile
  # profile = var.aws_profile
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values
locals {
  app_name = var.app_name
  environment = var.environment
  common_tags = {
    Application = local.app_name
    Environment = local.environment
    ManagedBy   = "Terraform"
  }
}

