
locals {
  lambda_zip_filename  = "${path.module}/${random_id.lambda_zip_randomizer.keepers.lambda_zip}"
  lambda_timeout       = 60
}

resource "random_id" "lambda_zip_randomizer" {
  keepers = {
    lambda_zip = "${var.action_name}.zip"
  }
  byte_length = 12
}

resource "aws_securityhub_action_target" "remove_action_target" {
  name        = var.action_name
  identifier  = var.action_name
  description = "Custom action for invoking ${var.action_name} lambda"
}

resource "aws_iam_role" "lambda_role" {
  name                = "${var.action_name}_role"
  assume_role_policy  = data.aws_iam_policy_document.lambda_assume_policy.json 
  inline_policy {
    name   = "default_lambda_permissions"
    policy = data.aws_iam_policy_document.default_lambda_policy.json
  }
  inline_policy {
    name   = "${var.action_name}_base"
    policy = file("remediations/${var.action_name}/${var.policy_name}")
  }  
}

resource "aws_lambda_function" "ca_lambda" {
  function_name = var.action_name
  filename      = local.lambda_zip_filename
  source_code_hash = filebase64sha256(local.lambda_zip_filename)
  role          = aws_iam_role.lambda_role.arn
  handler       = "${var.action_name}.lambda_handler"
  runtime = yamldecode(file("remediations/${var.action_name}/config.yml"))["runtime"]
  timeout = local.lambda_timeout
  environment {
    variables = {
      DEBUG = "False"
    }
  }
}

resource "aws_cloudwatch_event_rule" "ca_lambda_rule" {
  name        = var.action_name
  description = "Rule to invoke custom action ${var.action_name}"

  event_pattern = <<EOF
{
  "source": ["aws.securityhub"],
  "detail-type": ["Security Hub Findings - Custom Action"],
  "resources": ["${aws_securityhub_action_target.remove_action_target.arn}"]
}
EOF
}

resource "aws_cloudwatch_event_target" "sg_lambda_target" {
  rule      = aws_cloudwatch_event_rule.ca_lambda_rule.name
  target_id = var.action_name
  arn       = aws_lambda_function.ca_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "allow_eventbridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ca_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ca_lambda_rule.arn
}

resource "aws_lambda_permission" "allow_ca_router_role" {
  statement_id  = "allow_ca_router_role"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ca_lambda.function_name
  principal     = data.aws_caller_identity.current.account_id
  source_arn    = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ca_router_ca_role"
}


