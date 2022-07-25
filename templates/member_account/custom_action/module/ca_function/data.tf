data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "lambda_assume_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# Default permissions need for lambda to create cloudwatch resources for logging
data "aws_iam_policy_document" "default_lambda_policy" {
  statement {
    sid = "LogGroupCreation"
    actions = ["logs:CreateLogGroup"]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:*"]
  }
  statement {
    sid = "StreamEvents"
    actions = ["logs:CreateLogStream",
               "logs:PutLogEvents"]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.action_name}:*"
    ]
  }
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir = "remediations/${var.action_name}"
  output_path = local.lambda_zip_filename
}