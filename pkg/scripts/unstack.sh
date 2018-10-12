#!/usr/bin/env bash
# Copyright BigchainDB GmbH and BigchainDB contributors
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


set -o nounset

# Make sure umask is sane
umask 022

# defaults
stack_branch=${STACK_BRANCH:="rbac"}
stack_repo=${STACK_REPO:="timathom/bigchaindb"}
stack_size=${STACK_SIZE:=4}
stack_type=${STACK_TYPE:="local"}
stack_type_provider=${STACK_TYPE_PROVIDER:=""}
tm_version=${TM_VERSION:="0.22.8"}
mongo_version=${MONGO_VERSION:="3.6"}
stack_vm_memory=${STACK_VM_MEMORY:=2048}
stack_vm_cpus=${STACK_VM_CPUS:=2}
stack_box_name=${STACK_BOX_NAME:="ubuntu/bionic64"}
azure_subscription_id=${AZURE_SUBSCRIPTION_ID:=""}
azure_tenant_id=${AZURE_TENANT_ID:=""}
azure_client_secret=${AZURE_CLIENT_SECRET:=""}
azure_client_id=${AZURE_CLIENT_ID:=""}
azure_region=${AZURE_REGION:="westeurope"}
azure_image_urn=${AZURE_IMAGE_URN:="Canonical:UbuntuServer:16.04-LTS:latest"}
azure_resource_group=${AZURE_RESOURCE_GROUP:="bdb-vagrant-rg-$(date '+%Y-%m-%d')"}
azure_dns_prefix=${AZURE_DNS_PREFIX:="bdb-instance-$(date '+%Y-%m-%d')"}
azure_admin_username=${AZURE_ADMIN_USERNAME:="vagrant"}
azure_vm_size=${AZURE_VM_SIZE:="Standard_D2_v2"}
ssh_private_key_path=${SSH_PRIVATE_KEY_PATH:=""}
unstack_type=${UNSTACK_TYPE:="hard"}


# Check for uninitialized variables
NOUNSET=${NOUNSET:-}
if [[ -n "$NOUNSET" ]]; then
	set -o nounset
fi

TOP_DIR=$(cd $(dirname "$0") && pwd)
SCRIPTS_DIR=$TOP_DIR/bigchaindb/pkg/scripts
CONF_DIR=$TOP_DIR/bigchaindb/pkg/configuration

function usage() {
	cat <<EOM

    Usage: $ bash ${0##*/} [-h]

    Deploys the BigchainDB network.

    ENV[STACK_SIZE]
        Set STACK_SIZE environment variable to the size of the network you desire.
        Network mimics a production network environment with single or multiple BDB
        nodes. (default: ${stack_size}).

    ENV[STACK_TYPE]
        Set STACK_TYPE environment variable to the type of deployment you desire.
        You can set it one of the following: ["docker", "local", "cloud"].
        (default: ${stack_type})

    ENV[STACK_TYPE_PROVIDER]
        Set only when STACK_TYPE="cloud". Only "azure" is supported.
        (default: ${stack_type_provider})

    ENV[STACK_VM_MEMORY]
        (Optional) Set only when STACK_TYPE="local". This sets the memory
        of the instance(s) spawned. (default: ${stack_vm_memory})

    ENV[STACK_VM_CPUS]
        (Optional) Set only when STACK_TYPE="local". This sets the number of VCPUs
        of the instance(s) spawned. (default: ${stack_vm_cpus})

    ENV[STACK_BOX_NAME]
        (Optional) Set only when STACK_TYPE="local". This sets the box Vagrant box name
        of the instance(s) spawned. (default: ${stack_box_name})

    ENV[STACK_REPO]
        (Optional) To configure bigchaindb repo to use, set STACK_REPO environment
        variable. (default: ${stack_repo})

    ENV[STACK_BRANCH]
        (Optional) To configure bigchaindb repo branch to use set STACK_BRANCH environment
        variable. (default: ${stack_branch})

    ENV[TM_VERSION]
        (Optional) Tendermint version to use for the setup. (default: ${tm_version})

    ENV[MONGO_VERSION]
        (Optional) MongoDB version to use with the setup. (default: ${mongo_version})

    ENV[AZURE_CLIENT_ID]
        Only required when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure". Steps to generate:
        https://github.com/Azure/vagrant-azure#create-an-azure-active-directory-aad-application

    ENV[AZURE_TENANT_ID]
        Only required when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure". Steps to generate:
        https://github.com/Azure/vagrant-azure#create-an-azure-active-directory-aad-application

    ENV[AZURE_SUBSCRIPTION_ID]
        Only required when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure". Steps to generate:
        https://github.com/Azure/vagrant-azure#create-an-azure-active-directory-aad-application

    ENV[AZURE_CLIENT_SECRET]
        Only required when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure". Steps to generate:
        https://github.com/Azure/vagrant-azure#create-an-azure-active-directory-aad-application

    ENV[AZURE_REGION]
        (Optional) Only applicable, when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure".
        Azure region for the BigchainDB instance. Get list of regions using Azure CLI.
        e.g. az account list-locations. (default: ${azure_region})

    ENV[AZURE_IMAGE_URN]
        (Optional) Only applicable, when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure".
        Azure image to use. Get list of available images using Azure CLI.
        e.g. az vm image list --output table. (default: ${azure_image_urn})

    ENV[AZURE_RESOURCE_GROUP]
        (Optional) Only applicable, when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure".
        Name of Azure resource group for the instance.
        (default: ${azure_resource_group})

    ENV[AZURE_DNS_PREFIX]
        (Optional) Only applicable, when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure".
        DNS Prefix of the instance. (default: ${azure_dns_prefix})

    ENV[AZURE_ADMIN_USERNAME]
        (Optional) Only applicable, when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure".
        Admin username of the the instance. (default: ${azure_admin_username})

    ENV[AZURE_VM_SIZE]
        (Optional) Only applicable, when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure".
        Azure VM size. (default: ${azure_vm_size})

    ENV[SSH_PRIVATE_KEY_PATH]
        Only required when STACK_TYPE="cloud" and STACK_TYPE_PROVIDER="azure". Absolute path of
        SSH keypair required to log into the Azure instance.

    ENV[UNSTACK_TYPE]
        Hard or Soft unstack. (default ${unstack_type})

    -s
        Soft unstack, only stop the processes.

    -h
        Show this help and exit.

EOM
}

while getopts ":h:s" opt; do
	case "$opt" in
	h)
		usage
		exit
		;;
    s)
      unstack_type="soft"
      ;;
	*)
		usage
		exit 1
		;;
	esac
done

mkdir -p logs
log_file=logs/install-$(date +%Y%m%d-%H%M%S).log
exec > >(tee $log_file) 2>&1
echo "Capturing output to $log_file"
echo "Installation started at $(date '+%Y-%m-%d %H:%M:%S')"

function finish() {
	echo "Installation finished at $(date '+%Y-%m-%d %H:%M:%S')"
}
trap finish EXIT

export STACK_REPO=$stack_repo
export STACK_BRANCH=$stack_branch
echo "Using bigchaindb repo: '$STACK_REPO'"
echo "Using bigchaindb branch '$STACK_BRANCH'"

git clone https://github.com/${stack_repo}.git -b ${stack_branch} || true

# Source utility functions
source ${SCRIPTS_DIR}/functions-common

if [[ $stack_type == "local" ]]; then
	mongo_version=$(echo "$mongo_version" | cut -d. -f-2)
fi

# configure stack-config.yml
cat >$TOP_DIR/bigchaindb/pkg/configuration/vars/stack-config.yml <<EOF
---
stack_type: "${stack_type}"
stack_size: "${stack_size}"
stack_type_provider: "${stack_type_provider}"
stack_box_name: "${stack_box_name}"
stack_vm_memory: "${stack_vm_memory}"
stack_vm_cpus: "${stack_vm_cpus}"
tm_version: "${tm_version}"
mongo_version: "${mongo_version}"
azure_region: "${azure_region}"
azure_image_urn: "${azure_image_urn}"
azure_resource_group: "${azure_resource_group}"
azure_dns_prefix: "${azure_dns_prefix}"
azure_admin_username: "${azure_admin_username}"
azure_vm_size: "${azure_vm_size}"
ssh_private_key_path: "${ssh_private_key_path}"
EOF

curl -fOL# https://raw.githubusercontent.com/${stack_repo}/${stack_branch}/pkg/scripts/Vagrantfile

#Convert to lowercase
stack_type="$(echo $stack_type | tr '[A-Z]' '[a-z]')"
stack_type_provider="$(echo $stack_type_provider | tr '[A-Z]' '[a-z]')"

if [[ $stack_type == "local" ]]; then
  if [[ $unstack_type == "hard" ]]; then
    vagrant destroy -f
  elif [[ $unstack_type == "soft" ]]; then
    ansible-playbook $CONF_DIR/bigchaindb-stop.yml -i $CONF_DIR/hosts/all \
      --extra-vars "operation=stop home_path=${TOP_DIR}"
  fi
elif [[ $stack_type == "cloud" && $stack_type_provider == "azure" ]]; then
  echo "Configuring Setup on Azure!"
  if [[ $unstack_type == "hard" ]]; then
    vagrant destroy -f
  elif [[ $unstack_type == "soft" ]]; then
    ansible-playbook $CONF_DIR/bigchaindb-stop.yml -i $CONF_DIR/hosts/all \
      --extra-vars "operation=stop home_path=${TOP_DIR}"
  fi
elif [[ $stack_type == "docker" ]]; then
  echo "Configuring Dockers locally!"
  source $SCRIPTS_DIR/bootstrap.sh --operation install
  cat > $CONF_DIR/hosts/all << EOF
  $(hostname)  ansible_connection=local
EOF

  ansible-playbook $CONF_DIR/bigchaindb-stop.yml -i $CONF_DIR/hosts/all \
    --extra-vars "operation=stop home_path=${TOP_DIR}"
else
  echo "Invalid Stack Type OR Provider"
  exit 1
fi

# Kill background processes on exit
trap exit_trap EXIT
function exit_trap {
    exit $?
}
# Exit on any errors so that errors don't compound and kill if any services already started
trap err_trap ERR
function err_trap {
    local r=$?
    tmux kill-session bdb-dev
    set +o xtrace
    exit $?
}

echo -e "Finished unstacking!!"
set -o errexit
