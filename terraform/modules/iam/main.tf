data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ------------------------------------------------------------------------------
# Bedrock Knowledge Base Execution Role
# ------------------------------------------------------------------------------
resource "aws_iam_role" "bedrock_execution" {
  name = "${var.environment}-bedrock-kb-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.environment}-bedrock-kb-execution-role"
  }
}

resource "aws_iam_role_policy" "bedrock_s3_access" {
  name = "${var.environment}-bedrock-s3-access"
  role = aws_iam_role.bedrock_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:AbortMultipartUpload",
          "s3:ListBucketMultipartUploads",
        ]
        Resource = [
          var.supplemental_s3_bucket_arn,
          "${var.supplemental_s3_bucket_arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_invoke_model" {
  name = "${var.environment}-bedrock-invoke-model"
  role = aws_iam_role.bedrock_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
        ]
        Resource = "arn:aws:bedrock:${data.aws_region.current.id}::foundation-model/amazon.titan-embed-text-v2:0"
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_aoss_access" {
  name = "${var.environment}-bedrock-aoss-access"
  role = aws_iam_role.bedrock_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "aoss:APIAccessAll"
        Resource = "arn:aws:aoss:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:collection/*"
      }
    ]
  })
}

# ------------------------------------------------------------------------------
# AgentCore Execution Role
# ------------------------------------------------------------------------------
resource "aws_iam_role" "agentcore_execution" {
  name = "${var.environment}-agentcore-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.environment}-agentcore-execution-role"
  }
}

resource "aws_iam_role_policy" "agentcore_runtime" {
  name = "${var.environment}-agentcore-runtime"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:CreateAgentRuntime",
          "bedrock:UpdateAgentRuntime",
          "bedrock:DeleteAgentRuntime",
          "bedrock:GetAgentRuntime",
          "bedrock:ListAgentRuntimes",
          "bedrock:InvokeAgentRuntime",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "agentcore_ecr" {
  name = "${var.environment}-agentcore-ecr"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetAuthorizationToken",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "agentcore_bedrock" {
  name = "${var.environment}-agentcore-bedrock"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Converse",
          "bedrock:ConverseStream",
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate",
          "bedrock:GetFoundationModelAvailability",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "agentcore_s3" {
  name = "${var.environment}-agentcore-s3"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "agentcore_cognito" {
  name = "${var.environment}-agentcore-cognito"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:AdminRespondToAuthChallenge",
        ]
        Resource = "arn:aws:cognito-idp:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:userpool/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "agentcore_ssm" {
  name = "${var.environment}-agentcore-ssm"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter",
        ]
        Resource = "arn:aws:ssm:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:parameter/${var.environment}/ai-agent/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "agentcore_logs" {
  name = "${var.environment}-agentcore-logs"
  role = aws_iam_role.agentcore_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:*"
      }
    ]
  })
}
