# This example sets all existing org accounts as members for SH.  SH in the admin account
# will already have been enabled for all US regions through the ../org_master by designating
# SH hub account as admin for those regions

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