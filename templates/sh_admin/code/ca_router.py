"""
Module for execution as a Lambda function used with Security Hub custom action for EC2.19.
Defaults to remove 0.0.0.0/0 rules in both direction.  CIDR ranges and direction can be
changed via environment variables.
"""

import json
import logging
import os
import traceback

import boto3


SOURCE_TYPE = "aws.securityhub"
ASSUME_ROLE = "ca_router_ca_role"
AGGREGATION_REGION = "us-east-1"

LOG_LEVEL = logging.INFO
if "DEBUG" in os.environ and os.environ["DEBUG"].lower() == "true":
    LOG_LEVEL = logging.DEBUG
LOG = logging.getLogger()
LOG.setLevel(LOG_LEVEL)
console = logging.StreamHandler()
console.setLevel(LOG_LEVEL)
LOG.addHandler(console)


# Disable boto3 logging spam
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('botocore').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)


def lambda_handler(event, context):
    """
    Function called by AWS Lambda on invocation.
    :param event: dict- AWS lambda input event
    :param context: obj- aws lambda input context object
    :return: dict- standard lambda status return dictionary
    """
    LOG.debug("Event: %s", str(event))
    LOG.debug("Starting main function")

    return_object = ""
    # Catch all exceptions so they can be returned by lambda
    try:
        return_object = main(event)
        status_code = 200

    except Exception:
        status_code = 500
        return_object = {"exception": str(traceback.format_exc())}
        LOG.error(return_object)

    return {'statusCode': status_code,
            'body': json.dumps(return_object)
        }


def main(event):
    """
    Main entrypoint for the module.  Takes in the eventbridge finding event for security hub
    and discovers the security groups contained within.  Calls the remove_rule function for each
    security group found.
    :param event: dict- aws lambda handler input event
    :return:dict- dictionary containing information about removed rules
    """

    LOG.info("Verifying event source as %s", SOURCE_TYPE)
    if event["source"] != SOURCE_TYPE:
        raise ValueError("Event sounce must be aws.securityhub by way of EventBridge")

    event_info = event_parser(event)

    for account in event_info["accounts"]:
        invoke_lambda(
            account=account,
            region=AGGREGATION_REGION,
            action_name=event_info["action_name"],
            event=event
        )


def event_parser(event):
    return_dict = {
        "action_name": event["detail"]["actionName"],
        "accounts": set()
    }
    for finding in event["detail"]["findings"]:
        return_dict["accounts"].add(finding["AwsAccountId"])

    return return_dict


def invoke_lambda(account, region, action_name, event):
    lambda_client = get_client("lambda", account=account, region=region, assume_role_name=ASSUME_ROLE)

    response = lambda_client.invoke(
        FunctionName=action_name,
        InvocationType='Event', # async=Event sync=RequestResponse
        Payload= json.dumps(event)
    )
    LOG.info(response)


def get_client(client_type, account=None, region=None, assume_role_name=None):

    sts_client = boto3.client('sts')
    current_account = sts_client.get_caller_identity().get('Account')

    client_params = {}
    if region:
        client_params["region_name"] = region

    if account and current_account != account:
        if not assume_role_name:
            assume_role_name = ASSUME_ROLE

        assume_role = "arn:aws:iam::%s:role/%s" % (account, assume_role_name)
        assumed_role_object = sts_client.assume_role(
            RoleArn=assume_role,
            RoleSessionName="ar_%s_%s" % (str(account), region)
        )
        client_params["aws_access_key_id"] = assumed_role_object['Credentials']['AccessKeyId']
        client_params["aws_secret_access_key"] = assumed_role_object['Credentials']['SecretAccessKey']
        client_params["aws_session_token"] = assumed_role_object['Credentials']['SessionToken']

    client = boto3.client(client_type, **client_params)

    return client
