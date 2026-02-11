terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.21"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.11"
    }
  }

  # Uncomment for remote state management
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "aws-ai-agent/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

data "aws_caller_identity" "current" {}

locals {
  ssm_prefix                   = "/${var.environment}/ai-agent"
  langfuse_public_key_ssm_name = "${local.ssm_prefix}/langfuse-public-key"
  langfuse_secret_key_ssm_name = "${local.ssm_prefix}/langfuse-secret-key"
  langfuse_public_key_ssm_arn  = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${local.langfuse_public_key_ssm_name}"
  langfuse_secret_key_ssm_arn  = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${local.langfuse_secret_key_ssm_name}"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "AWS AI Agent"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# S3 Module for Document Storage
module "s3" {
  source = "./modules/s3"

  environment = var.environment
  bucket_name = var.s3_bucket_name
}

# Cognito Module
module "cognito" {
  source = "./modules/cognito"

  environment     = var.environment
  user_pool_name  = var.cognito_user_pool_name
  app_client_name = var.cognito_app_client_name
}

# ECR Module for Container Images
module "ecr" {
  source = "./modules/ecr"

  environment     = var.environment
  repository_name = var.ecr_repository_name
}

# IAM Module
module "iam" {
  source = "./modules/iam"

  environment   = var.environment
  s3_bucket_arn = module.s3.bucket_arn
}

# Bedrock Module (Knowledge Base)
module "bedrock" {
  source = "./modules/bedrock"

  environment                = var.environment
  knowledge_base_name        = var.bedrock_knowledge_base_name
  s3_bucket_arn              = module.s3.bucket_arn
  bedrock_execution_role_arn = module.iam.bedrock_execution_role_arn
}

# ECS Module for FastAPI Application
module "ecs" {
  source = "./modules/ecs"

  environment                 = var.environment
  vpc_id                      = module.vpc.vpc_id
  private_subnet_ids          = module.vpc.private_subnet_ids
  public_subnet_ids           = module.vpc.public_subnet_ids
  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_role_arn           = module.iam.ecs_task_role_arn
  container_image             = var.container_image
  container_port              = var.container_port

  # Environment variables for the container
  cognito_user_pool_id        = module.cognito.user_pool_id
  cognito_app_client_id       = module.cognito.app_client_id
  s3_documents_bucket         = module.s3.bucket_name
  bedrock_knowledge_base_id   = module.bedrock.knowledge_base_id
  langfuse_public_key_ssm_arn = local.langfuse_public_key_ssm_arn
  langfuse_secret_key_ssm_arn = local.langfuse_secret_key_ssm_arn
}

# AgentCore Module (Bedrock AgentCore Runtime)
module "agentcore" {
  source = "./modules/agentcore"

  environment                  = var.environment
  agentcore_role_arn           = module.iam.agentcore_execution_role_arn
  ecr_repository_url           = module.ecr.repository_url
  container_image_tag          = var.container_image_tag
  cognito_user_pool_id         = module.cognito.user_pool_id
  cognito_app_client_id        = module.cognito.app_client_id
  s3_documents_bucket          = module.s3.bucket_name
  bedrock_knowledge_base_id    = module.bedrock.knowledge_base_id
  langfuse_public_key_ssm_name = local.langfuse_public_key_ssm_name
  langfuse_secret_key_ssm_name = local.langfuse_secret_key_ssm_name
}
