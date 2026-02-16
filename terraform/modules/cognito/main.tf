resource "aws_cognito_user_pool" "main" {
  name = "${var.user_pool_name}-${var.environment}"

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  username_configuration {
    case_sensitive = false
  }

  tags = {
    Name = "${var.environment}-user-pool"
  }
}

resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.app_client_name}-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  generate_secret = false
}
