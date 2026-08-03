provider "aws" {
  region = var.region
}

locals {
  tags = merge(var.tags, {
    ManagedBy = "Terraform"
    Component = "aria-telemetry"
  })
}

resource "aws_kms_key" "telemetry" {
  description             = "ARIA telemetry archive encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = local.tags
}

resource "aws_kms_alias" "telemetry" {
  name          = "alias/${var.name}"
  target_key_id = aws_kms_key.telemetry.key_id
}

resource "aws_s3_bucket" "archive" {
  bucket_prefix = "${var.name}-"
  force_destroy = false
  tags          = local.tags
}

resource "aws_s3_bucket_public_access_block" "archive" {
  bucket                  = aws_s3_bucket.archive.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "archive" {
  bucket = aws_s3_bucket.archive.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.telemetry.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id
  rule {
    id     = "telemetry-retention"
    status = "Enabled"
    filter {}
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }
    expiration {
      days = var.archive_expiration_days
    }
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
