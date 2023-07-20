"""
Implements the class Securityhub which is used by ir_setup to enable and configure
AWS Security Hub for an AWS Organization through the organizations service.
"""
import logging

import botocore.exceptions
from org_accounts import manager


class Securityhub(manager.OrgManager):
    AWS_SERVICE = "securityhub"
    SERVICE_PRINCIPAL = "securityhub.amazonaws.com"

    def __init__(self, target_account=None, assume_role_name=None, external_id=None, region=None):
        super().__init__(target_account=target_account,
                         assume_role_name=assume_role_name,
                         external_id=external_id,
                         region=region)

        self.da_client_manager = None
        self.aggregation_arn = None

    def create(self, input_dict):
        """
        Common coordination method that enables Security Hub for the organization.
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
            self.set_delegated_admin(input_dict['admin_account_id'])

        elif input_dict['admin_account_id'] != del_admin_info["Id"]:
            raise ValueError(f"Delegated admin account for service {self.AWS_SERVICE} does not match requested target {input_dict['admin_account_id']}")

        else:
            logging.info(f"Account {input_dict['admin_account_id']} is already set to delegated admin for service {self.AWS_SERVICE}")

        # Enable SH in management account if flag is true.  Management account is not automatically
        # enabled for SH through DA
        if "enable_for_management" in input_dict and input_dict["enable_for_management"]:
            logging.info(f"Enabling Security Hub in manager account")
            self.enable_for_management_account(region=input_dict["aggregate_region"])

        # Enable the delegated admin account as the admin for SH service in the desired regions
        logging.info(f"Enabling {self.SERVICE_PRINCIPAL} in regions {input_dict['enable_regions']}")
        for region in input_dict["enable_regions"]:
            # Strip whitespace on region to prevent incorrectly formed ","
            # separated lists from introducing valid region strings
            region = region.strip()
            try:
                self.enable_org_admin(input_dict['admin_account_id'], region)

            except botocore.exceptions.ClientError as err:
                if err.response['Error']['Code'] == "ResourceConflictException":
                    logging.warning(f"{self.AWS_SERVICE} service admin already setup for region {region}")
                else:
                    raise err from None

        region_disable = self.enabled_regions.copy()
        [region_disable.remove(region) for region in input_dict["enable_regions"]]
        logging.info(f"Ensuring {self.SERVICE_PRINCIPAL} is disabled in regions {region_disable}")
        for region in region_disable:
            self.disable_org_admin(account_id=input_dict["admin_account_id"], region=region)


        self.da_client_manager = self.get_delegated_client_manager(self.SERVICE_PRINCIPAL)
        org_accounts = self.get_org_accounts()

        # Configure Service Aggregation
        self.get_aggregator_arn(region=input_dict["aggregate_region"])
        if not self.aggregation_arn:
            self.enable_aggregation(region=input_dict["aggregate_region"])
        else:
            self.update_aggregation(region=input_dict["aggregate_region"])

        # Autojoin needs to be set per region where security hub is enabled
        for region in input_dict["enable_regions"]:
            logging.info(f"Enabling default standards and autojoin for security hub in region {region}")
            response = self.da_client_manager.client("securityhub", region).update_organization_configuration(
                AutoEnable=True,
                AutoEnableStandards='DEFAULT'
            )

            add_account_list = []
            sh_members = [ account["AccountId"] for account in self.get_associated_members(region=region)]
            for account, account_email in {account:org_accounts[account]["Email"] for account in org_accounts}.items():
                if account not in sh_members and account != input_dict['admin_account_id']:
                    logging.info(f"Adding account {account} as a SH member")
                    add_account_list.append({'AccountId': account, 'Email': account_email})

            if add_account_list:
                self.add_members(add_account_list, region=region)

    def update(self, input_dict):
        """
        Common coordination method that updates the configuration of Security Hub
        for an organization.  The create method is implemented to to perform
        the create and update workflows.
        Args:
        input_dict - IR dictionary

        Returns None
        """
        self.create(input_dict)

    def destroy(self, input_dict):
        """
        Common coordination method that disables the Security Hub delegated admin
        account from being able to manage the organizations Security Hub Service.
        This returns the control of Security Hub back to each account and does
        NOT disable or remove any findings from organization member accounts.
        Args:
        input_dict - IR dictionary

        Returns None
        """
        account_services = self.list_services_for_account(input_dict['admin_account_id'])

        if not account_services:
            logging.info(f"No delegated admin account for service {self.AWS_SERVICE}")

        elif self.SERVICE_PRINCIPAL in account_services:
            logging.info(f"Unregistering delegated admin account {input_dict['admin_account_id']} for service {self.AWS_SERVICE}")
            self.deregister_delegated_admin(input_dict['admin_account_id'])
            logging.info(f"Account {input_dict['admin_account_id']} unregistered for service {self.AWS_SERVICE}")

    def get_delegated_admin(self):
        """
        Returns information about the delegated administrator account which
        manages the Security Hub service for the organization.
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
        organizations delegated administrator for the Security Hub service. The
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
        service administrator for the Security Hub service in
        the organization for the region provided in the region parameter.
        Args:
        account_id - AWS account ID string
        region - AWS region string

        Returns None
        """
        return super().enable_org_admin(account_id, self.AWS_SERVICE, region)

    def disable_org_admin(self, account_id, region):
        """
        Disables the account provided in the account_id parameter as the
        service administrator for the Security Hub service in
        the organization for the region provided in the region parameter.
        Args:
        account_id - AWS account ID string
        region - AWS region string

        Returns None
        """

        try:
            super().disable_org_admin(account_id, self.AWS_SERVICE, region)

        except botocore.exceptions.ClientError as err:
            if err.response['Error']['Code'] == "ResourceNotFoundException" and "Admin account was not found for this organization" in err.response['Error']["Message"]:
                logging.warning(f"{self.AWS_SERVICE} service admin not enabled for region {region}")
            else:
                raise err from None

    @manager.s_client_manager
    def get_aggregator_arn(self, region):
        """
        Returns the ARN for the security hub aggregator for the region provided
        in the region parameter.
        Args:
        region - aws region string

        Returns arn if aggregator found, None if no aggregator is found.
        """
        response = self.da_client_manager.client("securityhub", region).list_finding_aggregators()

        if response["FindingAggregators"]:
            self.aggregation_arn = response["FindingAggregators"][0]["FindingAggregatorArn"]
            return self.aggregation_arn

    @manager.s_client_manager
    def enable_aggregation(self, region):
        """
        Sets the region specified by the region parameter as the aggregation
        region for Security Hub.
        Args:
        region - aws region string

        Returns the arn of the new aggregator as a string.
        """
        response = self.da_client_manager.client("securityhub", region).create_finding_aggregator(RegionLinkingMode='ALL_REGIONS')
        self.aggregation_arn = response["FindingAggregatorArn"]

        return self.aggregation_arn

    @manager.s_client_manager
    def update_aggregation(self, region):
        """
        Updates the region used as the aggregation region for Security Hub to
        the value provided by the region parameter.
        Args:
        region - aws region string

        Returns None
        """
        if not self.aggregation_arn:
            self.get_aggregator_arn(region)

        self.da_client_manager.client("securityhub", region).update_finding_aggregator(
            FindingAggregatorArn=self.aggregation_arn,
            RegionLinkingMode="ALL_REGIONS")

    @manager.s_client_manager
    def delete_aggregation(self, region):
        """
        Disables finding aggregation.
        Args:
        region - aws region string

        Returns None
        """
        if not self.aggregation_arn:
            self.get_aggregator_arn(region)

        if not self.aggregation_arn:
            raise ValueError(f"Unable to get service aggregation arn for region {region}")
        self.da_client_manager.client("securityhub", region).delete_finding_aggregator(
            FindingAggregatorArn=self.aggregation_arn)

    @manager.s_client_manager
    def add_members(self, member_list, region):
        """
        Adds AWS accounts as members to the Security Hub Region.  The parameter member_list
        is a list of dictionaries where each dictionary contains keys AccountId and Email.  The
        case of these keys is intentional and matches those returned from the list_members
        method return.
        Args:
        member_list -

        Returns None
        """
        response = self.da_client_manager.client("securityhub", region).create_members(
            AccountDetails=member_list)

        if response["UnprocessedAccounts"] != []:
            raise ValueError(f"Unable to add all accounts as members {response['UnprocessedAccounts']}")

    @manager.s_client_manager
    def get_associated_members(self, region):
        """
        Returns the organization member accounts that are associated with
        security hub for the region provided by the region parameter.
        Args:
        region - aws region string

        Returns list of dictionaries contaiing member information.
        """
        response = self.da_client_manager.client("securityhub", region).list_members(OnlyAssociated=True)
        return response["Members"]

    @manager.s_client_manager
    def enable_for_management_account(self, region):
        """
        Enables the security hub service for the region provided by the region
        parameter.
        Args:
        region - aws region string

        Returns None
        """
        try:
            self.client_manager.client("securityhub", region).enable_security_hub(EnableDefaultStandards=True)

        except botocore.exceptions.ClientError as err:
            if err.response['Error']['Code'] == "ResourceConflictException" and "Account is already subscribed" in err.response['Error']["Message"]:
                logging.warning(f"{self.AWS_SERVICE} service admin already setup for region {region}")
            else:
                raise err from None
