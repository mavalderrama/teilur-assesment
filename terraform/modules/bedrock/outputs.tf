output "knowledge_base_id" {
  description = "ID of the Bedrock knowledge base"
  value       = aws_bedrockagent_knowledge_base.main.id
}

output "knowledge_base_arn" {
  description = "ARN of the Bedrock knowledge base"
  value       = aws_bedrockagent_knowledge_base.main.arn
}

output "data_source_id" {
  description = "ID of the S3 data source"
  value       = aws_bedrockagent_data_source.s3.data_source_id
}

output "supplemental_bucket_arn" {
  description = "ARN of the supplemental data storage bucket"
  value       = aws_s3_bucket.supplemental.arn
}
