## Kubernetes Deployment

### Deployment The Hard Way

The YAML files do not include configuration/passwords for starting services. Such configuration can generated using the `make bootstrap` script in the `~/LocalEGA/deployment/docker` folder or provided per each case.

File that require configuration:
* `keyserver/cm.keyserver.yml`
* `keyserver/secret.keyserver.yml`
* `lega-config/cm.lega.yml`
* `lega-config/secret.lega.yml`
* `mq/cm.lega-mq.yml`
* `mq/sts.lega-mq.yml`

Following instructions are for Minikube deployment:
Once [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/) and [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) are installed:

```
cd ~/LocalEGA/deployment/kube
minikube start
kubectl create namespace localega
```
#### Deploy Fake CEGA

Only the CEGA Broker is available for now and its address needs to be setup LocalEGA broker in `amqp://<user>:<password>@<cega-ip>:5672/<queue>`
The `<cega-ip>` is the IP of the Kubernetes Pod for CEGA Broker.
```
kubectl create -f ./cega-mq
```
####  Deploy LocalEGA
```
kubectl create -f ./lega-config -f ./mq -f ./postgres -f ./s3
kubectl create -f ./keyserver -f ./verify -f ./ingest -f ./inbox
```

#### Other useful information

* See minikube services: `minikube service list`
* Delete services: `kubectl delete -f ./keyserver`
* Working with [volumes in Minio](https://vmware.github.io/vsphere-storage-for-kubernetes/documentation/minio.html)
