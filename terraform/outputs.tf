output "cognito_user_pool_id" {
  description = "ID of the Cognito user pool"
  value       = module.cognito.user_pool_id
}

output "cognito_user_pool_arn" {
  description = "ARN of the Cognito user pool"
  value       = module.cognito.user_pool_arn
}

output "cognito_app_client_id" {
  description = "ID of the Cognito app client"
  value       = module.cognito.app_client_id
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for documents"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "bedrock_knowledge_base_id" {
  description = "ID of the Bedrock knowledge base"
  value       = module.bedrock.knowledge_base_id
}

output "bedrock_knowledge_base_arn" {
  description = "ARN of the Bedrock knowledge base"
  value       = module.bedrock.knowledge_base_arn
}

output "bedrock_data_source_id" {
  description = "ID of the Bedrock KB S3 data source"
  value       = module.bedrock.data_source_id
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}

output "agentcore_runtime_id" {
  description = "ID of the AgentCore agent runtime"
  value       = module.agentcore.agent_runtime_id
}

output "agentcore_runtime_arn" {
  description = "ARN of the AgentCore agent runtime"
  value       = module.agentcore.agent_runtime_arn
}
