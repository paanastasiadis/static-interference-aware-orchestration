# Static interference-aware resource orchestration using infrastructure monitoring for a known set of containerized apps  

## Introduction

This project aims to orchestrate resource allocation in a Kubernetes cluster for a known set of containerized applications. The project utilizes infrastructure monitoring to allocate resources such that interference between applications is minimized.

## Prerequisites

The following tools must be installed:

* kind
* docker
* kubectl
* helm
* python (Flask)

## Setup

### Creating a Kubernetes Cluster

1. Delete any previously created clusters by running:

```
kind delete clusters --all
```

2. Create a new local cluster with one master and two worker nodes by running the following command inside the project's root directory:

```
kind create cluster --name=cluster-kind --config=create_cluster.yaml
```

The name of our cluster will be `cluster-kind`, and the name of the worker nodes will be `cluster-kind-worker` and `cluster-kind-worker2`, respectively.

## Assigning labels to nodes

To influence the scheduler into choosing specific nodes for deploying our apps, we need to assign specific labels to the worker nodes.

1. For the first worker node `cluster-kind-worker`, run:

```
kubectl label nodes cluster-kind-worker group=node1
```

2. For the second worker, cluster-kind-worker2, run:

```
kubectl label nodes cluster-kind-worker2 group=node2
```

## Installing Prometheus and Grafana

1. Install the kube-prometheus-stack ([Github](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)) package containing both Prometheus and Grafana using the helm package manager. Run the following commands:

```
helm repo update
```

```
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack
```

2. Forward the Grafana Pod to port 3000 to access the Grafana page from the browser:

```
kubectl --namespace default port-forward <kube-prometheus-grafana-pod-name> 3000
```

Replace `<kube-prometheus-grafana-pod-name>` with the exact name of the Grafana Pod. You can check the name of the pod by checking the detailed information about Pods by running:

```
kubectl get pods -A -o wide
```

## Testing Apps

For this experiment, we use the **Phoronix Test Suite**.

Using the docker image **phoronix/pts** as a base, we managed to create four new images for stress testing CPU and memory. Each image has one test app installed from the Phoronix Test Suite.

### Installed Tests

CPU-heavy Tests

* [pts/compress-7zip](https://hub.docker.com/r/paanastasiadis/pts-compress7zip)
* [pts/c-ray](https://hub.docker.com/r/paanastasiadis/pts-cray)

RAM-Heavy Tests

* [pts/mbw](https://hub.docker.com/r/paanastasiadis/pts-mbw)
* [pts/stressapptest](https://hub.docker.com/r/paanastasiadis/pts-stressapptest)

## About Script

### Static Orchestrator

* `static_orchestrator.py`

This is a Python script that deploys containerized applications to two nodes. The script is built using Flask and uses Kubernetes for deployment.

### Getting Started

To run the script, execute the following command:

```
python static_orchestrator.py
```

### Deployment

To deploy a new application, send an HTTP POST request to the `/deploy` endpoint with the following JSON payload:

```
{
    "name": "myapp",
    "type": "CPU or Memory",
    "image": "myregistry/myapp:latest"
}
```

The `name` field is the name of the application, `type` is the resource type that the application requires, and `image` is the Docker image that will be deployed.

If the deployment is successful, the server will respond with an HTTP 200 status code and a success message. If there is a problem with the deployment, the server will respond with an HTTP 500 status code and an error message.

### Monitoring

To monitor the status of the deployed apps, use a tool like Postman to make an HTTP request to the `/deploy` endpoint with the desired app name.

After deploying one or more apps to the cluster, run the following command to see the status of the pods:

```
kubectl get pods -A -o wide
```

Each CPU-intensive app should be deployed to a separate node, and the same should be true for the memory-intensive apps.

### Limitations

This script is designed for a static infrastructure with two nodes and may not work well in dynamic environments. It also assumes that the Kubernetes cluster is set up properly with `kubectl` configured on the machine where the script is executed.

## Running Tests

After deploying one or more apps to the cluster, you can access the bash terminal of an app and run a corresponding test.

### Accessing the Bash Terminal

To access the bash terminal of an app, run the following command, replacing `<app-pod-name>` with the name of the Pod for the desired app:

```
kubectl exec --stdin --tty <app-pod-name> -- /bin/bash
```

### Running a Test

After accessing the bash terminal of an app, run the corresponding test using the following command, replacing `<installed-test>` with one of the following depending on the app:

* pts/c-ray
* pts/compress-7zip
* pts/stressapptest
* pts/mbw

```
./phoronix-test-suite/phoronix-test-suite run <installed-test>
```

## Performance Monitoring with Grafana

After deploying the apps to the cluster and running the tests inside them, you can use the Grafana page to monitor their performance. To access the Grafana page, use the following credentials:

* `username`: admin
* `password`: prom-operator

Once you have logged in, navigate to `Dashboards` > `Browse` and select any of the available options for Kubernetes monitoring, such as "Kubernetes / Compute Resources / Node (Pods)".

## Deploying apps manually

If you want to deploy any of the apps manually to a specific node, you can use a YAML configuration. For example, to deploy the **MBW** app specifically to **cluster-worker2**, use the following YAML configuration:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mbw-deployment
spec:
  selector:
    matchLabels:
      app: mbw-app
  template:
    metadata:
      labels:
        app: mbw-app
    spec:
      nodeSelector:
        group: node2
      containers:
      - name: mbw-container
        image: docker.io/paanastasiadis/pts-mbw
```

Save this configuration to a file named `deployment_mbw.yaml` and run the following command to deploy the app:

```
kubectl apply -f deployment_mbw.yaml
```

Note that you can replace MBW with any other app that you want to deploy manually.
