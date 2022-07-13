# Role for Custom Action Router Lambda
## 7/9/2022

### Description
These templates create the role that is assumed by the custom action lambda deployed in
the central security account.  The role gives this lambda the ability to invoke the auto
remediation lambdas in a member account.  This role must be created in all member accounts
where organization auto remediations are used.

When creating a new auto remediation, a lambda permission must be created that allows
this role to invoke it.  In terraform this is a aws_lambda_permissions resource and would look 
like the following;

```
resource "aws_lambda_permission" "allow_ca_router_role" {
  statement_id  = <NAME TO USE FOR THE PERMISSION RESOURCE>
  action        = <ACTION THIS PERMISSION GRANTS>
  function_name = <NAME OF LAMBDA THAT WILL ALLOW THE ACTION>
  principal     = <PRINCIPAL OF THE SERVICE, USER OR ROLE BEOMG GRAMTED PERMISSIONS>
  source_arn    = <ARN OF THE SERVICE, USER OR ROLE BEING GRANTED PERMISSION>
}
```

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
remote state be added for any environment other than development.

The Terraform version used to develop and test these templates was 1.2.2. Although 
it may work on older versions of Terraform, the providers in the template are set to restrict
the version to 1.2.2 or higher.

1. Clone this repo. 
2. Ensure AWS credentials exist in the execution environment for the member account where this
   role is to be created.  The user/role must have the ability to create IAM resources.
3. Initialize Terraform for the execution environment
   #### terraform init
4. Create a terraform plan. Verify that all resources the 
   #### terraform --out [PLAN FILENAME]
5. Apply the plan.
   #### terraform apply [PLAN FILENAME]
