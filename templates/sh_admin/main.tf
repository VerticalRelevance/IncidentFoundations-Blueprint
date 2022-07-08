# This template is meant to be run using credentials from the Security Hub Admin account.
# It adds all organization accounts as SH member accounts under control of this admin account.
# Member account IDs are loaded from the state created when running the ../org_master templates.
# Security Hub will already be enabled in the SH admin account through the ../org_master template
# when the account is designated as the SH admin for the US regions.

locals {
  rule_name            = "ca_router"
  lambda_name          = "ca_router"
  lambda_zip_filename  = "${path.module}/${random_id.lambda_zip_randomizer.keepers.lambda_zip}"
  lambda_timeout       = 30
}

# Sets up the us-east-1 region as the SH aggregation region
resource "aws_securityhub_finding_aggregator" "sh_aggregator" {
  linking_mode = "ALL_REGIONS"
  provider = aws.us-east-1
}

# Enable auto-membership and existing member accounts for us-east-1
module "enable_us-east-1" {
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-east-1
  }
  sh_member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}

# Enable auto-membership and existing member accounts for us-east-2
module "enable_us-east-2" {
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-east-2
  }
  sh_member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}

# Enable auto-membership and existing member accounts for us-west-1
module "enable_us-west-1" {
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-west-1
  }
  sh_member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}

# Enable auto-membership and existing member accounts for us-west-2
module "enable_us-west-2" {
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-west-2
  }
  sh_member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}

# AWS GuardDuty Setup
module "enable_gd_us-east-1" {
  count = var.enable_guardduty ? 1 : 0
  source    = "./modules/gd_enable"
  providers = {
    aws = aws.us-east-1
  }
  member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}

module "enable_gd_us-east-2" {
  count = var.enable_guardduty ? 1 : 0
  source    = "./modules/gd_enable"
  providers = {
    aws = aws.us-east-2
  }
  member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}
module "enable_gd_us-west-1" {
  count = var.enable_guardduty ? 1 : 0
  source    = "./modules/gd_enable"
  providers = {
    aws = aws.us-west-1
  }
  member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}
module "enable_gd_us-west-2" {
  count = var.enable_guardduty ? 1 : 0
  source    = "./modules/gd_enable"
  providers = {
    aws = aws.us-west-2
  }
  member_accounts = data.terraform_remote_state.org_master.outputs.org_accounts
}

# AWS Access Analyzer Setup
resource "aws_accessanalyzer_analyzer" "aa_us-east-1" {
  count = var.enable_accessanalyzer ? 1 : 0
  provider = aws.us-east-1
  analyzer_name = "Main-us-east-1"
  type          = "ORGANIZATION"
}

resource "aws_accessanalyzer_analyzer" "aa_us-east-2" {
  count = var.enable_accessanalyzer ? 1 : 0
  provider = aws.us-east-2
  analyzer_name = "Main-us-east-2"
  type          = "ORGANIZATION"
}

resource "aws_accessanalyzer_analyzer" "aa_us-west-1" {
  count = var.enable_accessanalyzer ? 1 : 0
  provider = aws.us-west-1
  analyzer_name = "Main-us-west-1"
  type          = "ORGANIZATION"
}

resource "aws_accessanalyzer_analyzer" "aa_us-west-2" {
  count = var.enable_accessanalyzer ? 1 : 0
  provider = aws.us-west-2
  analyzer_name = "Main-us-west-2"
  type          = "ORGANIZATION"
}

# CA Router Lambda Setup
resource "random_id" "lambda_zip_randomizer" {
  keepers = {
    lambda_zip = "sgr.zip"
  }
  byte_length = 12
}

resource "aws_iam_role" "lambda_role" {
  name                = "${local.lambda_name}_role"
  assume_role_policy  = data.aws_iam_policy_document.lambda_assume_policy.json
  inline_policy {
    name   = "sg_remove_base"
    policy = data.aws_iam_policy_document.lambda_policy.json
  }
}

resource "aws_lambda_function" "ca_router_lambda" {
  function_name = local.lambda_name
  filename      = local.lambda_zip_filename
  source_code_hash = filebase64sha256(local.lambda_zip_filename)
  role          = aws_iam_role.lambda_role.arn
  handler       = "ca_router.lambda_handler"
  runtime = "python3.9"
  timeout = local.lambda_timeout
  environment {
    variables = {
      DEBUG = "True"
    }
  }
}

resource "aws_cloudwatch_event_rule" "ca_router_lambda_rule" {
  name        = local.rule_name
  description = "Routes a custom action to the appropriate remediation lambda in a member account"
  event_pattern = <<EOF
{
  "source": ["aws.securityhub"],
  "detail-type": ["Security Hub Findings - Custom Action"]
}
EOF
}

resource "aws_cloudwatch_event_target" "sg_lambda_target" {
  rule      = aws_cloudwatch_event_rule.ca_router_lambda_rule.name
  target_id = local.rule_name
  arn       = aws_lambda_function.ca_router_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "allow_eventbridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ca_router_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ca_router_lambda_rule.arn
}
