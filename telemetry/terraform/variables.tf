variable "region" {
  description = "AWS region containing the Kubernetes cluster."
  type        = string
  default     = "ca-central-1"
}

variable "name" {
  description = "Prefix for telemetry archive resources."
  type        = string
  default     = "aria-telemetry"
}

variable "archive_expiration_days" {
  description = "Compliance-approved archive retention period."
  type        = number
  default     = 365
  validation {
    condition     = var.archive_expiration_days >= 30
    error_message = "Archive retention must be at least 30 days."
  }
}

variable "tags" {
  description = "Additional resource tags."
  type        = map(string)
  default     = {}
}

