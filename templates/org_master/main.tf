# This example uses us-east-1 as the default working region.  This can be changed by updating the
# provider in providers.tf.  It sets the provided account as a delegated administrator for security
# hub and enables it as the security hub administrator account for the organization.
#
# Prerequisites
# Security Hub trusted access must be enabled as a service in the AWS Organization.  This step should be
# part of the organization initial configuration.


# Make the sh_admin_account_id account the SH admin account
resource "aws_organizations_delegated_administrator" "security_hub_delegation" {
  account_id        = var.sh_admin_account_id
  service_principal = "securityhub.amazonaws.com"
}

# Sent SH admin account as the admin for security hub
resource "aws_securityhub_organization_admin_account" "sh_admin_enable" {
  depends_on = [aws_organizations_delegated_administrator.security_hub_delegation]
  admin_account_id = var.sh_admin_account_id
}