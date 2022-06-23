# A provider must be defined for every region where SH is going to be enabled

provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias = "us-east-2"
  region = "us-east-2"
}

provider "aws" {
  alias = "us-west-1"
  region = "us-west-1"
}

provider "aws" {
  alias = "us-west-2"
  region = "us-west-2"
}
