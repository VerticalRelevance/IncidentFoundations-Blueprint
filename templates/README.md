# Using as a Custom Resource
The custom resource in this example solution is called using the Cloudformation template cr_deploy.template.  This template will enable Security Hub as well as Guardduty and Inspector for the regions indicated in the CF input parameters.  Each service has its own custom resource, even though a single invocation of the custom resource would be able to configure N services. This was done so that it is easy to see when a specific service deployment fails during a stack update.

### Prerequisites:
- S3 bucket where custom resource lambda zip file can be placed.

### Create
Create a new cloudformation stack using the cr_deploy.template. This can be done using the AWS console, the AWS CLI or the included install.py python script in this directory.  Upon successful stack creation Security Hub, Guardduty and inspector will be enabled for the organization and all org members will be managed by the delegated admin account for all three services in the regions specified in the stack parameters.

### Delete
Deleting the Cloudformation stack will remove the delegated admin account for the services. The management of service resources and findings will fall back to the local account.  Stack delete can be done via the console or AWS CLI.  install.py does not support delete functionality.

### install.py
install.py is a python script that provides a way to deploy the solution stack without the need to use the console or execute multiple AWS CLI commands.  It packages up the files used by the custom resource, uploads them to the S3 bucket provided by the user and then creates a new Cloudformation stack to enable and configure the solution services.
```
usage: install.py [-h] --deladmin DELADMIN --bucket BUCKET --shregions SHREGIONS --gdregions GDREGIONS
                  --inregions INREGIONS [--crfilename CRFILENAME] [--stackname STACKNAME]
                  [--cftemplate CFTEMPLATE]

options:
  --deladmin DELADMIN   ID of the delegated admin account
  --bucket BUCKET       S3 bucket for CR zip file
  --shregions SHREGIONS
                        Security Hub enabled regions
  --gdregions GDREGIONS
                        Guardduty enabled regions
  --inregions INREGIONS
                        Inspector enabled regions
  --crfilename CRFILENAME
                        Filename to use for the CR zip
  --stackname STACKNAME
                        New CF stack name
  --cftemplate CFTEMPLATE
                        CF template filename
```