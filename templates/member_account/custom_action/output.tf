output "lambda_arn" {
  value = aws_lambda_function.sg_rule_lambda.arn
}

output "event_bridge_rule_arn" {
  value = aws_cloudwatch_event_rule.sg_lambda_rule.arn
}

output "sh_action_target_arn" {
  value = aws_securityhub_action_target.remove_action_target.arn
}