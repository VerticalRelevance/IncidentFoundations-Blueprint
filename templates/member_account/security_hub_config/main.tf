
# Terraform doesn't let you specify providers dynamically so have to
# have a call for each region.  Using a subset of US regions
# and ap-south-1 and ca-central-1 as a baseline.
module "enable_default_region" {
  count = var.enable_default ? 1 : 0
  source    = "./modules/sh_enable"
}

module "enable_us-east-1" {
  count = var.us-east-1 ? 1 : 0
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-east-1
  }
}

module "enable_us-east-2" {
  count = var.us-east-2 ? 1 : 0
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-east-2
  }
}

module "enable_us-west-1" {
  count = var.us-west-1 ? 1 : 0
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-west-1
  }
}

module "enable_us-west-2" {
  count = var.us-west-2 ? 1 : 0
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.us-west-2
  }
}

module "enable_ap-south-1" {
  count = var.ap-south-1 ? 1 : 0
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.ap-south-1
  }
}

module "enable_ca-central-1" {
  count = var.ca-central-1 ? 1 : 0
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.ca-central-1
  }
}

# Sets up the default region as the SH aggregation region
resource "aws_securityhub_finding_aggregator" "sh_aggregator" {
  count = var.enable_aggregation ? 1 : 0
  linking_mode = "ALL_REGIONS"
  depends_on = [module.enable_default_region]
}
