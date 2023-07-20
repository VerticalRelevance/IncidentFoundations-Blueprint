# custom_resources

## Code
ir_setup.py is the entrypoint for the custom resource and when executing from the command line.  This module contains the IRManager class which calls the supported service modules, lambda handler function "lambda_handler" and the helper functions.  These helper functions are responsible for parsing the custom resource event into an input dictionary understandable by the three main  IRManager methods (create, update and destroy).  The common.py module is used for things like arg parsing, loading json file contents and helper classes for boto3 clients.

The three main methods of IRManager align with Cloudformation stack request types of create, update and delete.  All methods expect a config dictionary which contains service specific root keys and their required configuration key/value pairs.  Currently, the three services supported are Security Hub, Guardduty and Inspector v2.

### Example config dictionary:
```
{
    "securityhub": {
        "admin_account_id": "919574677846",
        "aggregate_region": "us-east-1",
        "enable_for_management": true,
        "enable_regions": [
        "us-east-1",
        "us-east-2"
        ]
    },
    "guardduty": {
        "admin_account_id": "919574677846",
        "enable_regions": [
        "us-east-1",
        "us-east-2"
        ]
    }
}
```

The root keys of the config dictionary are the service(s) to enable and configure.  The three valid key names are "securityhub" for Security Hub, "guardduty" for GuardDuty and "inspector" for Inspector V2.  Note that although the CF template requires that parameters be provided for all three services, ir_setup.py can be called with any combination of supported services.

### All Service Required Parameters
All supported services must include the following key/value pair parameters.

- admin_account_id: AWS account ID of the delegated administrator account to use for the service.  Although the module does support a different account ID for each service it is recommended that one account is used for all security related services.

- enable_regions: AWS regions to where the service should be enabled.  Note that for Security Hub and GuardDuty any region that is not included will be explicitly disabled for the delegated admin.

### Security Hub Parameters
The additional parameters for the security hub config section are optional.  If they are not provided defaults are used.  It is highly recomended that these values are explicitly provided for clarity.

- aggregate_region: AWS region to use as the aggregate region for Security Hub findings.  If no region is provided us-east-1 is used.

- enable_for_management: Flag to enable Security Hub for the Organizations Management account.

### GuardDuty
GuardDuty does not currently support any additional parameters.

### Inspector V2
Inspector does not current support any additional parameters.


Each service has a defined module and class that handles the implementation of it in this solution.  Their module associations are defined at the top of the IRManager class.

```
    SERVICE_CLASS_MAPPING = {
        "securityhub": securityhub.Securityhub,
        "guardduty": guardduty.Guardduty,
        "inspector": inspector.Inspector
    }
```
Each of these classes has a create, update and destroy method.  These methods are the only interface IRManager uses when calling the supported classes.

All custom resources utilize the base manager.py module and its' OrgManager class as their base class.  This base class contains methods common to most AWS services that support Organizations management.


## Using from Command Line
Using ir_setup.py from the command line requires AWS credentials with the same permissions as those defined in the cr_deploy.template file. In addition, the input parameters for the services you wish to configure need to be placed in a json file.  When invoking the module, this json file is read and for each service defined the appropriate service module is run for the type of request.  There is no need to run this for each service to be enabled.

### Required Parameters:
--config - filename of the input json document containing required information to deploy one or more supported services

--create or --destroy Action to take on the services defined in the json config file.

```
  --config CONFIG  IR config json file
  --target TARGET  AWS account ID of organization master
  --role ROLE      AWS IAM role to assume in organization master
  --exid EXID      External ID for organization master role
  --create         Enable or update IR services.
  --destroy        Remove the services defined in the config file
  --debug          Set logging level to debug
```

## Credentials
As a prerequisite, AWS credentials from the organizations management account capable of making the various organizations and service API calls must either be part of the AWS credentials defined in the environment where the code is run or part of a role that can be assumed by the AWS credentials from the execution environment. When run as a custom resource, the lambda role is created with the necessary permissions.

When configuring the services in the delegated admin account the AWS organizations created role "OrganizationAccountAccessRole" is assumed using the management account credentials.

## Destroy
The destroy functionality of all services removes the assignment of a delegated administrator for the organization but does NOT disable the service in any member account.  This was done on purpose to ensure that findings and automations arent disabled before resolution.  In addition, there may be cases where a record of these events is required for auditing purposes.
