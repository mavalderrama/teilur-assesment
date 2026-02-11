variable "environment" {
  description = "Environment name"
  type        = string
}

variable "knowledge_base_name" {
  description = "Name of the Bedrock knowledge base"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for data source"
  type        = string
}

variable "bedrock_execution_role_arn" {
  description = "ARN of the Bedrock KB execution role"
  type        = string
}
