output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

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

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs.service_name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = "https://${module.ecs.alb_dns_name}"
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
