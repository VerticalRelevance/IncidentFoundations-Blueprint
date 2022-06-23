# This example uses us-east-1 as the aggregate regionm. It is expected that SH must already be
# enabled for this region in the hub account as part of the account onboarding process.

module "enable_us-east-2" {
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-east-2
  }
}

module "enable_us-west-1" {
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-west-1
  }
}

module "enable_us-west-2" {
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-west-2
  }
}

# Sets up the us-east-1 region as the SH aggregation region
resource "aws_securityhub_finding_aggregator" "sh_aggregator" {
  linking_mode = "ALL_REGIONS"
}

# Auto enable security hub in organization member accounts
resource "aws_securityhub_organization_configuration" "autoenable_sh" {
  auto_enable = true
}

# Add existing accounts as managed to sh hub.
resource "aws_securityhub_member" "example" {
  for_each =  {for account in data.terraform_remote_state.org_master.outputs.org_accounts:  account[0] => account[1] if account[0] != data.aws_caller_identity.current.account_id}
  account_id = each.key
  email      = each.value
}

