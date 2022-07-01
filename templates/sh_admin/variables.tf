variable "org_master_state_location" {
  description = "Path to the state file created by the org_master templates"
  default = "../org_master/terraform.tfstate"
}

variable "enable_guardduty" {
  description = "Enable guardduty"
  default = true
}

variable "enable_accessanalyzer" {
  description = "Enable access analyzer"
  default = true
}