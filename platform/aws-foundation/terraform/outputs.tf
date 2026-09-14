output "github_actions_role_arn" {
  value = aws_iam_role.github_deployment.arn
}

output "required_resource_tags" {
  value = local.mandatory_tags
}
