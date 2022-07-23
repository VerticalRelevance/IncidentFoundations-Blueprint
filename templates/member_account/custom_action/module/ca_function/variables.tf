variable "action_name" {
  description = "Name to use for all resources for this lambda custom action"
}

variable "policy_name" {
  default = "policy.json"
  description = "Filename of the lambda policy definition"
}