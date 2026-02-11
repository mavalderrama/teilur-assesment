variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of the private subnets for ECS tasks"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "IDs of the public subnets for ALB"
  type        = list(string)
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "container_image" {
  description = "Docker image for the ECS task"
  type        = string
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
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

variable "langfuse_public_key_ssm_arn" {
  description = "ARN of the SSM parameter containing the Langfuse public key"
  type        = string
}

variable "langfuse_secret_key_ssm_arn" {
  description = "ARN of the SSM parameter containing the Langfuse secret key"
  type        = string
}
