output "archive_bucket" {
  description = "Bucket to configure in the Vector archive sink."
  value       = aws_s3_bucket.archive.id
}

output "archive_kms_key_arn" {
  description = "KMS key for workload-identity permissions."
  value       = aws_kms_key.telemetry.arn
}

