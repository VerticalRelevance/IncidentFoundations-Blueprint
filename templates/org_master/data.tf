# Using data object to get a snapshot of accounts that are part of the organization so that
# they can be used by the SH admin account template to put existing accounts under SH org management
data "aws_organizations_organization" "master_account" {}