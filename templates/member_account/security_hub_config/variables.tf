variable "regions" {
  type        = list(string)
  description = "List of regions where Security Hub will be enabled (Use 'friendly' names.)"
  nullable    = false
}

#variable "aggregate_region" {
#  type        = string
#  description = "Aggregation region for Security Hub findings. (Use 'friendly' names.)"
#  default     = "virginia"
#  nullable    = false
#}