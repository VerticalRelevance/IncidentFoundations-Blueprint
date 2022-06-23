# Using data object to get a snapshot of accounts that are part of the organization so that
# they can be added as managed by the Security Hub hub account.
data "aws_organizations_organization" "master_account" {}