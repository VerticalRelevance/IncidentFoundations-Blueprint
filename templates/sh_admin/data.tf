data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "org_master" {
  backend = "local"
  config = {
    path = "../org_master/terraform.tfstate"
  }
}