# Security Hub Custom Action 0.0.0.0/0 Rule Removal
## 6/15/2022

### Description
This repo contains all artifacts required to create a AWS Security Hub custom 
action backed by a lambda function using Terraform.  This custom action is 
intended for use on AWS Foundational Security Best Practices EC2.19 findings 
to remove all 0.0.0.0/0 rules from a security group.  The solution contains 
the following high level AWS resources.

- Security Hub Custom Action
- EventBridge Rule for the Custom Action
- Lambda function

See the main.tf template for the additional resources required for EventBridge
and Lambda execution.

### Repo Content
- /code/sgr.py - Python module used in the auto-remediation lambda
- data.tf  - Defines data objects for Terraform stack
- main.tf  - Defines main resources for Terraform stack 
- output.tf  - Defines output for Terraform stack
- providers.tf  - Defines the AWS provider for the Terraform stack
- variables.tf - Defines the variables for the Terraform stack
- version.tf - Contains the Terraform and provider version requirements


### Installation Requirements
The IAC is implemented in Terraform.  See the Hashicorp Terraform 
website for download and installation instructions.
https://www.terraform.io/downloads

Note that this example uses a local state file.  It is highly recommended that
remote state be added for any environment other than development.

The Terraform version used to develop and test these templates was 1.2.2. Although 
it may work on older versions of Terraform, the providers in the template are set to restrict
the version to 1.2.2 or higher.

1. Clone this repo. 
2. Ensure AWS credentials exist in the execution environment.  The most common 
   method to do this through environment variables.  Although credentials
      can be added directly to the templates after cloning, it is against security best
      practices to have them statically in the template file.
3. Initialize Terraform for the execution environment
   #### terraform init
4. Create a terraform plan. Verify that all resources the 
   #### terraform --out [PLAN FILENAME]
5. Apply the plan.
   #### terraform apply [PLAN FILENAME]


### Use