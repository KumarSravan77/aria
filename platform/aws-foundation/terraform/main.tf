locals {
  name = lower("${var.project_name}-${var.environment}")
  mandatory_tags = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
  }
  tags = merge(var.additional_tags, local.mandatory_tags)
}

data "aws_iam_policy_document" "github_oidc_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [var.github_oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_owner}/${var.github_repository}:environment:${var.environment}"]
    }
  }
}

resource "aws_iam_role" "github_deployment" {
  name                 = "${local.name}-github-deploy"
  description          = "Short-lived GitHub Actions deployment identity for ${local.name}"
  assume_role_policy   = data.aws_iam_policy_document.github_oidc_trust.json
  max_session_duration = 3600
  tags                 = local.tags
}

resource "aws_iam_role_policy_attachment" "project_permissions" {
  for_each   = var.permission_policy_arns
  role       = aws_iam_role.github_deployment.name
  policy_arn = each.value
}

resource "aws_budgets_budget" "project" {
  name         = "${local.name}-monthly-cost"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  cost_filter {
    name   = "TagKeyValue"
    values = ["user:Project$${var.project_name}"]
  }
  dynamic "notification" {
    for_each = length(var.alert_email_addresses) == 0 ? [] : [80, 100]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = notification.value == 80 ? "FORECASTED" : "ACTUAL"
      subscriber_email_addresses = var.alert_email_addresses
    }
  }
  tags = local.tags
}

resource "aws_ce_anomaly_monitor" "account_services" {
  count             = var.create_account_anomaly_monitor ? 1 : 0
  name              = "portfolio-account-service-cost-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
  tags              = local.tags
}

resource "aws_ce_anomaly_subscription" "account_services" {
  count            = var.create_account_anomaly_monitor && length(var.alert_email_addresses) > 0 ? 1 : 0
  name             = "portfolio-immediate-anomaly-alerts"
  frequency        = "IMMEDIATE"
  monitor_arn_list = [aws_ce_anomaly_monitor.account_services[0].arn]
  subscriber {
    type    = "EMAIL"
    address = sort(tolist(var.alert_email_addresses))[0]
  }
  threshold_expression {
    and {
      dimension {
        key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
        match_options = ["GREATER_THAN_OR_EQUAL"]
        values        = [tostring(var.anomaly_threshold_usd)]
      }
    }
  }
  tags = local.tags
}
