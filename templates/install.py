"""
Helper module that creates the Incident Response Foundations solution
Cloudformation stack in an Organizations' management account.
"""
import argparse
import os
from zipfile import ZipFile


import boto3


CR_DIRECTORY = "custom_resources"
IR_STACKNAME = "IRSolution"
IR_TEMPLATE = "cr_deploy.template"

DEFAULT_CR_ZIP_FILENAME = "ir_manager.zip"
CR_ZIP_DIRECTORY = "custom_resources"
CR_ZIP_FILE_LIST = [
    "ir_setup.py",
    "guardduty.py",
    "common.py",
    "securityhub.py",
    "cfnresponse.py",
    "inspector.py",
    "org_accounts/__init__.py",
    "org_accounts/manager.py"
]


def main(args):
    base_directory = os.getcwd()
    s3_client = boto3.client('s3')
    cf_client = boto3.client('cloudformation')

    bucket = args.bucket
    delegated_account = args.deladmin
    sh_regions = args.shregions
    gd_regions = args.gdregions
    in_regions = args.inregions

    stack_name = args.stackname
    if not stack_name:
        stack_name = IR_STACKNAME

    zip_filename = args.crfilename
    if not zip_filename:
        zip_filename = DEFAULT_CR_ZIP_FILENAME

    cf_template = args.cftemplate
    if not cf_template:
        cf_template = IR_TEMPLATE


    if os.path.isfile(zip_filename):
        print("Removing existing CR zip file %s" % zip_filename)
        os.remove(zip_filename)

    artifact_zip = os.path.join(base_directory, zip_filename)
    with ZipFile(artifact_zip, 'w') as zip_object:
        for file in CR_ZIP_FILE_LIST:
            zip_object.write(os.path.join(base_directory, CR_ZIP_DIRECTORY, file),
                             arcname=file)

    # Upload CR Zip
    print("Uploading CR Zip to bucket %s" % bucket)
    response = s3_client.upload_file(artifact_zip, bucket, zip_filename)

    # Upload CF Template
    print("Uploading CF Template to bucket %s" % bucket)
    cf_template = os.path.join(base_directory, cf_template)
    response = s3_client.upload_file(cf_template, bucket, cf_template)

    parameter_list = [
            {'ParameterKey': "LambdaZipBucket", 'ParameterValue': bucket},
            {'ParameterKey': "AdminAccountId", 'ParameterValue': delegated_account},
            {'ParameterKey': "SHEnableRegions", 'ParameterValue': sh_regions},
            {'ParameterKey': "GDEnableRegions", 'ParameterValue': gd_regions},
            {'ParameterKey': "INEnableRegions", 'ParameterValue': in_regions}
        ]

    print("Creating solution Cloudformation stack")
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket,
                'Key': cf_template}
        )

    response = cf_client.create_stack(
        StackName=stack_name,
        TemplateURL=presigned_url,
        Parameters=parameter_list,
        Capabilities=[
            'CAPABILITY_IAM',
            'CAPABILITY_NAMED_IAM',
        ],
        OnFailure='DO_NOTHING'
    )

    print("Waiting for stack create to complete")
    waiter = cf_client.get_waiter("stack_create_complete")
    waiter.wait(
        StackName=response["StackId"]
    )

if __name__ == "__main__":
    arg_dict = {
        "--deladmin" : {"help": "ID of the delegated admin account",
                        "required": True},
        "--bucket" : {"help": "S3 bucket for CR zip file",
                        "required": True},
        "--shregions" : {"help": "Security Hub enabled regions",
                        "required": True},
        "--gdregions" : {"help": "Guardduty enabled regions",
                        "required": True},
        "--inregions" : {"help": "Inspector enabled regions",
                        "required": True},
        "--crfilename" : {"help": "Filename to use for the CR zip"},
        "--stackname" : {"help": "New CF stack name"},
        "--cftemplate" : {"help": "CF template filename"}
    }

    parser = argparse.ArgumentParser()
    for arg in arg_dict:
        parser.add_argument(arg, **arg_dict[arg])

    args = parser.parse_args()
    main(args)
