# This example enables the supplied SH admin account as the administrator for all US regions.
# Prerequisites
# Security Hub trusted access must be enabled as a service in the AWS Organization.  This step should be
# part of the organization initial configuration.


# Make the sh_admin_account_id account a delegated admin for security hub
resource "aws_organizations_delegated_administrator" "security_hub_delegation" {
  account_id        = var.sh_admin_account_id
  service_principal = "securityhub.amazonaws.com"
  provider = aws.us-east-1
}

# Set SH admin account as the admin for security hub in us-east-1
resource "aws_securityhub_organization_admin_account" "sh_admin_east_1_enable" {
  depends_on = [aws_organizations_delegated_administrator.security_hub_delegation]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-east-1
}

# Set SH admin account as the admin for security hub in us-east-2
resource "aws_securityhub_organization_admin_account" "sh_admin_east_2_enable" {
  depends_on = [aws_securityhub_organization_admin_account.sh_admin_east_1_enable]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-east-2
}

# Set SH admin account as the admin for security hub in us-west-1
resource "aws_securityhub_organization_admin_account" "sh_admin_west_1_enable" {
  depends_on = [aws_securityhub_organization_admin_account.sh_admin_east_2_enable]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-west-1
}

# Set SH admin account as the admin for security hub in us-west-2
resource "aws_securityhub_organization_admin_account" "sh_admin_west_2_enable" {
  depends_on = [aws_securityhub_organization_admin_account.sh_admin_west_1_enable]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-west-2
}

# Make the sh_admin_account_id account a deletaged admin for guardduty
resource "aws_organizations_delegated_administrator" "guardduty_delegation" {
  account_id        = var.sh_admin_account_id
  service_principal = "guardduty.amazonaws.com"
  provider = aws.us-east-1
}

resource "aws_guardduty_organization_admin_account" "gd_admin_us_east_1_enable" {
  depends_on = [aws_organizations_delegated_administrator.guardduty_delegation]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-east-1
}

resource "aws_guardduty_organization_admin_account" "gd_admin_us_east_2_enable" {
  depends_on = [aws_guardduty_organization_admin_account.gd_admin_us_east_1_enable]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-east-2
}

resource "aws_guardduty_organization_admin_account" "gd_admin_us_west_1_enable" {
  depends_on = [aws_guardduty_organization_admin_account.gd_admin_us_east_2_enable]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-west-1
}

resource "aws_guardduty_organization_admin_account" "gd_admin_us_west_2_enable" {
  depends_on = [aws_guardduty_organization_admin_account.gd_admin_us_west_1_enable]
  admin_account_id = var.sh_admin_account_id
  provider = aws.us-west-2
}