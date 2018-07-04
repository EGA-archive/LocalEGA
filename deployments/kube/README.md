## Kubernetes Deployment

### Deployment the "Easy" Way

We provide an python script based on https://github.com/kubernetes-client/python the sets up all the necessary configuration (e.g. generating keys, certificates, configuration files etc.) and pods along with necessary services and volumes.
The script is intended to work both with a minikube or any kubernetes cluster, provided the user has an API key.

**NOTE: Requires Python >3.6.**

The script is in `auto` and can be run as:
```
cd ~/LocalEGA/deployment/kube/auto
pyton deploy.py
kubectl create -f ../yml/cega-mq --namespace=testing
```

In the `deploy.py` service/pods names and other parameters can be configured:
```json
_localega = {
      "namespace": "testing",
      "role": "testing",
      "services": {"keys": "keys",
                   "inbox": "inbox",
                   "ingest": "ingest",
                   "s3": "minio",
                   "broker": "mq",
                   "db": "db",
                   "verify": "verify"},
      "cega": {"ip": "ip", "user": "lega", "pwd": "pass", "endpoint": "rest_api"}
  }
```

### Deployment The Hard Way

The YAML files (from the `yml` directory) represent vanilla deployment setup configuration for LocalEGA, configuration that does not include configuration/passwords for starting services. Such configuration can generated using the `make bootstrap` script in the `~/LocalEGA/deployment/docker` folder or provided per each case.

File that require configuration:
* `keys/cm.keyserver.yml`
* `keys/secret.keyserver.yml`
* `lega-config/cm.lega.yml`
* `lega-config/secret.lega.yml`
* `mq/cm.lega-mq.yml`
* `mq/sts.lega-mq.yml`

Following instructions are for Minikube deployment:
Once [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/) and [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) are installed:

```
cd ~/LocalEGA/deployment/kube/yml
minikube start
kubectl create namespace localega
```
#### Deploy Fake CEGA

Only the CEGA Broker is available for now and its address needs to be setup LocalEGA broker in `amqp://<user>:<password>@<cega-ip>:5672/<queue>`
The `<cega-ip>` is the IP of the Kubernetes Pod for CEGA Broker.
```
kubectl create -f ./cega-mq --namespace=localega
```
####  Deploy LocalEGA
```
kubectl create -f ./lega-config -f ./mq -f ./postgres -f ./s3
kubectl create -f ./keys -f ./verify -f ./ingest -f ./inbox
```

#### Other useful information

* See minikube services: `minikube service list`
* Delete services: `kubectl delete -f ./keys`
* Working with [volumes in Minio](https://vmware.github.io/vsphere-storage-for-kubernetes/documentation/minio.html)
