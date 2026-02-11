variable "environment" {
  description = "Environment name"
  type        = string
}

variable "agentcore_role_arn" {
  description = "ARN of the AgentCore execution role"
  type        = string
}

variable "ecr_repository_url" {
  description = "URL of the ECR repository"
  type        = string
}

variable "container_image_tag" {
  description = "Tag of the container image to deploy"
  type        = string
  default     = "latest"
}

variable "cognito_user_pool_id" {
  description = "Cognito user pool ID"
  type        = string
}

variable "cognito_app_client_id" {
  description = "Cognito app client ID"
  type        = string
}

variable "s3_documents_bucket" {
  description = "S3 bucket name for documents"
  type        = string
}

variable "bedrock_knowledge_base_id" {
  description = "Bedrock knowledge base ID"
  type        = string
}

variable "langfuse_public_key_ssm_name" {
  description = "Name of the SSM parameter containing the Langfuse public key"
  type        = string
}

variable "langfuse_secret_key_ssm_name" {
  description = "Name of the SSM parameter containing the Langfuse secret key"
  type        = string
}
