# Org Master Account Setup
## 7/1/2022

### Description
This repo contains all artifacts required to configure an AWS organization
to use a centralized security account for the aggregation and management 
of security findings using native AWS services. This example operates on the
four US regions. (us-east-1, us-east-2, us-west-1, us-west-2)

### Repo Content
Note: Some of the below .tf files may be empty but are still included so that all
Terraform projects in this contain the same base set of files.
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
Analyzer as organization level managed services and to set the centralized security account as
the administrator account for the organization. The below prerequisites must be met before
attempting to run these templates.

#### Prerequisites
1. A centralized security account must be created within the Organization
2. Security Hub, GuardDuty and Access Analyzer must be enabled as AWS Organization managed services
   1. For Security Hub and GuardDuty AWS recommends doing this through the AWS Organizations console
   2. Enabling Access Analyzer should be done through the Access Analyzer console 
      in the master account by delegating the centralized security account as the 
      delegated admin.

For Security Hub, the centralized security account is made a delegated administrator for both
the Security Hub and GuardDuty services.  As stated above, the centralized security account
is made a delegated admin for Access Analyzer manually through the IAM AA console.

For the four US regions, the centralized security account is designated as the
administrator account for Security Hub and GuardDuty.  At the time of writing
Access Analyzer doesn't require an admin account be designated.

The Terraform templates here take care of all the org level configuration for GuardDury and
Security Hub. Once these templates successfully run the templates in the ../sh_admin directory
can be run in the centralized security account to complete the setup of these
services for the organization.

### Relationship to sh_admin Templates
As part of enabling services in the centralized security account, resources
are made to add all existing organization member accounts to the services.  The
IDs of all member accounts can be queried from an API call, but only when run in the 
org master account.  To simplify credential usage in sh_admin, these templates add an output data 
object containing a map of the member accounts at execution time. The sh_admin templates import 
this map and use the values to add the member accounts as "managed by" to the services.  It 
assumes that the path to the org_master state file matches that in the repo (ie ../org_master)