#!/usr/bin/env bash
set +x

# Assume role must exist in all target accounts. Role name is contained in
# ASSUME_ROLE_NAME environment variable.
# Assumes that the .aws/credentials file has been configured with a "default" profile.


add_profile() {
# Adds a new profile to the .aws/credentials file the account specified in the
# first parameter.

  TEMP_CREDS=$(aws sts assume-role --query 'Credentials' --role-arn "arn:aws:iam::$CURRENT_ACCOUNT_ID:role/$ASSUME_ROLE_NAME" --role-session-name $CURRENT_ACCOUNT_ID )
  TEMP_ACCESS_KEY=$(echo $TEMP_CREDS | jq '.AccessKeyId' | sed 's/\"//g')
  TEMP_SECRET_KEY=$(echo $TEMP_CREDS | jq '.SecretAccessKey'| sed 's/\"//g')
  TEMP_TOKEN=$(echo $TEMP_CREDS | jq '.SessionToken'| sed 's/\"//g')

  aws configure set aws_access_key_id $TEMP_ACCESS_KEY --profile $1
  aws configure set aws_secret_access_key  $TEMP_SECRET_KEY --profile $1
  aws configure set aws_session_token $TEMP_TOKEN --profile $1

}

# Determine the execution account ID.  This can be used to prevent remediations from being
# added to the centralized security account.
CRED_ACCOUNT=$(aws sts get-caller-identity --query 'Account' | sed 's/\"//g')
echo "Execution account: $CRED_ACCOUNT"

# Sanitize output for array conversion
MEMBER_ACCOUNTS=$(aws organizations list-accounts --output text --query 'Accounts[*].Id')
# Returned string delimits using tabs
IFS=$'\t' read -ra ACCOUNT_ARRAY <<< "$MEMBER_ACCOUNTS"
echo "Number of accounts: ${#ACCOUNT_ARRAY[@]}"
echo "Member accounts: "$MEMBER_ACCOUNTS

for account in "${ACCOUNT_ARRAY[@]}"
do
  if [ "$account" == "$CRED_ACCOUNT" ]
  then
    continue
  fi
  echo "Executing on account $account"
  #CURRENT_ACCOUNT_ID="$account"

  CURRENT_ACCOUNT_ID="086220966294"
  ASSUME_ROLE_NAME="ca_router_role"

  add_profile $CURRENT_ACCOUNT_ID
  export AWS_PROFILE="$CURRENT_ACCOUNT_ID"

  terraform workspace new $CURRENT_ACCOUNT_ID || terraform workspace select $CURRENT_ACCOUNT_ID
  terraform init
  terraform plan -out $CURRENT_ACCOUNT_ID.plan
  terraform apply -auto-approve $CURRENT_ACCOUNT_ID.plan


  exit








done




