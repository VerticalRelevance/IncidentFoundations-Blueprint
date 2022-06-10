import os 

import boto3


def lambda_handler(event, context):
    print(event)
    print(context)

    remove_rule()




def remove_rule(sg_id, rule_list):
    ec2_resource = boto3.resource("ec2")
    sg = ec2_resource.SecurityGroup(sg_id)

    print(sg.ip_permissions)



    print(sg.ip_permissions_egress)