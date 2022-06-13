import logging
import os

import boto3


SOURCE_TYPE = "aws.securityhub"
RESOURCE_TYPE = "AwsEc2SecurityGroup"

DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_REMOVE_RULES = ["0.0.0.0/0"]
DEFAULT_DIRECTION = "all"


logging.basicConfig(level=DEFAULT_LOG_LEVEL)
#if os.environ.get("AWS_EXECUTION_ENV") is None:


def lambda_handler(event, context):
    logging.debug("Event: %s", str(event))
    logging.debug("Starting main function")
    main(event)


def main(event):
    logging.debug("Verifying event source")
    if event["source"] != SOURCE_TYPE:
        raise ValueError("Event sounce must be aws.securityhub by way of EventBridge")

    # Pull all sg ids and account/region info from provided event
    event_resources = event_parser(event)
    logging.debug("Discovered SG resources: %s", str(event_resources))

    logging.info(event_resources)

    # Execute rule changes on all discovered sg resources
    # Capable of executing in any region.
    # TODO: Add execution in other accounts
    boto_resource_dict = {}
    for resource, resource_info in event_resources.items():
        if resource_info["region"] not in boto_resource_dict:
            boto_resource_dict[resource_info["region"]] = boto3.resource("ec2", region=resource_info["region"])

        remove_rule(boto_resource_dict[resource_info["region"]], resource, DEFAULT_REMOVE_RULES)


def event_parser(event):
    return_dict = {}

    for finding in event["detail"]["findings"]:
        for resource in finding["Resources"]:
            if RESOURCE_TYPE not in resource["Details"]:
                LOG.debug("Resource is not type %s", RESOURCE_TYPE)
                continue

            # Add SGs to output dictionary. SG id as key.
            return_dict[resource["Details"][RESOURCE_TYPE]["GroupId"]] = {"account_id": finding["AwsAccountId"],
                                                                          "region": finding["Region"]}
    return return_dict


def remove_rule(boto_resource, sg_id, rule_list):
    sg = boto_resource.SecurityGroup(sg_id)

    logging.info(sg.ip_permissions)
    logging.info(sg.ip_permissions_egress)



if __name__ == "__main__":
    event = {}
    main(event)