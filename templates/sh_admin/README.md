# Centralized Security Account SH Aggregation and Member Region Configuration
## 6/15/2022

### Description
This repo contains all artifacts required to enable Security Hub, GuardDuty and
Access Analyzer through the organization centralized security account.  It also creates
the Custom Action routing lambda and EventBridge rules used to route CA invokations to
member accounts.

### Repo Content
Note: Some of the below .tf files may be empty but are still included so that all
Terraform projects in this contain the same base set of files.
- code/ca_router.py - Python code that is used for the ca_router lambda function
- modules/sh_enable - Terraform module that enables Security Hub for a single region
- modules/gd_enable - Terraform module that enables GuardDuty for a single region
- data.tf  - Defines data objects for Terraform stack
- main.tf  - Defines main resources for Terraform stack 
- output.tf  - Defines output for Terraform stack
- providers.tf  - Defines the AWS provider for the Terraform stack
- README.md - This file
- variables.tf - Defines the variables for the Terraform stack
- version.tf - Contains the Terraform and provider version requirements

### Details

#### Service Configuration


#### Custom Action Router
The Custom Action routing lambda routes custom action events created in the Centralized
Security account to the respective member account for the finding.  It is triggered for 
each custom action event.  It pulls the account id, region and finding name from the payload
and then invokes the appropriate lambda in the target member account.  A cross account role, 
ca_router_ca_role, is created in each member account as part of their provisioning.  This
role is used to invoke any remediation lambda in member accounts.  Each auto remediation 
lambda is configured allow this role to invoke their lambda.


### Use
The IAC is implemented in Terraform.  See the Hashicorp Terraform 
website for download and installation instructions.
https://www.terraform.io/downloads

Note that this example uses a local state file.  It is highly recommended that
remote state be added for any environment other than development.

The Terraform version used to develop and test these templates was 1.2.2. Although 
it may work on older versions of Terraform, the providers in the template are set to restrict
the version to 1.2.2 or higher.

1. Clone this repo. 
2. Create a terraform.tfvars file and place all input parameters in this file.  If this is 
   being run in multiple accounts which need different regions enabled, a seperate tfvers file
   should be made for each one.  Input parameters can be input at the command line, but for 
   auditability purposes this should be avoided in any environment but Dev.
3. Ensure AWS credentials exist in the execution environment.  The most common 
   method to do this through environment variables.  Although credentials
      can be added directly to the templates after cloning, it is against security best
      practices to have them statically in the template file.
4. Initialize Terraform for the execution environment
   #### terraform init
5. Create a terraform plan. Verify that all resources the 
   #### terraform --out [PLAN FILENAME]
6. Apply the plan.
   #### terraform apply [PLAN FILENAME]


