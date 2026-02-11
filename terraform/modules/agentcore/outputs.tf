output "agent_runtime_id" {
  description = "ID of the AgentCore agent runtime"
  value       = aws_bedrockagentcore_agent_runtime.main.agent_runtime_id
}

output "agent_runtime_arn" {
  description = "ARN of the AgentCore agent runtime"
  value       = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn
}
