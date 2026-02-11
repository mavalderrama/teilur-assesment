data "aws_region" "current" {}

resource "aws_bedrockagentcore_agent_runtime" "main" {
  agent_runtime_name = "${var.environment}-ai-agent-runtime"
  role_arn           = var.agentcore_role_arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${var.ecr_repository_url}:${var.container_image_tag}"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  environment_variables = {
    ENVIRONMENT               = var.environment
    AWS_REGION                = data.aws_region.current.id
    COGNITO_USER_POOL_ID      = var.cognito_user_pool_id
    COGNITO_APP_CLIENT_ID     = var.cognito_app_client_id
    COGNITO_REGION            = data.aws_region.current.id
    S3_DOCUMENTS_BUCKET       = var.s3_documents_bucket
    BEDROCK_KNOWLEDGE_BASE_ID = var.bedrock_knowledge_base_id
    BEDROCK_REGION            = data.aws_region.current.id
    BEDROCK_MODEL_ID          = "anthropic.claude-3-sonnet-20240229-v1:0"
    OBSERVABILITY_PROVIDER    = "langfuse"
    LANGFUSE_PUBLIC_KEY       = var.langfuse_public_key
    LANGFUSE_SECRET_KEY       = var.langfuse_secret_key
    LANGFUSE_HOST             = "https://cloud.langfuse.com"
    API_HOST                  = "0.0.0.0"
    API_PORT                  = "8000"
    LOG_LEVEL                 = "INFO"
  }

  tags = {
    Name = "${var.environment}-agentcore-runtime"
  }
}
