output "bedrock_execution_role_arn" {
  description = "ARN of the Bedrock KB execution role"
  value       = aws_iam_role.bedrock_execution.arn
}

output "agentcore_execution_role_arn" {
  description = "ARN of the AgentCore execution role"
  value       = aws_iam_role.agentcore_execution.arn
}
