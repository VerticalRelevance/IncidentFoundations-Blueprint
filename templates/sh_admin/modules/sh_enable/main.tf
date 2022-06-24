# Auto enable security hub in organization member accounts
resource "aws_securityhub_organization_configuration" "autoenable_sh" {
  auto_enable = true
}

# Add existing accounts as managed to sh hub.
resource "aws_securityhub_member" "example" {
  for_each   = {for account in var.sh_member_accounts:  account[0] => account[1] if account[0] != data.aws_caller_identity.current.account_id}
  account_id = each.key
  email      = each.value
}