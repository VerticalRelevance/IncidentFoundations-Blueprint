module "custom_action_lambdas" {
  source = "./module/ca_function"
  for_each = toset(split(",", var.remediation_list))
  action_name = each.key
}
