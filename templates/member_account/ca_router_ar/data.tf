data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "lambda_assume_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.cs_account_id}:role/ca_router_role"]
    }
  }
}



data "aws_iam_policy_document" "ca_router_policy" {
  statement {
    actions = ["lambda:InvokeFunction"]
    resources = ["arn:aws:lambda:*:${data.aws_caller_identity.current.account_id}:function:remove0rules"]
  }
}
