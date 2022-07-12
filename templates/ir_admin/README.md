# Setup Incident Manager
## 7/5/2022

### Description
This repo contains all artifacts required to enable Incident Manager in
an Organizations operations hub account.


### Repo Content
- data.tf  - Defines data objects for Terraform stack
- main.tf  - Defines main resources for Terraform stack 
- output.tf  - Defines output for Terraform stack
- providers.tf  - Defines the AWS provider for the Terraform stack
- README.md - This file
- variables.tf - Defines the variables for the Terraform stack
- version.tf - Contains the Terraform and provider version requirements


### Use
Terraform does not currently support the creation of replication set
for Incident Manager.  To keep consistency with the other blueprints,
Terraform is still used to create a Cloudformation stack that creates
the required replication set 
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

### Details
