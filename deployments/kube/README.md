## Kubernetes Deployment

#### Table of Contents

- [Deployment the Somewhat Easy Way](#deployment-the-somewhat-easy-way)
- [Deployment The Difficult Way](#deployment-the-difficult-way)
	- [Deploy Fake CEGA](#deploy-fake-cega)
	- [Deploy LocalEGA](#deploy-localega)
	- [Other useful information](#other-useful-information)
- [Deployment the OpenShift Way](#deployment-the-openshift-way)


### Deployment the "Easy" Way

We provide an python script based on https://github.com/kubernetes-client/python that sets up all the necessary configuration (e.g. generating keys, certificates, configuration files etc.) and pods along with necessary services and volumes.
The script is intended to work both with a minikube or any Kubernetes cluster, provided the user has an API key.

**NOTES:**
  - **Requires Python >3.6.**
  - **Work in Progress**

The script is in `auto` folder and can be run as:
```
cd ~/LocalEGA/deployment/kube/auto
pip install -r requirements.txt
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

### Deployment The Difficult Way

The YAML files (from the `yml` directory) represent vanilla deployment setup configuration for LocalEGA, configuration that does not include configuration/passwords for starting services. Such configuration can generated using the `make bootstrap` script in the `~/LocalEGA/deployment/docker` folder or provided per each case. The YML file only provide base `hostPath` volumes, for other volume types check [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/).

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
kubectl create -f ./lega-config --namespace=localega
kubectl create -f ./mq -f ./postgres -f ./s3 --namespace=localega
kubectl create -f ./keys -f ./verify -f ./ingest -f ./inbox --namespace=localega
```

#### Other useful information

* See minikube services: `minikube service list`
* Delete services: `kubectl delete -f ./keys`
* Working with [volumes in Minio](https://vmware.github.io/vsphere-storage-for-kubernetes/documentation/minio.html)

### Deployment the OpenShift Way

The files provided in the `yml` directory can be reused for deployment to OpenShift with some changes:
- Minio requires `10Gi` volume to start properly in Openshift, although in minikube it it seems to do by with just 0.5Gi.
- By default, OpenShift Origin runs containers using an arbitrarily assigned user ID as per [OpenShift Guidelines](https://docs.openshift.org/latest/creating_images/guidelines.html#openshift-specific-guidelines), thus using `gosu` command for changing user is not allowed. The command for keyserver would look like `["ega-keyserver","--keys","/etc/ega/keys.ini"]` instead of `["gosu","lega","ega-keyserver","--keys","/etc/ega/keys.ini"]`.

* Postgres DB requires a different container therefore we provided a different YML configuration file for it in the `os/postgres` directory, also the volume attached to Postgres DB needs `ReadWriteMany` permissions.
* Keyserver requires different configuration therefore we provided a different YML configuration file for it in the `os/keys` directory.
