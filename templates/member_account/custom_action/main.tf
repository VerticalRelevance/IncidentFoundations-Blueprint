
locals {
  lambda_function_name = "sg_rule_removal"
  lambda_zip_filename  = "${path.module}/${random_id.lambda_zip_randomizer.keepers.lambda_zip}"
  lambda_timeout       = 60
}

resource "random_id" "lambda_zip_randomizer" {
  keepers = {
    lambda_zip = "sgr.zip"
  }
  byte_length = 8
}

resource "aws_securityhub_action_target" "remove_action_target" {
  name        = "remove0rules"
  identifier  = "remove0rules"
  description = "Custom action to remove 0.0.0.0/0 rules from a security group"
}

resource "aws_iam_role" "lambda_role" {
  name                = "${local.lambda_function_name}_role"
  assume_role_policy  = data.aws_iam_policy_document.lambda_assume_policy.json 
  inline_policy {
    name   = "sg_remove_base"
    policy = data.aws_iam_policy_document.lambda_policy.json
  }  
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/code/sgr.py"
  output_path = local.lambda_zip_filename
}

resource "aws_lambda_function" "sg_rule_lambda" {
  function_name = local.lambda_function_name
  filename      = local.lambda_zip_filename
  source_code_hash = filebase64sha256(local.lambda_zip_filename)
  role          = aws_iam_role.lambda_role.arn
  handler       = "sgr.lambda_handler"
  runtime = "python3.9"
  timeout = local.lambda_timeout
  environment {
    variables = {
      DEBUG = "True"
    }
  }
}

resource "aws_cloudwatch_event_rule" "sg_lambda_rule" {
  name        = "remove0rules"
  description = "Remove 0/0 rules from security groups"

  event_pattern = <<EOF
{
  "source": ["aws.securityhub"],
  "detail-type": ["Security Hub Findings - Custom Action"],
  "resources": ["${aws_securityhub_action_target.remove_action_target.arn}"]
}
EOF
}

resource "aws_cloudwatch_event_target" "sg_lambda_target" {
  rule      = aws_cloudwatch_event_rule.sg_lambda_rule.name
  target_id = "remove0rules"
  arn       = aws_lambda_function.sg_rule_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "allow_eventbridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sg_rule_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sg_lambda_rule.arn
}
