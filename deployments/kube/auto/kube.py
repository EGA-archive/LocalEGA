import string
import secrets
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pathlib import Path
from configure import ConfigGenerator
from hashlib import md5
from base64 import b64encode, b64decode
import click

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

    def read_secret(self, name):
        """Read secret."""
        api_response = ''
        try:
            api_response = api_core.read_namespaced_secret(name, self._namespace, exact=True, export=True)
            LOG.info(f'Secret: {name} read.')
        except ApiException as e:
            LOG.error(f'Exception message: {e}')
        else:
            return api_response

    def config_map(self, name, data, binary=False, patch=False):
        """Create and upload configMap, patch option also available."""
        conf_map = client.V1ConfigMap()
        conf_map.metadata = client.V1ObjectMeta(name=name)
        if not binary:
            conf_map.data = data
        else:
            conf_map.binary_data = data

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

    def horizontal_scale(self, name, pod_name, pod_kind, max, metric):
        """Create horizontal pod scaller, based on metric."""
        api = client.AutoscalingV1Api()
        pd_scale = client.V1HorizontalPodAutoscaler()
        pd_scale.metadata = client.V1ObjectMeta(name=name)
        target = client.V1CrossVersionObjectReference(name=pod_name, kind=pod_kind)
        spec = client.V1HorizontalPodAutoscalerSpec(min_replicas=1, max_replicas=max, scale_target_ref=target)
        status = client.V1HorizontalPodAutoscalerStatus(current_replicas=1, desired_replicas=2)
        pd_scale.spec = spec
        pd_scale.status = status
        try:
            api.create_namespaced_horizontal_pod_autoscaler(namespace=self._namespace, body=pd_scale)
            LOG.info(f'Persistent Volume: {name} created.')
        except ApiException as e:
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


def kubernetes_deployment(_localega, config, deploy, ns, fake_cega, cega_ip, cega_pwd, key_pass):
    """Wrap all the kubernetes settings."""
    val = set(["secrets", "sc", "configmap", "cm", "pods", "pd", "services", "svc", "all"])
    set_sc = set(["secrets", "sc", "all"])
    set_cm = set(["configmap", "cm", "all"])
    set_pd = set(["pods", "pd", "all"])
    set_sv = set(["services", "svc", "all"])

    _here = Path(__file__).parent
    config_dir = _here / 'config'

    # Generate Configuration
    conf = ConfigGenerator(config_dir,  _localega['key']['name'],  _localega['email'],  ns, _localega['services'])
    deploy_lega = LocalEGADeploy(_localega, ns)
    if fake_cega:
        cega_pass, cega_config_mq, cega_defs_mq = conf.generate_mq_auth()
        cega_address = f"amqp://{_localega['cega']['user']}:{cega_pass}@cega-mq.{ns}:5672/{_localega['cega']['user']}"
    else:
        cega_address = f"amqp://{_localega['cega']['user']}:{cega_pwd}@{cega_ip}:5672/{_localega['cega']['user']}"

    if config:
        conf.create_conf_shared()
        conf.add_conf_key(_localega['key']['expire'], _localega['key']['id'], comment=_localega['key']['comment'],
                          passphrase=None, armor=True, active=True)
        ssl_cert, ssl_key = conf.generate_ssl_certs(country=_localega['ssl']['country'], country_code=_localega['ssl']['country_code'],
                                                    location=_localega['ssl']['location'], org=_localega['ssl']['org'], email=_localega['email'])

    # Setting ENV variables and Volumes
    env_cega_api = client.V1EnvVar(name="CEGA_ENDPOINT", value=f"{_localega['cega']['endpoint']}")
    env_inbox_mq = client.V1EnvVar(name="BROKER_HOST", value=f"{_localega['services']['broker']}.{ns}")
    env_inbox_port = client.V1EnvVar(name="INBOX_PORT", value="2222")
    env_db_data = client.V1EnvVar(name="PGDATA", value="/var/lib/postgresql/data/pgdata")
    env_cega_mq = client.V1EnvVar(name="CEGA_CONNECTION",
                                  value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='cega-connection',
                                                                                                             key="address")))
    env_cega_creds = client.V1EnvVar(name="CEGA_ENDPOINT_CREDS",
                                     value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='cega-creds',
                                                                                                                key="credentials")))
    env_acc_minio = client.V1EnvVar(name="MINIO_ACCESS_KEY",
                                    value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='s3-keys',
                                                                                                               key="access")))
    env_sec_minio = client.V1EnvVar(name="MINIO_SECRET_KEY",
                                    value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='s3-keys',
                                                                                                               key="secret")))
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
    env_keys_pass = client.V1EnvVar(name="KEYS_PASSWORD",
                                    value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='keys-password',
                                                                                                               key="password")))
    mount_config = client.V1VolumeMount(name="config", mount_path='/etc/ega')
    mount_inbox = client.V1VolumeMount(name="inbox", mount_path='/ega/inbox')
    mount_mq_temp = client.V1VolumeMount(name="mq-temp", mount_path='/temp')
    mount_mq_rabbitmq = client.V1VolumeMount(name="rabbitmq", mount_path='/etc/rabbitmq')
    mount_mq_script = client.V1VolumeMount(name="mq-entrypoint", mount_path='/script')
    mount_db_data = client.V1VolumeMount(name="data", mount_path='/var/lib/postgresql/data', read_only=False)
    mound_db_init = client.V1VolumeMount(name="initsql", mount_path='/docker-entrypoint-initdb.d')
    mount_minio = client.V1VolumeMount(name="data", mount_path='/data')

    pmap_ini_conf = client.V1VolumeProjection(config_map=client.V1ConfigMapProjection(name="lega-config",
                                                                                      items=[client.V1KeyToPath(key="conf.ini", path="conf.ini", mode=0o744)]))
    pmap_ini_keys = client.V1VolumeProjection(config_map=client.V1ConfigMapProjection(name="lega-keyserver-config",
                                                                                      items=[client.V1KeyToPath(key="keys.ini.enc",
                                                                                                                path="keys.ini.enc", mode=0o744)]))
    sec_keys = client.V1VolumeProjection(secret=client.V1SecretProjection(name="keyserver-secret",
                                                                          items=[client.V1KeyToPath(key="key1.sec", path="pgp/key.1"), client.V1KeyToPath(key="ssl.cert", path="ssl.cert"), client.V1KeyToPath(key="ssl.key", path="ssl.key")]))
    if set.intersection(set(deploy), val) or fake_cega:
        deploy_lega.create_namespace()
        deploy_lega.config_secret('cega-creds', {'credentials': 32})
    else:
        click.echo("Option not recognised.")
    if set.intersection(set(deploy), set_sc):
        # Create Secrets
        deploy_lega.config_secret('cega-connection', {'address': cega_address})
        deploy_lega.config_secret('lega-db-secret', {'postgres_password': 32})
        deploy_lega.config_secret('s3-keys', {'access': 16, 'secret': 32})
        deploy_lega.config_secret('lega-password', {'password': 32})
        deploy_lega.config_secret('keys-password', {'password': 32})
        with open(_here / 'config/key.1.sec') as key_file:
            key1_data = key_file.read()

        deploy_lega.config_secret('keyserver-secret', {'key1.sec': key1_data,
                                                       'ssl.cert': ssl_cert, 'ssl.key': ssl_key})
    if set.intersection(set(deploy), set_cm):
        # Read conf from files
        with open('../../../extras/db.sql') as sql_init:
            init_sql = sql_init.read()

        with open(_here / 'scripts/mq.sh') as mq_init:
            init_mq = mq_init.read()

        with open('../../docker/images/mq/defs.json') as mq_defs:
            defs_mq = mq_defs.read()

        with open('../../docker/images/mq/rabbitmq.config') as mq_config:
            config_mq = mq_config.read()

        with open(_here / 'config/conf.ini') as conf_file:
            data_conf = conf_file.read()

        with open(_here / 'config/keys.ini') as keys_file:
            data_keys = keys_file.read()

        secret = deploy_lega.read_secret('keys-password')
        enc_keys = conf.aes_encrypt(b64decode(secret.to_dict()['data']['password'].encode('utf-8')), data_keys.encode('utf-8'), md5)

        with open(_here / 'config/keys.ini.enc', 'w') as enc_file:
            enc_file.write(b64encode(enc_keys).decode('utf-8'))

        # Upload Configuration Maps
        deploy_lega.config_map('initsql', {'db.sql': init_sql})
        deploy_lega.config_map('mq-config', {'defs.json': defs_mq, 'rabbitmq.config': config_mq})
        deploy_lega.config_map('mq-entrypoint', {'mq.sh': init_mq})
        deploy_lega.config_map('lega-config', {'conf.ini': data_conf})
        deploy_lega.config_map('lega-keyserver-config', {'keys.ini.enc': b64encode(enc_keys).decode('utf-8')}, binary=True)
        deploy_lega.config_map('lega-db-config', {'user': 'lega', 'dbname': 'lega'})

    if set.intersection(set(deploy), set_pd):
        # Volumes
        deploy_lega.persistent_volume("postgres", "0.5Gi", accessModes=["ReadWriteMany"])
        deploy_lega.persistent_volume("rabbitmq", "0.5Gi")
        deploy_lega.persistent_volume("inbox", "0.5Gi", accessModes=["ReadWriteMany"])
        deploy_lega.persistent_volume_claim("db-storage", "postgres", "0.5Gi", accessModes=["ReadWriteMany"])
        deploy_lega.persistent_volume_claim("mq-storage", "rabbitmq", "0.5Gi")
        deploy_lega.persistent_volume_claim("inbox", "inbox", "0.5Gi", accessModes=["ReadWriteMany"])
        volume_db = client.V1Volume(name="data", persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="db-storage"))
        volume_rabbitmq = client.V1Volume(name="rabbitmq",
                                          persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="mq-storage"))
        volume_db_init = client.V1Volume(name="initsql", config_map=client.V1ConfigMapVolumeSource(name="initsql"))
        volume_mq_temp = client.V1Volume(name="mq-temp", config_map=client.V1ConfigMapVolumeSource(name="mq-config"))
        volume_mq_script = client.V1Volume(name="mq-entrypoint", config_map=client.V1ConfigMapVolumeSource(name="mq-entrypoint",
                                                                                                           default_mode=0o744))
        volume_config = client.V1Volume(name="config", config_map=client.V1ConfigMapVolumeSource(name="lega-config"))
        # volume_ingest = client.V1Volume(name="ingest-conf", config_map=client.V1ConfigMapVolumeSource(name="lega-config"))
        volume_inbox = client.V1Volume(name="inbox", persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="inbox"))
        volume_keys = client.V1Volume(name="config",
                                      projected=client.V1ProjectedVolumeSource(sources=[pmap_ini_conf, pmap_ini_keys, sec_keys]))

        pvc_minio = client.V1PersistentVolumeClaim(metadata=client.V1ObjectMeta(name="data"),
                                                   spec=client.V1PersistentVolumeClaimSpec(access_modes=["ReadWriteOnce"],
                                                                                           resources=client.V1ResourceRequirements(requests={"storage": "10Gi"})))
        # Deploy LocalEGA Pods
        deploy_lega.deployment('keys', 'nbisweden/ega-base:latest',
                               ["ega-keyserver", "--keys", "/etc/ega/keys.ini.enc"],
                               [env_lega_pass, env_keys_pass], [mount_config], [volume_keys], ports=[8443], patch=True)
        deploy_lega.deployment('db', 'postgres:9.6', None, [env_db_pass, env_db_user, env_db_name, env_db_data],
                               [mount_db_data, mound_db_init], [volume_db, volume_db_init], ports=[5432])
        deploy_lega.deployment('ingest', 'nbisweden/ega-base:latest', ["ega-ingest"],
                               [env_lega_pass, env_acc_s3, env_sec_s3, env_db_pass],
                               [mount_config, mount_inbox], [volume_config, volume_inbox])

        deploy_lega.stateful_set('minio', 'minio/minio:latest', None, [env_acc_minio, env_sec_minio],
                                 [mount_minio], None, args=["server", "/data"], vol_claims=[pvc_minio], ports=[9000])

        deploy_lega.stateful_set('verify', 'nbisweden/ega-base:latest', ["ega-verify"],
                                 [env_acc_s3, env_sec_s3, env_lega_pass, env_db_pass], [mount_config], [volume_config])

        deploy_lega.stateful_set('mq', 'rabbitmq:3.6.14-management', ["/script/mq.sh"],
                                 [env_cega_mq], [mount_mq_temp, mount_mq_script, mount_mq_rabbitmq],
                                 [volume_mq_temp, volume_mq_script, volume_rabbitmq],
                                 ports=[15672, 5672, 4369, 25672])
        deploy_lega.stateful_set('inbox', 'nbisweden/ega-mina-inbox:latest', None,
                                 [env_inbox_mq, env_cega_api, env_cega_creds, env_inbox_port],
                                 [mount_inbox], [volume_inbox], ports=[2222])

    # Ports
    ports_db = [client.V1ServicePort(protocol="TCP", port=5432, target_port=5432)]
    ports_inbox = [client.V1ServicePort(protocol="TCP", port=2222, target_port=2222)]
    ports_s3 = [client.V1ServicePort(name="web", protocol="TCP", port=9000)]
    ports_keys = [client.V1ServicePort(protocol="TCP", port=8443, target_port=8443)]
    ports_mq_management = [client.V1ServicePort(name="http", protocol="TCP", port=15672, target_port=15672)]
    ports_mq = [client.V1ServicePort(name="amqp", protocol="TCP", port=5672, target_port=5672),
                client.V1ServicePort(name="epmd", protocol="TCP", port=4369, target_port=4369),
                client.V1ServicePort(name="rabbitmq-dist", protocol="TCP", port=25672, target_port=25672)]

    if set.intersection(set(deploy), set_sv):

        # Deploy Services
        deploy_lega.service('db', ports_db)
        deploy_lega.service('mq-management', ports_mq_management, pod_name="mq", type="NodePort")
        deploy_lega.service('mq', ports_mq)
        deploy_lega.service('keys', ports_keys)
        deploy_lega.service('inbox', ports_inbox, type="NodePort")
        deploy_lega.service('minio', ports_s3)  # Headless
        deploy_lega.service('minio-service', ports_s3, pod_name="minio", type="LoadBalancer")

    if set.intersection(set(deploy), set(["scale"])):
        metric_cpu = client.V2beta1MetricSpec(type="Resource",
                                              resource=client.V2beta1ResourceMetricSource(name="cpu", target_average_utilization=50))
        deploy_lega.horizontal_scale("ingest", "ingest", "Deployment", 5, [metric_cpu])

    if fake_cega:
        deploy_fake_cega(deploy_lega, _here, conf, cega_config_mq, cega_defs_mq,  ports_mq, ports_mq_management, key_pass)


def deploy_fake_cega(deploy_lega, _here, conf, cega_config_mq, cega_defs_mq, ports_mq, ports_mq_management, key_pass):
    """Deploy the Fake CEGA."""
    user_pub = conf.generate_user_auth(key_pass)
    with open(_here / 'scripts/server.py') as users_init:
        init_users = users_init.read()

    with open('../../docker/images/cega/users.html') as user_list:
        users = user_list.read()

    with open(_here / 'scripts/cega-mq.sh') as ceg_mq_init:
        cega_init_mq = ceg_mq_init.read()

    deploy_lega.config_map('users-config', {'server.py': init_users, 'users.html': users,
                           'ega-box-999.yml': f'---\npubkey: {user_pub}'})
    env_users_inst = client.V1EnvVar(name="LEGA_INSTANCES", value="lega")
    env_users_creds = client.V1EnvVar(name="CEGA_REST_lega_PASSWORD",
                                      value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name='cega-creds',
                                                                                                                 key="credentials")))
    mount_users = client.V1VolumeMount(name="users-config", mount_path='/cega')
    users_map = client.V1ConfigMapProjection(name="users-config",
                                             items=[client.V1KeyToPath(key="server.py", path="server.py"),
                                                    client.V1KeyToPath(key="users.html", path="users.html"),
                                                    client.V1KeyToPath(key="ega-box-999.yml", path="users/ega-box-999.yml"),
                                                    client.V1KeyToPath(key="ega-box-999.yml", path="users/lega/ega-box-999.yml")])
    users_vol = client.V1VolumeProjection(config_map=users_map)
    volume_users = client.V1Volume(name="users-config",
                                   projected=client.V1ProjectedVolumeSource(sources=[users_vol]))

    deploy_lega.config_map('cega-mq-entrypoint', {'cega-mq.sh': cega_init_mq})
    deploy_lega.config_map('cega-mq-config', {'defs.json': cega_defs_mq, 'rabbitmq.config': cega_config_mq})
    deploy_lega.persistent_volume("cega-rabbitmq", "1Gi")
    deploy_lega.persistent_volume_claim("cega-mq-storage", "cega-rabbitmq", "1Gi")
    mount_cega_temp = client.V1VolumeMount(name="cega-mq-temp", mount_path='/temp')
    mount_cega_rabbitmq = client.V1VolumeMount(name="cega-rabbitmq", mount_path='/etc/rabbitmq')
    volume_cega_temp = client.V1Volume(name="cega-mq-temp", config_map=client.V1ConfigMapVolumeSource(name="cega-mq-config"))
    volume_cega_rabbitmq = client.V1Volume(name="cega-rabbitmq",
                                           persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="cega-mq-storage"))
    mount_mq_cega = client.V1VolumeMount(name="cega-mq-entrypoint", mount_path='/script')
    volume_mq_cega = client.V1Volume(name="cega-mq-entrypoint", config_map=client.V1ConfigMapVolumeSource(name="cega-mq-entrypoint",
                                                                                                          default_mode=0o744))

    deploy_lega.stateful_set('cega-mq', 'rabbitmq:3.6.14-management', ["/script/cega-mq.sh"], None,
                             [mount_cega_temp, mount_mq_cega, mount_cega_rabbitmq],
                             [volume_cega_temp, volume_mq_cega, volume_cega_rabbitmq],
                             ports=[15672, 5672, 4369, 25672])

    deploy_lega.deployment('cega-users', 'python:3.6-alpine3.7', ["/bin/sh", "-c"],
                           [env_users_inst, env_users_creds],
                           [mount_users], [volume_users],
                           args=["pip install PyYAML aiohttp aiohttp_jinja2; python /cega/server.py"],
                           ports=[8001])
    ports_users = [client.V1ServicePort(protocol="TCP", port=8001, target_port=8001)]
    deploy_lega.service('cega-mq', ports_mq, type="NodePort")
    deploy_lega.service('cega-mq-management', ports_mq_management, pod_name="cega-mq", type="NodePort")
    deploy_lega.service('cega-users', ports_users, type="NodePort")
