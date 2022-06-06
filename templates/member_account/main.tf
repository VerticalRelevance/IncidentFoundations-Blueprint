resource "aws_securityhub_account" "current_account" {}

# Sets up region aggregation for SH
resource "aws_securityhub_finding_aggregator" "sh_aggregator" {
  linking_mode = "ALL_REGIONS"
  depends_on = [aws_securityhub_account.current_account]
}

