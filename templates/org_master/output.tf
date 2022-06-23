output "org_accounts" {
  value = [ for org_account in data.aws_organizations_organization.master_account.accounts: tolist([org_account.id, org_account.email])]
}
