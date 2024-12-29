"""
cloud/azure_integration.py

This module handles integration with Microsoft Azure cloud services, providing support for
key functionalities such as virtual machines, storage accounts, AI services, and networking.
"""

import os
import azure.identity
import azure.mgmt.compute
import azure.mgmt.storage
import azure.mgmt.network
import azure.ai.textanalytics

# Constants
AZURE_CREDENTIALS_ENV_VARS = ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"]
DEFAULT_REGION = "East US"

# Azure Authentication
def get_azure_credentials():
    """
    Retrieves Azure credentials from environment variables.
    """
    try:
        for var in AZURE_CREDENTIALS_ENV_VARS:
            if var not in os.environ:
                raise EnvironmentError(f"{var} is not set in the environment variables.")
        credentials = azure.identity.ClientSecretCredential(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            client_secret=os.environ["AZURE_CLIENT_SECRET"]
        )
        return credentials
    except Exception as e:
        raise RuntimeError(f"Error retrieving Azure credentials: {e}")

# Azure Virtual Machine Operations
def list_virtual_machines(credentials, subscription_id):
    """
    Lists all virtual machines in a given subscription.
    """
    try:
        compute_client = azure.mgmt.compute.ComputeManagementClient(credentials, subscription_id)
        vms = compute_client.virtual_machines.list_all()
        return [vm.name for vm in vms]
    except Exception as e:
        raise RuntimeError(f"Error listing virtual machines: {e}")

def create_virtual_machine(credentials, subscription_id, resource_group, vm_name, region=DEFAULT_REGION):
    """
    Creates a virtual machine in Azure.
    """
    try:
        compute_client = azure.mgmt.compute.ComputeManagementClient(credentials, subscription_id)
        # Example VM creation details (extend as needed)
        vm_params = {
            # Add VM creation parameters here
        }
        compute_client.virtual_machines.begin_create_or_update(resource_group, vm_name, vm_params)
        return f"Virtual machine '{vm_name}' created successfully."
    except Exception as e:
        raise RuntimeError(f"Error creating virtual machine: {e}")

# Azure Storage Account Operations
def create_storage_account(credentials, subscription_id, resource_group, account_name, region=DEFAULT_REGION):
    """
    Creates a storage account in Azure.
    """
    try:
        storage_client = azure.mgmt.storage.StorageManagementClient(credentials, subscription_id)
        storage_params = {
            "location": region,
            "sku": {"name": "Standard_LRS"},
            "kind": "StorageV2",
        }
        storage_client.storage_accounts.begin_create(resource_group, account_name, storage_params)
        return f"Storage account '{account_name}' created successfully."
    except Exception as e:
        raise RuntimeError(f"Error creating storage account: {e}")

# Azure Networking Operations
def list_virtual_networks(credentials, subscription_id):
    """
    Lists all virtual networks in a given subscription.
    """
    try:
        network_client = azure.mgmt.network.NetworkManagementClient(credentials, subscription_id)
        vnets = network_client.virtual_networks.list_all()
        return [vnet.name for vnet in vnets]
    except Exception as e:
        raise RuntimeError(f"Error listing virtual networks: {e}")

# Azure AI Services (Text Analytics Example)
def analyze_text(credentials, endpoint, api_key, text):
    """
    Analyzes text using Azure's Text Analytics service.
    """
    try:
        text_analytics_client = azure.ai.textanalytics.TextAnalyticsClient(
            endpoint=endpoint,
            credential=azure.core.credentials.AzureKeyCredential(api_key)
        )
        result = text_analytics_client.analyze_sentiment([text])[0]
        return {
            "sentiment": result.sentiment,
            "confidence_scores": result.confidence_scores
        }
    except Exception as e:
        raise RuntimeError(f"Error analyzing text: {e}")

# Main Entry Point for Testing
if __name__ == "__main__":
    try:
        # Set subscription and resource details
        SUBSCRIPTION_ID = "your_subscription_id"
        RESOURCE_GROUP = "your_resource_group"
        VM_NAME = "test-vm"
        STORAGE_ACCOUNT_NAME = "teststorageaccount"
        TEXT = "Azure is a powerful cloud platform."

        # Authenticate
        creds = get_azure_credentials()

        # Perform operations
        print("Listing Virtual Machines:")
        print(list_virtual_machines(creds, SUBSCRIPTION_ID))

        print("\nCreating Virtual Machine:")
        print(create_virtual_machine(creds, SUBSCRIPTION_ID, RESOURCE_GROUP, VM_NAME))

        print("\nCreating Storage Account:")
        print(create_storage_account(creds, SUBSCRIPTION_ID, RESOURCE_GROUP, STORAGE_ACCOUNT_NAME))

        print("\nListing Virtual Networks:")
        print(list_virtual_networks(creds, SUBSCRIPTION_ID))

        print("\nAnalyzing Text Sentiment:")
        print(analyze_text(creds, "your_text_analytics_endpoint", "your_text_analytics_api_key", TEXT))
    except Exception as e:
        print(f"Error: {e}")
