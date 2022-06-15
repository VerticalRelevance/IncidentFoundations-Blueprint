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
RESOURCE_TYPE = "AwsEc2SecurityGroup"
DEFAULT_CIDR_LIST = ["0.0.0.0/0"]
DEFAULT_DIRECTION = "both"


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
        LOG.error(return_message)

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
    # Check environment variables for values for direction and rule CIDRS
    if "DIRECTION" in os.environ:
        rule_direction = os.environ["DIRECTION"]
    else:
        rule_direction = DEFAULT_DIRECTION

    if "CIDR" in os.environ:
        cidr_list = os.environ["CIDR"].split(",")
    else:
        cidr_list = DEFAULT_CIDR_LIST

    LOG.info("Verifying event source as %s", SOURCE_TYPE)
    if event["source"] != SOURCE_TYPE:
        raise ValueError("Event sounce must be aws.securityhub by way of EventBridge")

    # Pull all sg ids and account/region info from provided event
    event_resources = event_parser(event)
    LOG.info("Discovered SG resources: %s", str(event_resources))

    removed_dict = {}
    boto_resource_dict = {}
    for resource, resource_info in event_resources.items():
        # If ec2 resource object doesn't exist for the region, create one
        if resource_info["region"] not in boto_resource_dict:
            boto_resource_dict[resource_info["region"]] = boto3.resource(
                "ec2",
                region_name=resource_info["region"]
            )
        removed_rules = remove_rule(
            boto_resource=boto_resource_dict[resource_info["region"]],
            sg_id=resource,
            cidr_list=cidr_list,
            direction=rule_direction
        )
        # Save list of rules removed from security group for
        # output.
        if removed_rules:
            removed_dict[resource] = removed_rules

    return removed_dict

def remove_rule(boto_resource, sg_id, cidr_list, direction):
    """
    Removes rules contaiing the CIDR range(s) contained in the cidr_list input parameter.
    :param boto_resource: boto3 ec2 resource object (used for creating sg resource objets)
    :param sg_id: str- id of the security group to act upon
    :param cidr_list: list- list of CIDRS to look for in the security group
    :param direction: str- the flow direction of rules to remove (ingress/egress/both)
    :return: list- list containing information about rules removed from the security group
    """
    valid_directions = ["ingress", "egress", "both"]
    if direction not in valid_directions:
        raise ValueError("Invalid direction parameter %s. Must be one of %s" %\
                         (str(direction), str(valid_directions)))
    if direction == "both":
        execution_list = ["ingress", "egress"]
    else:
        execution_list = [direction]

    sg_object = boto_resource.SecurityGroup(sg_id)
    direction_dict = {
        "ingress": {"attribute": sg_object.ip_permissions, "method": sg_object.revoke_ingress },
        "egress": {"attribute": sg_object.ip_permissions_egress, "method": sg_object.revoke_egress}
    }

    return_list = []
    for current_direction in execution_list:
        LOG.info("Checking %s rules", current_direction)
        remove_list = []
        for rule in direction_dict[current_direction]["attribute"]:
            for cidr in cidr_list:
                if {'CidrIp': cidr} in rule['IpRanges']:
                    LOG.debug("Will remove rule %s", rule)
                    remove_list.append(rule)

        if remove_list:
            LOG.info("Removing rules %s", str(remove_list))
            return_list.extend(remove_list)
            direction_dict[current_direction]["method"](
                GroupId=sg_id,
                IpPermissions=remove_list)
        else:
            LOG.info("No rules found matching delete criteria")

    return return_list

def event_parser(event):
    """
    Parses the event passed in to the Lambda and returns a dictionary containing the security
    group IDs as keys and a dictionary containing their region and account as a value. It expects
    that the incoming event is from an eventbridge rule configured for Security Hub custom actions.
    :param event: dict- eventbrindge finding event
    :return: dict- security groups contained within the input event
    """
    return_dict = {}
    for finding in event["detail"]["findings"]:
        for resource in finding["Resources"]:
            if RESOURCE_TYPE not in resource["Details"]:
                LOG.debug("Resource is not type %s", RESOURCE_TYPE)
                continue

            return_dict[resource["Details"][RESOURCE_TYPE]["GroupId"]] = \
                {"account_id": finding["AwsAccountId"],
                 "region": finding["Region"]}
    return return_dict
