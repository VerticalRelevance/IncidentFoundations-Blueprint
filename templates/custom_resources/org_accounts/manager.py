"""
Module containing the base class for IR services. Base class contains common
functionality used by all services.
"""
import logging

import botocore.exceptions
import common


def s_client_manager(function):
    def wrapper(self, *args, **kwargs):
        if not self.da_client_manager:
            self.da_client_manager = self.get_delegated_client_manager(self.SERVICE_PRINCIPAL)

        return function(self, *args, **kwargs)
    return wrapper


class OrgManager:
    """
    Base class to use with IR service classes. Contains base functionality for
    managing AWS services through AWS organizations.

    NOTE: Assumes credentials with Organizations permissions are configured in
    the environment where the class is run or the environment configured class
    is able to assume a role with the required Organizations permissions.
    """
    DEFAULT_REGION = "us-east-1"
    ORG_ACCESS_ROLE_NAME = "OrganizationAccountAccessRole"
    AWS_SERVICE = None
    SERVICE_PRINCIPAL = None

    def __init__(self, target_account=None, assume_role_name=None,
                 external_id=None, region=None):
        self.target_account = target_account
        self.assume_role_name = assume_role_name
        self.external_id = external_id
        self.region = region
        if not self.region:
            self.region = self.DEFAULT_REGION

        self.access_key = None
        self.secret_key = None
        self.token = None

        self.sts_client = common.get_client("sts", region=self.region)
        if self.target_account:
            self.access_key, self.secret_key, self.token = common.assume_role(self.sts_client,
                               target_account=self.target_account,
                               assume_role_name=self.assume_role_name,
                               external_id=self.external_id)

        self.client_manager = common.ClientManager(access_key=self.access_key,
                                                   secret_key=self.secret_key,
                                                   token=self.token)

        self.org_client = self.client_manager.client("organizations")

        self.enabled_regions = self.get_enabled_regions()


    def get_delegated_admins(self, service_principal=None):
        """
        Return a list containing information about the delegated admin accounts
        for an organization.
        Args:
        service_principal - AWS service principal to use as a filter

        Returns list of del admin accounts.
        """
        param_dict = {}
        if service_principal:
            param_dict["ServicePrincipal"] = service_principal

        paginator = self.org_client.get_paginator("list_delegated_administrators")

        return_list = []
        for response in paginator.paginate(**param_dict):
            return_list.extend(response["DelegatedAdministrators"])

        return return_list



    def list_services_for_account(self, account_id):
        """
        Returns a list of service principals for which the account indicated serves
        as the delgated admin.

        Args:
        account_id - AWS account id

        Returns a list of service principals
        """
        return_list = []
        try:
            paginator = self.org_client.get_paginator("list_delegated_services_for_account")
            for response in paginator.paginate(AccountId=account_id):
                return_list.extend(response["DelegatedServices"])

            return_list = [service["ServicePrincipal"] for service in return_list]

        except botocore.exceptions.ClientError as err:
            if err.response['Error']['Code'] == "AccountNotRegisteredException":
                logging.warning("Account %s is not a registered delegated administrator",
                                account_id)
            else:
                raise err from None

        return return_list

    def set_delegated_admin(self, account_id, service_principal):
        """
        Set the account indicated in the account_id parameter as the delegated admin for
        the organization for the service indicated by the service_name parameter.
        account_id - AWS account id
        service_principal - AWS service to register as del admin

        Returns None
        """
        self.org_client.enable_aws_service_access(ServicePrincipal=service_principal)

        enabled_services = self.list_service_access()
        if self.SERVICE_PRINCIPAL not in enabled_services:
            raise ValueError("Service %s does not have access enabled for the organization" % self.SERVICE_PRINCIPAL)

        self.org_client.register_delegated_administrator(
            AccountId=account_id,
            ServicePrincipal=service_principal
        )

    def deregister_delegated_admin(self, account_id, service_principal):
        """
        Deregisters a member account as the delegated admin for an organization.
        Args:
        account_id - AWS account id
        service_principal - AWS service to deregister del admin

        Returns None
        """
        self.org_client.deregister_delegated_administrator(
            AccountId=account_id,
            ServicePrincipal=service_principal
        )

    def enable_org_admin(self, account_id, service_name, region):
        """
        Enables the account as the service admin for the region specified.
        account_id - AWS account to enable as admin
        service_name - AWS service to enable as admin
        region - AWS region

        Returns None
        """
        logging.info("Enabling account %s as org admin for %s in %s",
                     account_id, service_name, region)
        self.client_manager.client(service_name, region).enable_organization_admin_account(
            AdminAccountId=account_id)

    def disable_org_admin(self, account_id, service_name, region):
        """
        Disables the account as the service admin for the region specified.
        Args:
        account_id - AWS account to disable as admin
        service_name - AWS service to disable admin
        region - AWS region

        Returns None
        """
        logging.info("Disabling %s as org admin for %s in %s",
                     account_id, service_name, region)
        self.client_manager.client(service_name, region).disable_organization_admin_account(
            AdminAccountId=account_id)

    def get_delegated_client_manager(self, service_principal):
        """
        Discovers the account that is the delegated admin for the service
        principal indicated in the service_principal argument. Returns a boto3
        client for the discovered delegated admin account.
        Args:
        service_principal - AWS service principal

        Returns a boto3 client for the delecated admin for the service indiated.
        """
        del_admin_info = self.get_delegated_admins(service_principal=service_principal)
        if not del_admin_info:
            raise ValueError("Unable to determine delegated admin account for service %s" %
                             service_principal)

        if len(del_admin_info) > 1:
            raise ValueError("Unexpected number of delegated admins for service %s (%s)" %
                             service_principal, str(len(del_admin_info)))

        del_admin_account_id = del_admin_info[0]["Id"]

        client_access_key, client_secret_key, client_token = common.assume_role(self.sts_client,
                               target_account=del_admin_account_id,
                               assume_role_name=self.ORG_ACCESS_ROLE_NAME)

        return common.ClientManager(access_key=client_access_key,
                                    secret_key=client_secret_key,
                                    token=client_token)

    def get_org_accounts(self):
        """
        Returns a dictionary containing information about the organizations
        member accounts.
        """
        response = self.org_client.list_accounts()
        return_dict = {}
        for account in response["Accounts"]:
            return_dict[account["Id"]] = account

        return return_dict

    def get_enabled_regions(self):
        """
        Returns a list of region names that are in states enabled, enabling or enabled by
        default.

        Returns a list of AWS regions
        """
        response = self.client_manager.client("account").list_regions(
            RegionOptStatusContains=['ENABLED','ENABLING', 'ENABLED_BY_DEFAULT']
        )

        return_list = []
        for region in response["Regions"]:
            return_list.append(region["RegionName"])

        return return_list

    def list_service_access(self):
        pag_response = common.method_paginate(
            self.org_client,
            "list_aws_service_access_for_organization")

        return [service["ServicePrincipal"] for service in pag_response["EnabledServicePrincipals"]]

    def enable_service_access(self, service_principal):
        """
        Enables a service's access through organizations.  This is here for
        development purposes only.  It is highly recommended by AWS that the
        enabling of service access for organizations take place through the
        console of the service itself.

        Args:
        service-principal - service principal to disable for the organization

        Returns None
        """
        response = self.org_client.enable_aws_service_access(
            ServicePrincipal=service_principal
        )

    def disable_service_access(self, service_principal):
        """
        Disables a service's access through organizations.  This is here for
        development purposes only.  It is highly recommended by AWS that the
        disabling of service access for organizations take place through the
        console of the service itself.

        Args:
        service-principal - service principal to disable for the organization

        Returns None
        """
        response = self.org_client.disable_aws_service_access(
            ServicePrincipal=service_principal
        )

    def echo_info(self):
        # List delegated admin accounts
        # List enabled service access
        # List management account info
        # List member account info


        pass