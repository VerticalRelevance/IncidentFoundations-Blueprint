"""
Implements the class Guardduty which is used by ir_setup to enable and configure
AWS GuardDuty for an AWS Organization through the organizations service.
"""
import logging

import botocore.exceptions
from org_accounts import manager


class Guardduty(manager.OrgManager):
    AWS_SERVICE = "guardduty"
    SERVICE_PRINCIPAL = "guardduty.amazonaws.com"
    GD_DATA_SOURCE_ENABLE = {
        "s3": {
            "name": "S3Logs",
            "content": {"AutoEnable": True}
        },
        "eks": {
            "name": "Kubernetes",
            "content": {"AuditLogs": {"AutoEnable": True}}
        },
        "malware": {
            "name": "MalwareProtection",
            "content": {
                "ScanEc2InstanceWithFindings": {
                    "EbsVolumes": {"AutoEnable": True}
                }
            }
        }
    }

    def __init__(self, target_account=None, assume_role_name=None, external_id=None, region=None):
        super().__init__(target_account=target_account,
                         assume_role_name=assume_role_name,
                         external_id=external_id,
                         region=region)

        self.da_client_manager = None
        self.aggregation_arn = None

    def create(self, input_dict):
        """
        Common coordination method that enables GuardDuty for the organization.
        Args:
        input_dict - IR dictionary

        Returns None
        """
        logging.info("#"*80)
        logging.info(f"Configuring for service {self.AWS_SERVICE} (Principal: {self.SERVICE_PRINCIPAL})")

        # Assign the provided account as the delegated admin for SH for this organization
        del_admin_info = self.get_delegated_admin()
        if not del_admin_info:
            logging.info(f"Setting account {input_dict['admin_account_id']} as delegated admin for service {self.AWS_SERVICE}")
            self.set_delegated_admin(input_dict["admin_account_id"])

        elif input_dict["admin_account_id"] != del_admin_info["Id"]:
            raise ValueError(f"Delegated admin account for service {self.AWS_SERVICE} does not match requested target {input_dict['admin_account_id']}")

        else:
            logging.info(f"Account {input_dict['admin_account_id']} is already set to delegated admin for service {self.AWS_SERVICE}")

        # Enable the delegated admin account as the admin for SH service in the desired regions
        logging.info(f"Enabling {self.SERVICE_PRINCIPAL} in regions {input_dict['enable_regions']}")
        for region in input_dict["enable_regions"]:
            # Strip whitespace on region to prevent incorrectly formed ","
            # separated lists from introducing valid region strings
            region = region.strip()
            try:
                self.enable_org_admin(input_dict["admin_account_id"], region)

            except botocore.exceptions.ClientError as err:
                if err.response["Error"]["Code"] == "ResourceConflictException":
                    logging.warning(f"{self.AWS_SERVICE} service admin already setup for region {region}")
                else:
                    raise err from None

        region_disable = self.enabled_regions.copy()
        [region_disable.remove(region) for region in input_dict["enable_regions"]]
        logging.info(f"Ensuring {self.SERVICE_PRINCIPAL} is disabled in regions {region_disable}")
        for region in region_disable:
            self.disable_org_admin(account_id=input_dict["admin_account_id"], region=region)

        org_accounts = self.get_org_accounts()

        # Autojoin needs to be set per region
        for region in input_dict["enable_regions"]:
            logging.info(f"Enabling autojoin for {self.AWS_SERVICE} in region {region}")
            param_dict = {"region": region}
            self.update_org_config(**param_dict)

            add_account_list = []
            gd_members = [ account["AccountId"] for account in self.get_associated_members(region=region)]
            for account, account_email in {account:org_accounts[account]["Email"] for account in org_accounts}.items():
                if account not in gd_members and account != input_dict["admin_account_id"]:
                    logging.info(f"Adding account {account} as a SH member")
                    add_account_list.append({"AccountId": account, "Email": account_email})

            if add_account_list:
                self.add_members(add_account_list, region=region)

    def update(self, input_dict):
        """
        Common coordination method that updates the configuration of GuardDuty
        for an organization.  The create method is implemented to to perform
        the create and update workflows.
        Args:
        input_dict - IR dictionary

        Returns None
        """
        self.create(input_dict)

    def destroy(self, input_dict):
        """
        Common coordination method that disables the GuardDuty delegated admin
        account from being able to manage the organizations GuardDuty Service.
        This returns the control of GuardDuty back to each account and does
        NOT disable or remove any findings from organization member accounts.
        Args:
        input_dict - IR dictionary

        Returns None
        """
        account_services = self.list_services_for_account(input_dict["admin_account_id"])

        if not account_services:
            logging.info(f"No delegated admin account for service {self.AWS_SERVICE}")

        elif self.SERVICE_PRINCIPAL in account_services:
            logging.info(f"Unregistering delegated admin account {input_dict['admin_account_id']} for service {self.AWS_SERVICE}")
            self.deregister_delegated_admin(input_dict["admin_account_id"])
            logging.info(f"Account {input_dict['admin_account_id']} unregistered for service {self.AWS_SERVICE}")


    def get_delegated_admin(self):
        """
        Returns information about the delegated administrator account which
        manages the GuardDuty service for the organization.
        Args:
        None

        Returns dictionary
        """
        del_admin_info = self.get_delegated_admins(service_principal=self.SERVICE_PRINCIPAL)
        if not del_admin_info:
            return None

        elif len(del_admin_info) > 1:
            raise ValueError(f"Unexpected number of delegated admins for service {self.SERVICE_PRINCIPAL} ({len(del_admin_info)})")

        return del_admin_info[0]

    def set_delegated_admin(self, account_id):
        """
        Configures the AWS account indicated in the account_id parameter as the
        organizations delegated administrator for the GuardDuty service. The
        method used is from the base manager class.
        Args:
        account_id - AWS account ID string

        Returns None
        """
        return super().set_delegated_admin(account_id, self.SERVICE_PRINCIPAL)

    def deregister_delegated_admin(self, account_id):
        """
        Removes the account provided through the account_id parameter as the
        delegated administrator for the organization.
        Args:
        account_id - AWS account ID string

        Returns None
        """
        return super().deregister_delegated_admin(account_id, self.SERVICE_PRINCIPAL)

    def enable_org_admin(self, account_id, region):
        """
        Enables the account provided in the account_id parameter as the
        service administrator for the GuardDuty service in
        the organization for the region provided in the region parameter.
        Args:
        account_id - AWS account ID string
        region - AWS region string

        Returns None
        """
        try:
            return super().enable_org_admin(account_id, self.AWS_SERVICE, region)

        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "BadRequestException" and "already enabled as the GuardDuty delegated administrator" in err.response["Error"]["Message"]:
                logging.warning(f"{self.AWS_SERVICE} service del admin already setup for region {region}")
            else:
                raise err from None

    def disable_org_admin(self, account_id, region):
        """
        Disables the account provided in the account_id parameter as the
        service administrator for the GuardDuty service in
        the organization for the region provided in the region parameter.
        Args:
        account_id - AWS account ID string
        region - AWS region string

        Returns None
        """
        try:
            super().disable_org_admin(account_id, self.AWS_SERVICE, region)

        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "BadRequestException" and "delegated administrator account has already been disabled" in err.response["Error"]["Message"]:
                logging.warning(f"{self.AWS_SERVICE} service admin not enabled for region {region}")
            else:
                raise err from None

    @manager.s_client_manager
    def get_detector_id(self, region):
        """
        Returns the detector id for the detector used in the region indicated by
        the region parameter.
        Args:
        region - aws region string

        Returns detector id string
        """

        response = self.da_client_manager.client("guardduty", region).list_detectors()

        if len(response["DetectorIds"]) != 1:
            raise ValueError(f"Unexpected number of detectors for region {region} *{len(response['DetectorIds'])}")

        return response["DetectorIds"][0]

    @manager.s_client_manager
    def update_org_config(self, region):
        """
        Update the configuration of GuardDuty for the organization enabling
        autojoin for new member accounts.
        Args:
        region - aws region string

        Returns None
        """
        param_dict = {
            "DetectorId": self.get_detector_id(region),
            "AutoEnable": True
        }

        self.da_client_manager.client("guardduty", region).update_organization_configuration(
            **param_dict)

    @manager.s_client_manager
    def add_members(self, member_list, region):
        """
        Adds AWS accounts as members to the Region.  The parameter member_list
        is a list of dictionaries where each dictionary contains keys AccountId and Email.  The
        case of these keys is intentional and matches those returned from the list_members
        method return.
        Args:
        member_list -

        Returns None
        """
        detector_id = self.get_detector_id(region)
        response = self.da_client_manager.client("guardduty", region).create_members(
            DetectorId=detector_id,
            AccountDetails=member_list)

        if response["UnprocessedAccounts"] != []:
            raise ValueError(f"Unable to add all accounts as members {response['UnprocessedAccounts']}")

    @manager.s_client_manager
    def get_associated_members(self, region):
        """
        Returns the organization member accounts that are associated with
        GuardDuty for the region provided by the region parameter.
        Args:
        region - aws region string

        Returns list of dictionaries contaiing member information.
        """
        detector_id = self.get_detector_id(region)
        response = self.da_client_manager.client("guardduty", region).list_members(DetectorId=detector_id,
                                                                                   OnlyAssociated="True")
        return response["Members"]

    @manager.s_client_manager
    def update_members(self, account_list, region):
        """
        Update member accounts to use the detector for the delegated admin.
        Args:
        account_list - list of aws account id strings
        region - aws region string

        Returns None
        """
        detector_id = self.get_detector_id(region)

        param_dict = {
            "DetectorId": detector_id,
            "AccountIds": account_list
        }

        logging.info(f"Updating member account GD features")
        self.da_client_manager.client("guardduty", region).update_member_detectors(**param_dict)