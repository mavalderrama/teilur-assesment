data "aws_region" "current" {}

data "aws_ssm_parameter" "langfuse_public_key" {
  name            = var.langfuse_public_key_ssm_name
  with_decryption = true
}

data "aws_ssm_parameter" "langfuse_secret_key" {
  name            = var.langfuse_secret_key_ssm_name
  with_decryption = true
}

resource "aws_bedrockagentcore_agent_runtime" "main" {
  agent_runtime_name = "${var.environment}_ai_agent_runtime"
  role_arn           = var.agentcore_role_arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${var.ecr_repository_url}:${var.container_image_tag}"
    }
  }

  authorizer_configuration {
    custom_jwt_authorizer {
      discovery_url    = "https://cognito-idp.${data.aws_region.current.id}.amazonaws.com/${var.cognito_user_pool_id}/.well-known/openid-configuration"
      allowed_clients  = [var.cognito_app_client_id]
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
    BEDROCK_LLM_REGION        = var.bedrock_llm_region
    BEDROCK_MODEL_ID          = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    OBSERVABILITY_PROVIDER    = "langfuse"
    LANGFUSE_PUBLIC_KEY       = data.aws_ssm_parameter.langfuse_public_key.value
    LANGFUSE_SECRET_KEY       = data.aws_ssm_parameter.langfuse_secret_key.value
    LANGFUSE_HOST             = "https://us.cloud.langfuse.com"
    API_HOST                  = "0.0.0.0"
    API_PORT                  = "8080"
    LOG_LEVEL                 = "INFO"
  }

  tags = {
    Name = "${var.environment}-agentcore-runtime"
  }
}
