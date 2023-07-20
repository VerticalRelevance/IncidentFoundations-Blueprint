# Incident Response Foundations-Blueprint

This solution uses Cloudformation and a Lambda based custom resource to configure a Security Hub based Instance Responce solution in an AWS Organization. At the time of implementation, Cloudformation does not natively support the resources required to enable and configure the AWS services used by this solution.

Security Hub serves as the repository and aggragation mechanism for AWS services like Guardduty and Inspector.

AWS Organizations is used to designate a single account as the delegated admin for all of the configured services.  The configuration of the individual services, including configuring auto-join, is done per service through the delegated admin account.

Any existing member accounts are discovered using Organizations APIs and added as "managed by" accounts to the delegated admin.

## Directories
diagrams- Contains draw.io and png files for the diagrams used in the playbook associated with this solution

templates- Contains all Cloudformation and python artifacts that are used to implement the solution in "IAC".

```bash
├── diagrams
│   ├── high_level.drawio
│   ├── high_level.png
│   ├── Incident_Response.drawio
│   ├── Incident_Response.png
├── templates
│   ├── custom_resources
│   │   ├── org_accounts
│   │       ├── __init__.py
│   │       ├── manager.py
│   │   ├── cfnresponse.py
│   │   ├── common.py
│   │   ├── guardduty.py
│   │   ├── inspector.py
│   │   ├── ir_setup.py
│   │   ├── securityhub.py
│   ├── install.py
│   ├── cr_deploy.template
```

The custom resource version of this solution uses the cr_deploy.template and the python modules located in the templates/custom_resources directory.  See the README file in the templates directory for details.

The modules in the templates/custom_resources can be used from the command line using python by running the ir_setup.py module with the correct command line parameters. See the readme in the templates/custom_resources directory.