data "aws_region" "current" {}

data "local_file" "cf_template" {
    filename = "${path.module}/ir_main.yml"
}