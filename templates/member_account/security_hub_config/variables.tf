variable "enable_default" {
  type        = bool
  description = "Enable Security Hub in the default region credentials"
  default     = false
}

variable "enable_aggregation" {
  type        = bool
  description = "Enable aggregation of findings to the default region for credentials used"
  default     = false
}

variable "us-east-1" {
  type        = bool
  description = "Enable Security Hub in the us-east-1 region"
  default     = false
}

variable "us-east-2" {
  type        = bool
  description = "Enable Security Hub in the us-east-2 region"
  default     = false
}

variable "us-west-1" {
  type        = bool
  description = "Enable Security Hub in the us-west-1 region"
  default     = false
}

variable "us-west-2" {
  type        = bool
  description = "Enable Security Hub in the us-west-2 region"
  default     = false
}

variable "ap-south-1" {
  type        = bool
  description = "Enable Security Hub in the ap-south-1 region"
  default     = false
}

variable "ca-central-1" {
  type        = bool
  description = "Enable Security Hub in the ca-central-1 region"
  default     = false
}
