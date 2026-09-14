variable "project_name" { type = string }
variable "environment" { type = string }
variable "github_owner" { type = string }
variable "github_repository" { type = string }
variable "github_oidc_provider_arn" { type = string }
variable "owner" { type = string }
variable "cost_center" { type = string }

variable "permission_policy_arns" {
  description = "Project-specific least-privilege policies attached to the deployment role."
  type        = set(string)
  default     = []
  validation {
    condition = alltrue([
      for arn in var.permission_policy_arns :
      !endswith(arn, "/AdministratorAccess") && !endswith(arn, "/PowerUserAccess")
    ])
    error_message = "AdministratorAccess and PowerUserAccess are forbidden for CI/CD roles."
  }
}

variable "monthly_budget_usd" {
  type    = number
  default = 50
  validation {
    condition     = var.monthly_budget_usd > 0
    error_message = "monthly_budget_usd must be greater than zero."
  }
}

variable "alert_email_addresses" {
  type    = set(string)
  default = []
}

variable "anomaly_threshold_usd" {
  type    = number
  default = 10
}

variable "create_account_anomaly_monitor" {
  description = "Create once per AWS account; service monitors cannot be duplicated."
  type        = bool
  default     = false
}

variable "additional_tags" {
  type    = map(string)
  default = {}
}
