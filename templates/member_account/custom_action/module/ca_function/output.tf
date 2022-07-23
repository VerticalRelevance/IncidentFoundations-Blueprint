output "lambda_arn" {
  value = aws_lambda_function.ca_lambda.arn
}

output "event_bridge_rule_arn" {
  value = aws_cloudwatch_event_rule.ca_lambda_rule.arn
}

output "sh_action_target_arn" {
  value = aws_securityhub_action_target.remove_action_target.arn
}