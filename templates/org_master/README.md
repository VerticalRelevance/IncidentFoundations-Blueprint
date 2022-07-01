# Org Master Account Setup
## 7/1/2022

### Description
This repo contains all artifacts required to configure an AWS organization
to use a centralized security account for the aggregation and management 
of security findings using native AWS services. It enables this functionality
for the four US regions.

### Repo Content
- data.tf  - Defines data objects for Terraform stack
- main.tf  - Defines main resources for Terraform stack 
- output.tf  - Defines output for Terraform stack
- providers.tf  - Defines the AWS provider for the Terraform stack
- README.md - This file
- variables.tf - Defines the variables for the Terraform stack
- version.tf - Contains the Terraform and provider version requirements


### Installation Requirements
The IAC is implemented in Terraform.  See the Hashicorp Terraform 
website for download and installation instructions.
https://www.terraform.io/downloads

Note that this example uses a local state file.  It is highly recommended that
remote state be added for any environment other than development. See Terraform
documentation on configuring a remote backend.

The Terraform version used to develop and test these templates was 1.2.2. Although 
it may work on older versions of Terraform, the providers in the template are set to restrict
the version to 1.2.2 or higher.

1. Clone this repo. 
2. Ensure AWS credentials for the organization master account exist in the 
   execution environment.  The most common method to do this through environment 
   variables.  Although credentials can be added directly to the templates after 
   cloning, it is against security best practices to have them statically in the template file.
3. Initialize Terraform for the execution environment
   #### terraform init
4. Create a terraform plan. Verify that all resources the 
   #### terraform --out [PLAN FILENAME]
5. Apply the plan.
   #### terraform apply [PLAN FILENAME]


### Details
The goal of these templates is to enable Security Hub, GuardDuty and Access
Analyzer to be enabled and managed via a designated central security account
for the Organization.  In order for this to happen a few prerequisites must be met.

#### Prerequisites
1. Security Hub, GuardDuty and Access Analyzer must be enabled as AWS Organization managed services
   1. For Security Hub and GuardDuty AWS recommends doing this through the AWS Organizations console
   2. Access Analyzer should be enabled via the Access Analyzer console in the master account
      by delegating the centralized security account as the delegated admin.
2. A centralized security account must be created within the Organization

For Security Hub, the central account is made a delegated administrator for both
the Security Hub and GuardDuty services.  As stated above, for Access Analyzer 
this needs to be done manually through the console.

For the four US regions, the central security account is designated as the
administrator account for Security Hub and GuardDuty.  At the time of writing
Access Analyzer doesn't require an admin account be designated.

Once these templates successfully run the templates in the sh_admin directory
can be run in the central security account to complete the setup of these
services for the organization.

