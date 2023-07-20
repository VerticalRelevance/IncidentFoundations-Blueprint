"""
Implements the class Inspector which is used by ir_setup to enable and configure
AWS Inspector 2 for an AWS Organization through the organizations service.
"""
import logging

import botocore.exceptions
from org_accounts import manager


class Inspector(manager.OrgManager):
    AWS_SERVICE = "inspector2"
    SERVICE_PRINCIPAL = "inspector2.amazonaws.com"

    def __init__(self, target_account=None, assume_role_name=None, external_id=None, region=None):
        super().__init__(target_account=target_account,
                         assume_role_name=assume_role_name,
                         external_id=external_id,
                         region=region)

        self.da_client_manager = None

    def create(self, input_dict):
        """
        Common coordination method that enables Inspector for the organization.
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

        logging.info(f"Enabling {self.SERVICE_PRINCIPAL} in regions {input_dict['enable_regions']}")
        for region in input_dict["enable_regions"]:
            self.enable_org_admin(input_dict["admin_account_id"], region)

        org_accounts = self.get_org_accounts()

        # Configuring autojoin per region and adding existing member accounts
        for region in input_dict["enable_regions"]:

            add_account_list = []
            in_members = [ account["accountId"] for account in self.get_associated_members(region=region)]
            for account in {account:org_accounts[account]["Email"] for account in org_accounts}:
                if account not in in_members and account != input_dict["admin_account_id"]:
                    logging.info(f"Adding account {account} as a {self.AWS_SERVICE} member in {region}")
                    add_account_list.append(account)

            if add_account_list:
                for account in add_account_list:
                    self.add_member(account, region=region)

            self.enable_scans(in_members, region=region)

            logging.info(f"Enabling autojoin for {self.AWS_SERVICE} in region {region}")
            self.update_org_config(region=region)

    def update(self, input_dict):
        """
        Common coordination method that updates the configuration of Inspector
        for an organization.  The create method is implemented to to perform
        the create and update workflows.
        Args:
        input_dict - IR dictionary

        Returns None
        """
        self.create(input_dict)

    def destroy(self, input_dict):
        """
        Common coordination method that disables the Inspector delegated admin
        account from being able to manage the organizations Inspector Service.
        This returns the control of Inspector back to each account and does
        NOT disable or remove any findings from organization member accounts.
        Args:
        input_dict - IR dictionary

        Returns None
        """
        for region in input_dict["enable_regions"]:
            self.disable_org_admin(input_dict["admin_account_id"], region)

        account_services = self.list_services_for_account(input_dict["admin_account_id"])

        if not account_services:
            logging.info(f"No delegated admin account for service {self.AWS_SERVICE}")

        elif self.SERVICE_PRINCIPAL in account_services:
            logging.info(f"Unregistering delegated admin account {input_dict['admin_account_id']} for service {self.AWS_SERVICE}")
            self.deregister_delegated_admin(input_dict["admin_account_id"])
            logging.info(f"Account {input_dict['admin_account_id']} unregistered for service {self.AWS_SERVICE}")

        else:
            logging.warning("Service principal %s was not found enabled for the org", self.SERVICE_PRINCIPAL)

    def get_delegated_admin(self):
        """
        Returns information about the delegated administrator account which
        manages the Inspector service for the organization.
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
        organizations delegated administrator for the Inspector service. The
        method used is from the base manager class.
        Args:
        account_id - AWS account ID string

        Returns None
        """
        super().set_delegated_admin(account_id, self.SERVICE_PRINCIPAL)

    @manager.s_client_manager
    def deregister_delegated_admin(self, account_id):
        """
        Removes the account provided through the account_id parameter as the
        delegated administrator for the organization.
        Args:
        account_id - AWS account ID string

        Returns None
        """
        return super().deregister_delegated_admin(account_id, self.SERVICE_PRINCIPAL)

    @manager.s_client_manager
    def enable_org_admin(self, account_id, region):
        """
        Enables the account provided in the account_id parameter as the
        service administrator for the Inspector service in
        the organization for the region provided in the region parameter.
        Args:
        account_id - AWS account ID string
        region - AWS region string

        Returns None
        """
        region = region.strip()
        try:
            self.client_manager.client(self.AWS_SERVICE, region).enable_delegated_admin_account(
                delegatedAdminAccountId=account_id)

        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "ConflictException"and "already enabled for the organization" in err.response["Error"]["Message"]:
                logging.warning(f"{self.AWS_SERVICE} service admin already setup for region {region}")
            else:
                raise err from None

    def disable_org_admin(self, account_id, region):
        """
        Disables the account provided in the account_id parameter as the
        service administrator for the Inspector service in
        the organization for the region provided in the region parameter.
        Args:
        account_id - AWS account ID string
        region - AWS region string

        Returns None
        """
        region = region.strip()
        try:
            self.client_manager.client(self.AWS_SERVICE, region).disable_delegated_admin_account(
                delegatedAdminAccountId=account_id)

        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException"and "not the delegated administrator" in err.response["Error"]["Message"]:
                logging.warning(f"{self.AWS_SERVICE} service not setup as admin for region {region}")
            else:
                raise err from None

    def update_org_config(self, region):
        """
        Set autoenable for new organization accounts.
        Args:
        region - aws region string

        Returns None
        """
        self.da_client_manager.client("inspector2", region).update_organization_configuration(
            autoEnable={
                'ec2': True,
                'ecr': True,
                'lambda': True
            }
        )

    def add_member(self, account_id, region):
        """
        Adds a member account as "managed by" for Inspector for the region
        indicated by the region parameter.
        Args:
        account_id - aws account ID string
        region - aws region string

        Returns None
        """
        self.da_client_manager.client("inspector2", region).associate_member(
            accountId=account_id
        )

    def enable_scans(self, add_account_list, region):
        """
        Enables the default stan types for the accounts provided by the
        add_account_list in the region indicated by the region parameter.
        Args:
        add_account_list - list of aws account id strings
        region - aws region string

        Returns None
        """
        response = self.da_client_manager.client("inspector2", region).enable(
            accountIds=add_account_list,
            resourceTypes=['EC2','ECR','LAMBDA','LAMBDA_CODE']
        )

        if response["failedAccounts"]:
            failure_results = []
            for failure in response["failedAccounts"]:
                if failure["errorCode"] != "ALREADY_ENABLED":
                    failure_results.append(failure)

            if failure_results:
                raise ValueError("Unable to enable in all accounts %s" % str(failure_results))

    @manager.s_client_manager
    def get_associated_members(self, region):
        """
        Returns the organization member accounts that are associated with
        Inspactor for the region provided by the region parameter.
        Args:
        region - aws region string

        Returns list of dictionaries contaiing member information.
        """
        response = self.da_client_manager.client("inspector2", region).list_members(onlyAssociated=True)
        return response["members"]