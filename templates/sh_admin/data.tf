data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "org_master" {
  backend = "local"
  config = {
    path = var.org_master_state_location
  }
}