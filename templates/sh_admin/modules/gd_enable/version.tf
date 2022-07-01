terraform {
    required_version = ">=1.2.2"
  required_providers {
    aws = {
      version = ">= 4.17.0"
      source = "hashicorp/aws"
    }
  }
}