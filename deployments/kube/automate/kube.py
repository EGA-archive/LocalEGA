import string
import secrets
import logging
import configparser
from base64 import b64encode
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pathlib import Path

# Logging
FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)

# Setup kubernete configuration
config.load_kube_config()
api_instance = client.CoreV1Api()


class ConfigGenerator:
    """Configuration generatorself.

    For when you need to do thing
    """



class LocalEGADeploy:
    """LocalEGA kubernetes deployment.

    Deployment configuration for LocalEGA to kubernetes.
    """

    def __init__(self, keys):
        """Setting things up."""
        self.keys = keys
        self._namespace = keys["namespace"]
        self._role = keys["role"]

    def default_namespace(self):
        """Create default namespace if not exists."""
        namespace_list = api_instance.list_namespace(label_selector='role')
        namespaces = [x for x in namespace_list.items if x.metadata.labels['role'] == self._role]

        if len(namespaces) == 0:
            namespace = client.V1Namespace()
            namespace.metadata = client.V1ObjectMeta(name=self._namespace, labels={'role': self._role})
            api_instance.create_namespace(self._namespace)
            LOG.info('Namespace: {self._namespace} created.')
        else:
            LOG.info('Namespace: {self._namespace} exists.')

    def _generate_secret(self, value):
        """"Generate secret of specifig value.

        .. note: If the value is of type integer it will generate a random of that value,
        else it will take that value.
        """
        if isinstance(value, int):
            secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(value)).encode("utf-8")
            return b64encode(secret).decode("utf-8")
        else:
            return b64encode(value.encode("utf-8")).decode("utf-8")

    # Default Secrets
    def default_secret(self, name, data, patch=False):
        """Create default secrets, if exists don't patch it."""
        sec_conf = client.V1Secret()
        sec_conf.metadata = client.V1ObjectMeta(name=name)
        sec_conf.type = "Opaque"
        sec_conf.data = {key: self._generate_secret(value) for (key, value) in data.items()}
        try:
            api_instance.create_namespaced_secret(namespace=self._namespace, body=sec_conf)
            LOG.info('Secret created: {name}.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_instance.patch_namespaced_secret(name=name, namespace=self._namespace, body=sec_conf)
                LOG.info('Pached secret: {name}.')
            else:
                LOG.error(f'Exception message: {e}')

    def default_config(self, name, data, patch=False):
        """Create default configMap for the deployment."""
        conf_map = client.V1ConfigMap()
        conf_map.metadata = client.V1ObjectMeta(name=name)
        conf_map.data = {}
        conf_map.data["test"] = data

        try:
            api_instance.create_namespaced_config_map(namespace=self._namespace, body=conf_map)
            LOG.info(f'ConfigMap: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_instance.patch_namespaced_config_map(name=name, namespace=self._namespace, body=conf_map)
                LOG.info('ConfigMap: {name} created.')
            else:
                LOG.error(f'Exception message: {e}')

    def destroy(self):
        """"No need for the namespace delete everything."""
        namespace_list = api_instance.list_namespace(label_selector='role')
        namespaces = [x for x in namespace_list.items if x.metadata.labels['role'] == self._role]

        if len(namespaces) == 0:
            namespace = client.V1Namespace()
            namespace.metadata = client.V1ObjectMeta(name=self._namespace, labels={'role': self._role})
            api_instance.delete_namespace(self._namespace)
            LOG.info('Namespace: {self._namespace} deleted.')
        else:
            LOG.info('Namespace: {self._namespace} exists.')


def main():
    """Where the magic happens."""
    _localega = {
        'namespace': 'test',
        'role': 'lega',
        'keyserver': 'keysrver',
        'inbox': 'inbox',
        'ingest': 'worker',
        's3': 's3',
        'broker': 'mq',
        'db': 'db',
        'verify': 'verify'
    }

    _here = Path(__file__).parent

    deploy = LocalEGADeploy(_localega)

    deploy.default_namespace()
    deploy.default_secret('lega-db-secret', {'postgres_password': 32})
    deploy.default_secret('s3-keys', {'access': 16, 'secret': 32})
    deploy.default_secret('lega-password', {'password': 32})
    with open(_here / 'config/ega.ini') as conf_file:
        data = conf_file.read()
        deploy.default_config('test', data, patch=True)


if __name__ == '__main__':
    main()
