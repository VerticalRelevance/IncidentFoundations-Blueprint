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
1. The security engineer logs in to the AWS console and switches to the region where all Security Hub findings are aggregated.
   - Either in findings or insights,  they look for EC2.19 findings that are in FAILED compliance status. 
   - The findings are analyzed.  Findings linked to security groups that need to be altered are selected. 
   - The engineer selects the “remove0rules” action from the  actions dropdown menu. A message at the top of the console will indicate that the findings have been sent to CloudwatchEvents.   


2. Security Hub creates one or more new Cloudwatch event(s) that contains the information about the findings to be remedied.

3. The EventBridge rule is triggered by the Security Hub event(s) 

4. The EventBridge rule triggers the configured lambda target, passing in the finding information as an event. 

5. The sg_remove_rule lambda starts 
   - The event is parsed and the ID of the associated security groups, their region and account ID is pulled out. 

   - The rules for each of the security groups discovered in 5.1 are parsed.  Any ingress or egress rules that contain  0.0.0.0/0 are removed from the security group. 

The next time Security Hub performs the check on the SG resource it will find the offending rules have been removed and 
the finding status will be updated. 

The behavior of sg_remove_rule can be modified by updating the DIRECTION and CIDR 
environment variables used by the lambda function.  This can be done by adding these to the lambda resource definition 
in main.tf. 

Valid values for DIRECTION are
- ingress 
- egress 
- both 

The value of CIDR is a comma separated string.  Each substring must be a valid CIDR range.   

 