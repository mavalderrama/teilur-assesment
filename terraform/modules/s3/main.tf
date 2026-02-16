data "aws_s3_bucket" "documents" {
  bucket = "${var.bucket_name}-${var.environment}"
}
