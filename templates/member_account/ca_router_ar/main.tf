resource "aws_iam_role" "ca_router_ca_role" {
  name                = "ca_router_ca_role"
  assume_role_policy  = data.aws_iam_policy_document.lambda_assume_policy.json 
  inline_policy {
    name   = "ca_router_ca_policy"
    policy = data.aws_iam_policy_document.ca_router_policy.json
  }  
}


