
# Create Organization Security Hub admin account
resource "aws_organizations_account" "sh_admin_account" {
  name  = var.sh_admin_account_name 
  email = var.sh_admin_account_email 
}

# Make the sh_admin_account_id account the SH admin account
resource "aws_organizations_delegated_administrator" "security_hub_delegation" {
  account_id        = aws_organizations_account.sh_admin_account.id
  service_principal = "securityhub.amazonaws.com"
}

# Enable Security Hub to be managed at the Org level
resource "aws_organizations_organization" "org_sh" {
  aws_service_access_principals = ["securityhub.amazonaws.com"]
  feature_set                   = "ALL"
}

# Enables security hub in the org main account
resource "aws_securityhub_account" "sh_admin_account" {}

# Security Hub Organization level management must be enabled before 
# assigning a admin account for SH
resource "aws_securityhub_organization_admin_account" "example" {
  depends_on = [aws_organizations_organization.org_sh]

  admin_account_id = aws_organizations_account.sh_admin_account.id
}

# Auto enable security hub in organization member accounts
resource "aws_securityhub_organization_configuration" "autoenable_sh" {
  auto_enable = true
}


resource "aws_organizations_organization" "iam_aa_enable" {
  aws_service_access_principals = ["access-analyzer.amazonaws.com"]
}

resource "aws_accessanalyzer_analyzer" "enable_iam_aa" {
  depends_on = [aws_organizations_organization.iam_aa_enable]

  analyzer_name = "example"
  type          = "ORGANIZATION"
}



