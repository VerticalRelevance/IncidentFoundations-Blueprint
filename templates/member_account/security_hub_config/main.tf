
# Enable SH in aggregation account
module "sh_enable_virginia" {
  for_each = [var.regions]
  source    = "./modules/sh_enable"
  providers = {
    aws = aws.each.key
  }
}

# Sets up region aggregation for SH
#resource "aws_securityhub_finding_aggregator" "sh_aggregator" {
#  provider = aws.var.aggregate_region
#  linking_mode = "ALL_REGIONS"
#  depends_on = [module.sh_enable]
#}

