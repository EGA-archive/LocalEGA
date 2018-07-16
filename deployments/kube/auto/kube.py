import string
import secrets
import logging
from base64 import b64encode
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Logging
FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

# Setup kubernete configuration
config.load_kube_config()
api_core = client.CoreV1Api()
api_app = client.AppsV1Api()
api_beta_app = client.AppsV1beta1Api()
api_extension = client.ExtensionsV1beta1Api()


class LocalEGADeploy:
    """LocalEGA kubernetes deployment.

    Deployment configuration for LocalEGA to kubernetes.
    """

    def __init__(self, keys, namespace):
        """Set things up."""
        self.keys = keys
        self._namespace = namespace
        self._role = keys["role"]

    def create_namespace(self):
        """Create default namespace if not exists."""
        namespace_list = api_core.list_namespace(label_selector='role')
        namespaces = [x for x in namespace_list.items if x.metadata.labels['role'] == self._role]

        if len(namespaces) == 0:
            namespace = client.V1Namespace()
            namespace.metadata = client.V1ObjectMeta(name=self._namespace, labels={'role': self._role})
            api_core.create_namespace(namespace)
            LOG.info(f'Namespace: {self._namespace} created.')
        else:
            pass
            LOG.info(f'Namespace: {self._namespace} exists.')

    def _generate_secret(self, value):
        """Generate secret of specifig value.

        .. note: If the value is of type integer it will generate a random of that value,
        else it will take that value.
        """
        if isinstance(value, int):
            secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(value)).encode("utf-8")
            return b64encode(secret).decode("utf-8")
        else:
            return b64encode(value.encode("utf-8")).decode("utf-8")

    # Default Secrets
    def config_secret(self, name, data, patch=False):
        """Create and upload secret, patch option also available."""
        sec_conf = client.V1Secret()
        sec_conf.metadata = client.V1ObjectMeta(name=name)
        sec_conf.type = "Opaque"
        sec_conf.data = {key: self._generate_secret(value) for (key, value) in data.items()}
        try:
            api_core.create_namespaced_secret(namespace=self._namespace, body=sec_conf)
            LOG.info(f'Secret: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_core.patch_namespaced_secret(name=name, namespace=self._namespace, body=sec_conf)
                LOG.info(f'Secret: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def config_map(self, name, data, patch=False):
        """Create and upload configMap, patch option also available."""
        conf_map = client.V1ConfigMap()
        conf_map.metadata = client.V1ObjectMeta(name=name)
        conf_map.data = data

        try:
            api_core.create_namespaced_config_map(namespace=self._namespace, body=conf_map)
            LOG.info(f'ConfigMap: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_core.patch_namespaced_config_map(name=name, namespace=self._namespace, body=conf_map)
                LOG.info(f'ConfigMap: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def deployment(self, name, image, command, env, vmounts, volumes, lifecycle=None, args=None, ports=None, replicas=1, patch=False):
        """Create and upload deployment, patch option also available."""
        deploy = client.V1Deployment(kind="Deployment", api_version="apps/v1")
        deploy.metadata = client.V1ObjectMeta(name=name)
        container = client.V1Container(name=name, image=image, image_pull_policy="IfNotPresent",
                                       volume_mounts=vmounts, command=command, env=env, args=args, lifecycle=lifecycle)
        if ports:
            container.ports = list(map(lambda x: client.V1ContainerPort(container_port=x), ports))
        template = client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels={"app": name}),
                                            spec=client.V1PodSpec(containers=[container], volumes=volumes, restart_policy="Always"))
        spec = client.V1DeploymentSpec(replicas=replicas, template=template, selector=client.V1LabelSelector(match_labels={"app": name}))
        deploy.spec = spec
        try:
            api_app.create_namespaced_deployment(namespace=self._namespace, body=deploy)
            LOG.info(f'Deployment: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_app.patch_namespaced_deployment(name=name, namespace=self._namespace, body=deploy)
                LOG.info(f'Deployment: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def service(self, name, ports, pod_name=None, type="ClusterIP", patch=False):
        """Create and upload service, patch option also available."""
        svc_conf = client.V1Service(kind="Service", api_version="v1")
        svc_conf.metadata = client.V1ObjectMeta(name=name)
        spec = client.V1ServiceSpec(selector={"app": pod_name if pod_name else name}, ports=ports, type=type)
        svc_conf.spec = spec

        try:
            api_core.create_namespaced_service(namespace=self._namespace, body=svc_conf)
            LOG.info(f'Service: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_core.patch_namespaced_service(name=name, namespace=self._namespace, body=svc_conf)
                LOG.info(f'Service: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def stateful_set(self, name, image, command, env, vmounts, vol, vol_claims=None, sec=None, args=None, ports=None, replicas=1, patch=False):
        """Create and upload StatefulSet, patch option also available."""
        sts_conf = client.V1StatefulSet()
        sts_conf.metadata = client.V1ObjectMeta(name=name)
        container = client.V1Container(name=name, image=image, image_pull_policy="IfNotPresent",
                                       volume_mounts=vmounts, command=command, env=env, args=args, security_context=sec)
        if ports:
            container.ports = list(map(lambda x: client.V1ContainerPort(container_port=x), ports))
        template = client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels={"app": name}),
                                            spec=client.V1PodSpec(containers=[container], volumes=vol, restart_policy="Always"))
        spec = client.V1StatefulSetSpec(replicas=replicas, template=template, selector=client.V1LabelSelector(match_labels={"app": name}),
                                        service_name=name, volume_claim_templates=vol_claims)
        sts_conf.spec = spec
        try:
            api_app.create_namespaced_stateful_set(namespace=self._namespace, body=sts_conf)
            LOG.info(f'Service: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch and not (vol_claims is None):
                api_app.patch_namespaced_stateful_set(name=name, namespace=self._namespace, body=sts_conf)
                LOG.info(f'Service: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def persistent_volume_claim(self, name, volume_name, storage, accessModes=["ReadWriteOnce"]):
        """Create a volume claim."""
        claim_vol = client.V1PersistentVolumeClaim(kind="PersistentVolumeClaim", api_version="v1")
        claim_vol.metadata = client.V1ObjectMeta(name=name)
        spec = client.V1PersistentVolumeClaimSpec(volume_name=volume_name, access_modes=accessModes, storage_class_name=volume_name)
        spec.resources = client.V1ResourceRequirements(requests={"storage": storage})
        claim_vol.spec = spec
        try:
            api_core.create_namespaced_persistent_volume_claim(namespace=self._namespace, body=claim_vol)
            LOG.info(f'Volume claim: {name} created.')
        except ApiException as e:
            LOG.error(f'Exception message: {e}')

    def persistent_volume(self, name, storage, accessModes=["ReadWriteOnce"], host_path=True, patch=False):
        """Create persistent volume by default on host."""
        ps_vol = client.V1PersistentVolume(kind="PersistentVolume", api_version="v1")
        ps_vol.metadata = client.V1ObjectMeta(name=name)
        spec = client.V1PersistentVolumeSpec(capacity={"storage": storage}, access_modes=accessModes, storage_class_name=name)
        if host_path:
            spec.host_path = client.V1HostPathVolumeSource(path=f'/mnt/data/{name}')
        ps_vol.spec = spec
        try:
            api_core.create_persistent_volume(body=ps_vol)
            LOG.info(f'Persistent Volume: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_core.patch_persistent_volume(name=name, body=ps_vol)
                LOG.info(f'PeVolume: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def destroy(self):
        """No need for the namespace, delete everything."""
        namespace_list = api_core.list_namespace(label_selector='role')
        namespaces = [x for x in namespace_list.items if x.metadata.labels['role'] == self._role]

        if len(namespaces) == 0:
            namespace = client.V1Namespace()
            namespace.metadata = client.V1ObjectMeta(name=self._namespace, labels={'role': self._role})
            api_core.delete_namespace(self._namespace)
            LOG.info('Namespace: {self._namespace} deleted.')
        else:
            LOG.info('Namespace: {self._namespace} exists.')
