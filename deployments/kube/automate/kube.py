import string
import secrets
import logging
from base64 import b64encode
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pathlib import Path
from configure import ConfigGenerator


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

    def __init__(self, keys):
        """Set things up."""
        self.keys = keys
        self._namespace = keys["namespace"]
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
    def upload_secret(self, name, data, patch=False):
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

    def upload_config(self, name, data, patch=False):
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

    def upload_deploy(self, name, image, command, env, vmounts, volumes, ports=None, replicas=1, patch=False):
        """Create and upload deployment, patch option also available."""
        deploy = client.V1Deployment(kind="Deployment", api_version="apps/v1")
        deploy.metadata = client.V1ObjectMeta(name=name)
        container = client.V1Container(name=name, image=image, image_pull_policy="IfNotPresent",
                                       volume_mounts=vmounts, command=command, env=env)
        if ports:
            container.ports = list(map(lambda x: client.V1ContainerPort(container_port=x), ports))
        template = client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels={"app": name}),
                                            spec=client.V1PodSpec(containers=[container], volumes=volumes, restart_policy="OnFailure"))
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

    def upload_service(self, name, ports, patch=False):
        """Create and upload service, patch option also available."""
        svc_conf = client.V1Service(kind="Service", api_version="v1")
        svc_conf.metadata = client.V1ObjectMeta(name=name)
        spec = client.V1ServiceSpec(selector={"app": name}, ports=ports)
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

    def upload_stateful_set(self, name, image, command, ports, env, vmounts, volumes, replicas=1, patch=False):
        """Create and upload StatefulSet, patch option also available."""
        sts_conf = client.V1StatefulSet(kind="StatefulSet", api_version="v1")
        sts_conf.metadata = client.V1ObjectMeta(name=name)
        container = client.V1Container(name=name, image=image, image_pull_policy="IfNotPresent",
                                       volume_mounts=vmounts, command=command, env=env)
        if ports:
            container.ports = list(map(lambda x: client.V1ContainerPort(container_port=x), ports))
        template = client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels={"app": name}),
                                            spec=client.V1PodSpec(containers=[container], volumes=volumes, restart_policy="OnFailure"))
        spec = client.V1StatefulSetSpec(replicas=replicas, template=template, selector=client.V1LabelSelector(match_labels={"app": name}))
        sts_conf.spec = spec
        try:
            api_beta_app.create_namespaced_service(namespace=self._namespace, body=sts_conf)
            LOG.info(f'Service: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_app.patch_namespaced_service(name=name, namespace=self._namespace, body=sts_conf)
                LOG.info(f'Service: {name} patched.')
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


def main():
    """Where the magic happens."""
    _localega = {
        'namespace': 'testing',
        'role': 'testing',
        'services': {'keys': 'lega-keyserver',
                     'inbox': 'lega-inbox',
                     'ingest': 'lega-ingest',
                     's3': 'minio',
                     'broker': 'lega-mq',
                     'db': 'lega-db',
                     'verify': 'lega-verify'}
    }

    _here = Path(__file__).parent
    config_dir = _here / 'config'

    # Generate Configuration
    config = ConfigGenerator(config_dir, 'Test PGP', 'test@csc.fi',  _localega['namespace'], _localega['services'])

    config.create_conf_shared()
    config.add_conf_key('30/DEC/19 08:00:00', 'key.1', comment=None, passphrase=None, armor=True, active=False)
    config.add_conf_key('30/DEC/19 08:00:00', 'key.2', comment=None, passphrase=None, armor=True, active=True)
    config.generate_ssl_certs(country="Finland", country_code="FI", location="Espoo", org="CSC", email="test@csc.fi")

    deploy_lega = LocalEGADeploy(_localega)

    deploy_lega.create_namespace()
    # Create Secrets
    deploy_lega.upload_secret('lega-db-secret', {'postgres_password': 32})
    deploy_lega.upload_secret('s3-keys', {'access': 16, 'secret': 32})
    deploy_lega.upload_secret('lega-password', {'password': 32})
    # Read conf from files
    with open(_here / 'scripts/db.sql') as sql_init:
        init_sql = sql_init.read()

    with open(_here / 'config/conf.ini') as conf_file:
        data_conf = conf_file.read()

    with open(_here / 'config/keys.ini') as keys_file:
        data_keys = keys_file.read()

    with open(_here / 'config/key.1.sec') as key_file:
        key1_data = key_file.read()

    with open(_here / 'config/key.2.sec') as key_file:
        key2_data = key_file.read()

    with open(_here / 'config/ssl.key') as cert_key_file:
        ssl_key_data = cert_key_file.read()

    with open(_here / 'config/ssl.cert') as cert_file:
        cert_data = cert_file.read()

    # Upload Configuration Maps
    deploy_lega.upload_config('initsql', {'db.sql': init_sql})
    deploy_lega.upload_config('lega-config', {'conf.ini': data_conf}, patch=True)
    deploy_lega.upload_config('lega-keyserver-config', {'keys.ini': data_keys}, patch=True)
    deploy_lega.upload_secret('keyserver-secret', {'key1.sec': key1_data, 'key2.sec': key2_data,
                                                   'ssl.cert': cert_data, 'ssl.key': ssl_key_data}, patch=True)
    deploy_lega.upload_config('lega-db-config', {'user': 'lega', 'dbname': 'lega'})

    # Setting ENV variables and Volumes
    env_acc_s3 = client.V1EnvVar(name="S3_ACCESS_KEY",
                                 value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='s3-keys',
                                                                                                            key="access")))
    env_sec_s3 = client.V1EnvVar(name="S3_SECRET_KEY",
                                 value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='s3-keys',
                                                                                                            key="secret")))
    env_db_pass = client.V1EnvVar(name="POSTGRES_PASSWORD",
                                  value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='lega-db-secret',
                                                                                                             key="postgres_password")))
    env_db_user = client.V1EnvVar(name="POSTGRES_USER",
                                  value_from=client.V1EnvVarSource(config_map_key_ref=client.V1ConfigMapKeySelector(name='lega-db-config',
                                                                                                                    key="user")))
    env_db_name = client.V1EnvVar(name="POSTGRES_DB",
                                  value_from=client.V1EnvVarSource(config_map_key_ref=client.V1ConfigMapKeySelector(name='lega-db-config',
                                                                                                                    key="dbname")))
    env_lega_pass = client.V1EnvVar(name="LEGA_PASSWORD",
                                    value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='lega-password',
                                                                                                               key="password")))
    mount_keys = client.V1VolumeMount(name="keyserver-conf", mount_path='/etc/ega')
    mount_db_data = client.V1VolumeMount(name="data", mount_path='/var/lib/postgresql/data', read_only=False)
    mound_db_init = client.V1VolumeMount(name="initsql", mount_path='/docker-entrypoint-initdb.d')

    pmap_ini_conf = client.V1VolumeProjection(config_map=client.V1ConfigMapProjection(name="lega-config",
                                                                                      items=[client.V1KeyToPath(key="conf.ini", path="conf.ini", mode=0o744)]))
    pmap_ini_keys = client.V1VolumeProjection(config_map=client.V1ConfigMapProjection(name="lega-keyserver-config",
                                                                                      items=[client.V1KeyToPath(key="keys.ini", path="keys.ini", mode=0o744)]))
    sec_keys = client.V1VolumeProjection(secret=client.V1SecretProjection(name="keyserver-secret",
                                                                          items=[client.V1KeyToPath(key="key1.sec", path="pgp/key.1"),
                                                                                 client.V1KeyToPath(key="key2.sec", path="pgp/key.2"), client.V1KeyToPath(key="ssl.cert", path="ssl.cert"), client.V1KeyToPath(key="ssl.key", path="ssl.key")]))
    volume_db = client.V1Volume(name="data", persistent_volume_claim=client.V1PersistentVolumeClaim(),)
    volume_db_init = client.V1Volume(name="init", config_map=client.V1ConfigMapVolumeSource(name="initdb", ))
    volume_keys = client.V1Volume(name="keyserver-conf",
                                  projected=client.V1ProjectedVolumeSource(sources=[pmap_ini_conf, pmap_ini_keys, sec_keys]))

    ports_db = client.V1ServicePort(protocol="TCP", port=5432, target_port=5432)

    # Deploy LocalEGA
    deploy_lega.upload_deploy('keyserver', 'nbisweden/ega-base:latest',
                              ["gosu", "lega", "ega-keyserver", "--keys", "/etc/ega/keys.ini"],
                              [env_db_pass, env_lega_pass], [mount_keys], [volume_keys], ports=[8443], patch=True)
    deploy_lega.upload_deploy('db', 'postgres:9.6', None, [env_db_pass, env_db_user, env_db_name],
                              [mount_db_data, mound_db_init], [volume_db, volume_db_init], ports=[5432])

    deploy_lega.upload_service('db', [ports_db], patch=True)


if __name__ == '__main__':
    main()
