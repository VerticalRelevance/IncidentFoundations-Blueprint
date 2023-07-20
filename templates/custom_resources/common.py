"""
Module that contains general helper and wrapper functions to help with the
management of general python and boto3 objects.
"""
import argparse
import importlib
import logging
import os
import sys
import json
from uuid import uuid4

import boto3


class ClientManager:
    """
    Class to help with the management of boto3 clients for a multi service
    multi region use.
    """
    def __init__(self, access_key=None, secret_key=None, token=None, region=None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = token
        self.default_region = region
        if not self.default_region:
            self.default_region = "us-east-1"

        self.__boto3_clients = {}

    def client(self, service_name, region_name=None):
        """
        Returns a boto3 client for the service and region requested.  If the
        client has already been created the existing client will be returned.
        Args:
        service_name - Name of AWS service
        Kargs:
        region_name - AWS region name

        Returns a boto3 client for the service and region requested.
        """
        if service_name not in self.__boto3_clients:
            self.__boto3_clients[service_name] = {}

        if not region_name:
            region_name = self.default_region

        if region_name not in self.__boto3_clients[service_name]:
            self.__boto3_clients[service_name][region_name] = \
                boto3.client(
                service_name,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                aws_session_token=self.token, region_name=region_name)

        return self.__boto3_clients[service_name][region_name]


def get_client(service_name, session_object=None,
               target_account=None, assume_role_name=None, external_id=None,
               region=None):
    """
    Create and return a boto3 client.  If a target account is included the client
    will be created as a assumed role client.
    Args:
    service_name - Name of the new client service

    Kargs:
    session_object - boto3 session object
    target_account - AWS account ID of the account containing the role to be assumed
    assume_role_name - Name of the role to assume in the target account
    external_id - External ID for the role being assumed.
    region - AWS region

    Returns boto3 client for the service requested

    """
    logging.debug("Creating new boto3 client for service %s", service_name)

    if session_object:
        logging.debug("Using provided boto3 session object for client creation")
        create_client_function = session_object.client
    else:
        create_client_function = boto3.client

    client_params = {"region_name": region}
    if target_account and assume_role_name:
        sts_client = create_client_function("sts")
        client_params["aws_access_key_id"], \
        client_params["aws_secret_access_key"], \
        client_params["aws_session_token"] = assume_role(
            sts_client,
            target_account=target_account,
            assume_role_name=assume_role_name,
            external_id=external_id)

    return create_client_function(service_name, **client_params)


def assume_role(sts_client, target_account, assume_role_name, external_id=None):
    """
    Takes a base boto3 client and assumes the role provided in the target_account and
    assume_role_name parameters.  Returns the access key, secret key and token of the
    assumed role.
    Args:
    sts_client - boto3 sts client object
    target_account - AWS account ID of the account containing the role to be assumed
    assume_role_name - Name of the role to assume in the target account
    Kargs:
    external_id - External ID for the role being assumed.

    Returns the access key, secret key and token of the assumed role as strings.
    """
    ar_param_dict = {
        "RoleArn": f"arn:aws:iam::{target_account}:role/{assume_role_name}",
        "RoleSessionName": f'{str(uuid4())[:8]}_{target_account}_{assume_role_name}',
    }
    if external_id:
        ar_param_dict["ExternalId"] = external_id
    logging.debug("Requesting assume role credentials for %s", ar_param_dict['RoleArn'])
    response = sts_client.assume_role(**ar_param_dict)
    return response["Credentials"]["AccessKeyId"], \
           response["Credentials"]["SecretAccessKey"], \
           response["Credentials"]["SessionToken"]


def parse_args(arg_dict):
    """
    Helper function for creating a argparser.
    Args:
    arg_dict - Dictionary where the keys are the argument and the value is the
               argparse argument setup parameters.
    Returns an argparse object of the values parsed from the command line
    """
    parser = argparse.ArgumentParser()

    for arg in arg_dict:
        parser.add_argument(arg, **arg_dict[arg])

    return parser.parse_args()


def load_json(filename):
    """
    Helper for loading the content of a json file and returning it as a python
    dictionary.
    Args:
    filename - File contain the JSON content to load.

    Returns python dictionary of the JSON content
    """
    logging.debug("Parsing content of file %s", filename)
    with open(filename, 'r') as file_handle:
        return json.load(file_handle)


def setup_logging(log_filename=None, log_level=None):
    """
    Helper that configures base logging for the root log object.  If logging
    level is not set to logging.DEBUG botocore logging level is set to logging.WARNING.
    Kargs:
    log_filename - Filname to use for the log output of the logger
    log_level - Logging level to use for the logging object (DEFAULT=logging.INFO)

    Returns None
    """
    param_dict = {
        "encoding": "utf-8",
        "format": '%(asctime)s | %(levelname)s:%(message)s',
    }
    if log_filename:
        param_dict["filename"] = log_filename

    if not log_level:
        param_dict["level"] = logging.INFO
    else:
        param_dict["level"] = log_level

    if param_dict["level"] != logging.DEBUG:
        logging.getLogger('botocore').setLevel(logging.WARNING)

    logging.basicConfig(**param_dict)


def import_module(module_filename):
    """
    Helper function that performs a dynamic import of the python module
    indicated by the module_filename parameter.
    Args:
    module_filename - Full filename of the python module to import

    Returns the loaded module object
    """
    if not module_filename.endswith(".py"):
        logging.warning("Supplied filename %s does not end with .py", module_filename)

    module_file = os.path.split(module_filename)[-1]
    module_name = module_file.replace(".py","").replace('-', '_')
    logging.debug("Loading module %s from %s", module_name, module_filename)

    spec = importlib.util.spec_from_file_location(module_name, module_filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module


def method_paginate(client_object, method_name, method_arguments=None, max_items=None):
    """
    Wrapper for the boto3 client pagination method. Returns the content of a
    fully paginated response with the response meta information removed.
    Args:
    client_object - boto3 client object used for pagination process
    method_name - name of the boto3 method that will be paginated. Must be a
                  method that allows pagination
    Kargs:
    method_arguments - Dictionary containing key/value pairs for the method
                       being paginated.
    max_items - Maximum number of items to return for each each pagination call

    Returns a python dictionary of the paginated response(s)
    """
    if not client_object.can_paginate(method_name):
        raise ValueError(f"Method {method_name} can be be paginated")

    if not max_items:
        max_items = 100

    if not method_arguments:
        method_arguments = {}

    method_arguments["PaginationConfig"] = {'MaxItems': max_items}
    paginator = client_object.get_paginator(method_name)

    return_dict = None
    for response in paginator.paginate(**method_arguments):
        del response["ResponseMetadata"]

        if return_dict:
            return_dict.update(response)
        else:
            return_dict = response

    return return_dict


def s_client_manager(function):
    def wrapper(self, *args, **kwargs):
        if not self.da_client_manager:
            self.da_client_manager = self.get_delegated_client_manager(self.SERVICE_PRINCIPAL)

        return function(self, *args, **kwargs)
    return wrapper