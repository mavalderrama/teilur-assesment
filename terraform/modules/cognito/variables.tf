variable "environment" {
  description = "Environment name"
  type        = string
}

variable "user_pool_name" {
  description = "Name of the Cognito user pool"
  type        = string
}

variable "app_client_name" {
  description = "Name of the Cognito app client"
  type        = string
}
