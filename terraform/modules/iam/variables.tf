variable "environment" {
  description = "Environment name"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 documents bucket"
  type        = string
}

variable "supplemental_s3_bucket_arn" {
  description = "ARN of the S3 bucket for Bedrock KB supplemental data storage"
  type        = string
}
