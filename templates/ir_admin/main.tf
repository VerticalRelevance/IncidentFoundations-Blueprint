
resource "aws_cloudformation_stack" "ir_enable_stack" {
  name = "ssmir-replication-set"
  parameters = {"KeyArn": var.key_arn}
  template_body = file("${path.module}/ir_main.yml")
}