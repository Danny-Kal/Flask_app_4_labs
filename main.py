from flask import Flask, render_template, Response
import os
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask app initialization
app = Flask(__name__)

# Retrieve Azure authentication variables
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = os.getenv("RESOURCE_GROUP")
BICEP_FILE = os.getenv("BICEP_FILE")

# Authenticate using Azure SDK
credentials = ClientSecretCredential(AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
resource_client = ResourceManagementClient(credentials, SUBSCRIPTION_ID)

@app.route('/')
def index():
    """Render the main page with the deploy button."""
    return render_template('index.html')

from subprocess import run
import shutil

import json
from subprocess import run
import shutil

@app.route('/deploy-lab', methods=['POST'])
def deploy_lab():
    """Trigger Azure Bicep deployment using Azure SDK (convert Bicep to ARM JSON first)."""
    try:
        # ✅ Get full path of 'az' CLI
        az_path = shutil.which("az")
        if not az_path:
            return Response("<span style='color: red;'>Error: Azure CLI (az.exe) not found in PATH.</span>", mimetype="text/html", status=500)

        print(f"Using Azure CLI at: {az_path}")

        # Ensure resource group exists
        print(f"Checking if Resource Group '{RESOURCE_GROUP}' exists...")
        resource_groups = [rg.name for rg in resource_client.resource_groups.list()]
        if RESOURCE_GROUP not in resource_groups:
            return Response(f"<span style='color: red;'>Error: Resource Group '{RESOURCE_GROUP}' not found.</span>", mimetype="text/html", status=500)

        # ✅ Convert Bicep file to ARM JSON using full az path
        print(f"Converting Bicep file '{BICEP_FILE}' to ARM JSON...")
        convert_result = run([az_path, "bicep", "build", "--file", BICEP_FILE], capture_output=True, text=True, check=True)

        if convert_result.returncode != 0:
            return Response(f"<span style='color: red;'>Bicep conversion failed: {convert_result.stderr}</span>", mimetype="text/html", status=500)

        # ✅ Get converted ARM JSON file path
        arm_template_file = BICEP_FILE.replace(".bicep", ".json")

        # ✅ Read and parse the converted JSON template
        print(f"Reading and parsing ARM JSON file: {arm_template_file}")
        with open(arm_template_file, "r") as file:
            arm_template = json.load(file)  # ✅ Converts JSON string to dictionary

        # ✅ Deployment properties for ARM JSON
        deployment_properties = {
            "properties": {
                "mode": "Incremental",
                "template": arm_template  # ✅ Now passing a dictionary, not a string
            }
        }

        # ✅ Deploy using Azure SDK
        print("Deploying converted ARM JSON template...")
        deployment_result = resource_client.deployments.begin_create_or_update(
            RESOURCE_GROUP, "DeploymentName", deployment_properties
        )

        # Wait for deployment to complete
        deployment_result.result()

        return Response("<span style='color: green;'>Lab deployed successfully!</span>", mimetype="text/html")

    except Exception as e:
        print("Deployment Error:", str(e))  # Log error to console
        return Response(f"<span style='color: red;'>Error: {str(e)}</span>", mimetype="text/html", status=500)


if __name__ == '__main__':
    app.run(debug=True)
