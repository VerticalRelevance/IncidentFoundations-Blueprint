resource "aws_iam_role" "example" {
  name               = "yak_role"
  assume_role_policy = data.aws_iam_policy_document.instance_assume_role_policy.json # (not shown)

  inline_policy {
    name = "my_inline_policy"

    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action   = ["ec2:Describe*"]
          Effect   = "Allow"
          Resource = "*"
        },
      ]
    })
  }

  inline_policy {
    name   = "policy-8675309"
    policy = data.aws_iam_policy_document.inline_policy.json
  }
}

data "aws_iam_policy_document" "inline_policy" {
  statement {
    actions   = ["ec2:DescribeAccountAttributes"]
    resources = ["*"]
  }
}





resource "aws_iam_role" "lambda_role" {
  name                = "remove_sg_rule_role"
  assume_role_policy  = data.aws_iam_policy_document.instance_assume_role_policy.json 
  managed_policy_arns = [aws_iam_policy.policy_one.arn, aws_iam_policy.policy_two.arn]
}


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
    sid = "1"

    actions = [
      "s3:ListAllMyBuckets",
      "s3:GetBucketLocation",
    ]

    resources = [
      "arn:aws:s3:::*",
    ]
  }

}

resource "aws_iam_policy" "policy" {
  name        = "test_policy"
  path        = "/"
  description = "My test policy"

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = data.aws_iam_policy_docum  jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:Describe*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda_sg_rule_remove"
  path               = "/system/"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_policy.json
  managed_policy_arns = [ aws_iam_policy.policy_one.arn, aws_iam_policy.policy_two.arn  ]
}


