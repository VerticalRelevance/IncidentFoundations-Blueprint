# This template is meant to be run using credentials from the Security Hub Admin account.
# It adds all organization accounts as SH member accounts under control of this admin account.
# Member account IDs are loaded from the state created when running the ../org_master templates.
# Security Hub will already be enabled in the SH admin account through the ../org_master template
# when the account is designated as the SH admin for the US regions.

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