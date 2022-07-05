
resource "aws_cloudformation_stack" "ir_enable_stack" {
  name = "ssmir-replication-set"

  parameters = {}

  template_body = data.local_file.cf_template.content
}