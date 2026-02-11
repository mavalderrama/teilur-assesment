variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# VPC Variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
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

# ECS Variables
variable "container_image" {
  description = "Docker image for ECS task"
  type        = string
  default     = "aws-ai-agent:latest"
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 8000
}

# Langfuse Variables
variable "langfuse_public_key" {
  description = "Langfuse public key for observability"
  type        = string
  sensitive   = true
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key for observability"
  type        = string
  sensitive   = true
}
