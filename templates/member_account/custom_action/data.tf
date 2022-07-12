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

data "aws_iam_policy_document" "lambda_policy" {
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
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.lambda_name}:*"
    ]
  }
  statement {
    sid = "ExecutionPermissions"
    actions = ["ec2:RevokeSecurityGroupIngress",
               "ec2:RevokeSecurityGroupEgress",
               "ec2:DescribeSecurityGroups"]
    resources = ["*"]
  }
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/code/sgr.py"
  output_path = local.lambda_zip_filename
}