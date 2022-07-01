

# Configure organization to use GS
resource "aws_guardduty_organization_configuration" "gd_org" {
  auto_enable = true
  detector_id = data.aws_guardduty_detector.gd_detector.id

  datasources {
    s3_logs {
      auto_enable = true
    }
  }
}

resource "aws_guardduty_member" "member" {
  for_each    = {for account in var.member_accounts:  account[0] => account[1] if account[0] != data.aws_caller_identity.current.account_id}
  account_id  = each.key
  detector_id = data.aws_guardduty_detector.gd_detector.id
  email       = each.value
}
