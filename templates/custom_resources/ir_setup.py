"""
Entrypoint for setting up IR solution.  Can be run from a system with the
appropriate IAM credentials or as a custom resource in a Cloudformation stack.
"""
import logging


import common
import guardduty
import inspector
import securityhub


class IRManager:
    """
    Class that manages the calling of IR service modules for the creation,
    updating and deletion of the IR solution.
    """
    SERVICE_CLASS_MAPPING = {
        "securityhub": securityhub.Securityhub,
        "guardduty": guardduty.Guardduty,
        "inspector": inspector.Inspector
    }

    def __init__(self, target_account=None, assume_role_name=None, external_id=None):
        self.target_account = target_account
        self.assume_role_name = assume_role_name
        self.external_id = external_id

    def ir_create(self, config_dict):
        """
        Invokes the create methods for the services requested in the config_dict
        Args:
        config_dict - IR dictionary

        Returns None
        """
        self._ir_action("create", config_dict)

    def ir_update(self, config_dict):
        """
        Invokes the update methods for the services requested in the
        config_dict. NOTE: The created method for IR services will be the same
        method used for creation.
        Args:
        config_dict - IR dictionary

        Returns None
        """
        self._ir_action("update", config_dict)

    def ir_destroy(self, config_dict):
        """
        Invokes the destroy methods for the services requested in the config_dict
        Note: Most services will destroy by removing the delegated admin from
        the organization which returns service control to local account.
        Args:
        config_dict - IR dictionary

        Returns None
        """
        self._ir_action("destroy", config_dict)

    def _ir_action(self, action, config_dict):
        """
        Generalized function used to perform create, update and destroy actions
        for IR services.
        Args:
        action - Type of action to take
        config_dict - IR configuration dictionary

        Returns None
        """
        for service in config_dict:

            logging.debug(config_dict[service])

            if service not in self.SERVICE_CLASS_MAPPING:
                continue

            service_object = self.SERVICE_CLASS_MAPPING[service](
                target_account=self.target_account,
                assume_role_name=self.assume_role_name,
                external_id=self.external_id)

            if action == "create":
                method = service_object.create
            elif action == "update":
                method = service_object.update
            else:
                method = service_object.destroy

            method(config_dict[service])

    def list_info(self):
        for service in self.SERVICE_CLASS_MAPPING:
            class_instance = self.SERVICE_CLASS_MAPPING[service]()
            class_instance.echo_info()


def lambda_handler(event, context):
    """
    Function used as a handler for when this module is called as a custom
    resource AWS lambda function.  Handles the invoking of the custom
    resource lambda and the responding to Cloudformation on success or failure
    of the custom resource.

    Args:
    event - AWS Cloudwatch event
    context - AWS contect object

    Returns None
    """
    print(event)

    import cfnresponse

    # CR considered failed if any part of the try block fails
    cfn_status = cfnresponse.FAILED
    cfn_response_data = {}

    try:
        common.setup_logging()

        config_dict = _process_lambda_event(event)

        irm_object = IRManager(target_account=config_dict["target_account"],
                               assume_role_name=config_dict["assume_role"],
                               external_id=config_dict["external_id"])

        if event["RequestType"] in  ["Create", "Update"]:
            irm_object.ir_create(config_dict)

        elif event["RequestType"] == "Delete":
            irm_object.ir_destroy(config_dict)

        cfn_status = cfnresponse.SUCCESS

    finally:
        cfnresponse.send(event, context, cfn_status, cfn_response_data)


def _process_lambda_event(event):
    """
    Parse a custom resource event's ResourceProperties and build a ir config
    dictionary using the values.
    Args:
    event - AWS lambda event dictionary

    Returns a dictionary containing the parsed values needed for the custom
        resource CF event.
    """

    core_parameters = [
        "target_account",
        "assume_role",
        "external_id",
    ]
    return_dict =  dict(zip(core_parameters, [None]*len(core_parameters)))

    skip_list = [
        "ServiceToken"
    ]
    service_param_type = {
        "sh__": "securityhub",
        "gd__": "guardduty",
        "in__": "inspector"
    }

    for parameter in event["ResourceProperties"]:
        if parameter in skip_list:
            continue

        if parameter in core_parameters:
            return_dict[parameter] = event["ResourceProperties"][parameter]
            continue


        for ptype, ptype_value in service_param_type.items():
            if parameter.startswith(ptype):
                if ptype_value not in return_dict:
                    return_dict[ptype_value] = {}

                param_name = parameter.replace(ptype, "", 1)
                param_value = event["ResourceProperties"][parameter]

                return_dict[ptype_value][param_name] = param_value
                break

    return return_dict



if __name__ == "__main__":
    arg_dict = {
        "--config" : {"help": "IR config json file",
                      "required": True},
        "--target": {"help": "AWS account ID of organization master"},
        "--role": {"help": "AWS IAM role to assume in organization master"},
        "--exid": {"help": "External ID for organization master role"},
        "--create": {"help": "Enable or update IR services.",
                     "action": "store_true"},
        "--destroy": {"help": "Remove the services defined in the config file",
                      "action": "store_true"},
        "--debug": {"help": "Set logging level to debug",
                    "action": "store_true"}
    }

    args = common.parse_args(arg_dict)

    if args.debug:
        LOG_LEVEL=logging.DEBUG
    else:
        LOG_LEVEL=logging.INFO

    common.setup_logging(log_level=LOG_LEVEL)

    config_content = common.load_json(args.config)
    ir_object = IRManager(target_account=args.target,
                          assume_role_name=args.role,
                          external_id=args.exid)

    if True not in [args.create, args.destroy]:
        logging.error("No action requested. Must request to create or destroy")

    if args.create:
        ir_object.ir_create(config_content)

    elif args.destroy:
        ir_object.ir_destroy(config_content)
