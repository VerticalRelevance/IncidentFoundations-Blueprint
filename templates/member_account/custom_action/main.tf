module "custom_action_lambdas" {
  source = "./module/ca_function"
  for_each = fileset(path.module, "remediations/*")
  action_name = each.key
}