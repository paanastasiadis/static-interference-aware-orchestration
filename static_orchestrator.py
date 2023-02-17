import csv
import os.path
import subprocess
from flask import Flask, request, make_response

# Create a Flask app
app = Flask(__name__)

# Define a deployment configuration in YAML format
DEPLOYMENT_CONFIG = DEPLOYMENT_CONFIG = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {appname}-deployment
spec:
  selector:
    matchLabels:
      app: {appname}-app
  template:
    metadata:
      labels:
        app: {appname}-app
    spec:
      nodeSelector:
        group: {nodename}
      containers:
      - name: {appname}-container
        image: {imagename}
"""

# Define the filename format for the deployment YAML files.
DEPLOYMENT_YAML = "deployment_{appname}.yaml"

# Define a dictionary to store the running apps and their respective nodes.
nodes = {
    "node1": {
        "apps": []
    },
    "node2": {
        "apps": []
    }
}

# Read the list of running apps from the CSV file if exists.
def get_running_apps_from_file():
    path = "./deployed_apps.csv"
    if not os.path.isfile(path):
        return
    with open("deployed_apps.csv", "r") as input_file:
        csv_file = csv.reader(input_file, delimiter=";")
        for row in csv_file:
            app = {
                "name": row[1],
                "type": row[2],
                "image": row[3]
            }
            nodes[row[0]]["apps"].append(app)

# Check if an app with the same name already exists on one of the nodes.
def is_existing_app(app):
    is_existing = False
    for node in nodes:
        for apps in nodes[node]:
            for existing_app in nodes[node][apps]:
                if (existing_app["name"] == app["name"]):
                    is_existing = True
    return is_existing

# Deploy the app to a specific node using Kubernetes.
def deploy_app(app, node):
    formatted_deployment_config = DEPLOYMENT_CONFIG.format(
        nodename=node, appname=app["name"].lower(), imagename=app["image"])
    yaml = DEPLOYMENT_YAML.format(appname=app["name"])

    with open(yaml, "w") as f:
        f.write(formatted_deployment_config)

    result = subprocess.run(["kubectl", "apply", "-f", yaml])
    if result.returncode == 0:
        # If the deployment is successful, add the app to the running apps list.
        with open("deployed_apps.csv", "a") as output_file:
            output_file.write("{};{};{};{}\n".format(
                node, app["name"], app["type"], app["image"]))
        return True
    return False

# Orchestrate the deployment of the app by selecting the appropriate node to deploy it to.
def orchestrate_app(app):
    
    # If a node has no running apps, deploy the app to that node.
    for node in nodes:
        for apps in nodes[node]:
            if len(nodes[node][apps]) == 0:
                if deploy_app(app, node):
                    nodes[node][apps].append(app)
                    return True

    for node in nodes:
        for apps in nodes[node]:
            if len(nodes[node][apps]) >= 2:
                continue
            # If a node has only one running app,
            # deploy the app to that node if the app types are different.
            for existingApp in nodes[node][apps]:
                if existingApp["type"] != app["type"]:
                    if deploy_app(app, node):
                        nodes[node][apps].append(app)
                        return True
    return False


@app.route('/deploy', methods=['POST'])
def deploy():

    # Get the app data from the request
    request_json = request.get_json()
    app = request_json

    # Validate the app data
    if ("name" not in app or "type" not in app or "image" not in app):
        return make_response("Bad request format!", 400)

    if (app["type"] != 'Memory' and app["type"] != "CPU"):
        return make_response("Bad Request Format", 400)

    # Check if the app has already been deployed
    if is_existing_app(app):
        return make_response("The requested app has already been deployed!", 400)

    # Try to orchestrate the app deployment
    if orchestrate_app(app):
        return make_response("Deployment was successful!", 200)
    else:
        return make_response("There was a problem with deployment!", 500)


# Read any existing running apps from the deployed_apps.csv file
get_running_apps_from_file()

if __name__ == "__main__":
    app.run(port=5000)
