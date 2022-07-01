data "aws_caller_identity" "current" {}

# Note: When the account is enabled as an admin via the master account a detector
# is automatically created.
data "aws_guardduty_detector" "gd_detector" {}