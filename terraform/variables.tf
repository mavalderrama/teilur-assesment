variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-2"
}

variable "bedrock_llm_region" {
  description = "AWS region where the Bedrock LLM is hosted (may differ from aws_region)"
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# S3 Variables
variable "s3_bucket_name" {
  description = "Name of S3 bucket for documents"
  type        = string
  default     = "aws-ai-agent-documents"
}

# Cognito Variables
variable "cognito_user_pool_name" {
  description = "Name of Cognito user pool"
  type        = string
  default     = "ai-agent-users"
}

variable "cognito_app_client_name" {
  description = "Name of Cognito app client"
  type        = string
  default     = "ai-agent-client"
}

# Bedrock Variables
variable "bedrock_knowledge_base_name" {
  description = "Name of Bedrock knowledge base"
  type        = string
  default     = "amazon-financial-docs"
}

# ECR Variables
variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "aws-ai-agent"
}

# AgentCore Variables
variable "container_image_tag" {
  description = "Tag of the container image for AgentCore"
  type        = string
  default     = "latest"
}
