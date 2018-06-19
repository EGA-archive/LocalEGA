import string
import secrets
import logging
import configparser
from base64 import b64encode
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pathlib import Path
import os
import errno

from pgpy import PGPKey, PGPUID
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm

# Logging
FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)

# Setup kubernete configuration
config.load_kube_config()
api_core = client.CoreV1Api()
api_app = client.AppsV1Api()
api_beta_app = client.AppsV1beta1Api()


class ConfigGenerator:
    """Configuration generator.

    For when one needs to do create configuration files.
    """

    def __init__(self, config_path, name, email, namespace, services,):
        """Setting things up."""
        self.name = name
        self.email = email
        self.namespace = namespace
        self._key_service = services['keys']
        self._db_service = services['db']
        self._s3_service = services['s3']
        self._broker_service = services['broker']
        self._config_path = config_path

        if not os.path.exists(self._config_path):
            try:
                os.makedirs(self._config_path)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

    def _generate_pgp_pair(self, comment, passphrase, armor):
        """Generate PGP key pair to be used by keyserver."""
        # We need to specify all of our preferences because PGPy doesn't have any built-in key preference defaults at this time.
        # This example is similar to GnuPG 2.1.x defaults, with no expiration or preferred keyserver
        key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
        uid = PGPUID.new(self.name, email=self.email, comment=comment)
        key.add_uid(uid,
                    usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
                    hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512, HashAlgorithm.SHA224],
                    ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
                    compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP, CompressionAlgorithm.Uncompressed])

        # Protecting the key
        key.protect(passphrase, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
        pub_data = str(key.pubkey) if armor else bytes(key.pubkey)  # armored or not
        sec_data = str(key) if armor else bytes(key)  # armored or not

        return (pub_data, sec_data)

    def create_conf_shared(self, scheme=None):
        """Creating default configuration file, namely ```conf.ini`` file."""
        config = configparser.RawConfigParser()
        file_flag = 'w'
        scheme = scheme if scheme else 'svc.cluster.local'
        # Apparently this is the only way the log is actually loaded. To investigate.
        config.set('DEFAULT', 'log', '/usr/lib/python3.6/site-packages/lega/conf/loggers/console.yaml')
        # keyserver
        config.add_section('keyserver')
        config.set('keyserver', 'port', '8443')
        # quality control
        config.add_section('quality_control')
        config.set('quality_control', 'keyserver_endpoint', f'https://{self._key_service}.{self.namespace}.{scheme}:8443/retrieve/%s/private')
        # inbox
        config.add_section('inbox')
        config.set('inbox', 'location', '/ega/inbox/%s')
        config.set('inbox', 'mode', '2750')
        # vault
        config.add_section('vault')
        config.set('vault', 'driver', 'S3Storage')
        config.set('vault', 'url', f'http://{self._s3_service}.{self.namespace}.{scheme}:9000')
        # outgestion
        config.add_section('outgestion')
        config.set('outgestion', 'keyserver_endpoint',  f'https://{self._key_service}.{self.namespace}.{scheme}:8443/retrieve/%s/private')
        # broker
        config.add_section('broker')
        config.set('broker', 'host', f'{self._broker_service}.{self.namespace}.{scheme}')
        config.set('broker', 'connection_attempts', '30')
        config.set('broker', 'retry_delay', '10')
        # Postgres
        config.add_section('postgres')
        config.set('postgres', 'host', f'{self._db_service}.{self.namespace}.{scheme}')
        config.set('postgres', 'user', 'lega')
        config.set('postgres', 'try', '30')

        with open(self._config_path / 'conf.ini', file_flag) as configfile:
            config.write(configfile)

    def add_conf_key(self, expire, file_name, comment, passphrase, armor=True, active=False):
        """Create default configuration for keyserver.

        .. note: Information for the key is provided as dictionary for ``key_data``, and should be in the format ``{'comment': '','passphrase': None, 'armor': True}. If a passphrase is not provided it will generated.``
        """
        _generate_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(32))
        _passphrase = passphrase if passphrase else _generate_secret
        comment = comment if comment else "Generated for use in LocalEGA."
        config = configparser.RawConfigParser()
        file_flag = 'w'
        if os.path.exists(self._config_path / 'keys.ini'):
            config.read(self._config_path / 'keys.ini')
        if active:
            config.set('DEFAULT', 'active', file_name)
        if not config.has_section(file_name):
            pub, sec = self._generate_pgp_pair(comment, _passphrase, armor)
            config.add_section(file_name)
            config.set(file_name, 'path', '/etc/ega/pgp/%s' % file_name)
            config.set(file_name, 'passphrase', _passphrase)
            config.set(file_name, 'expire', expire)
            with open(self._config_path / f'{file_name}.pub', 'w' if armor else 'bw') as f:
                f.write(pub)
            with open(self._config_path / f'{file_name}.sec', 'w' if armor else 'bw') as f:
                f.write(sec)
        with open(self._config_path / 'keys.ini', file_flag) as configfile:
            config.write(configfile)


class LocalEGADeploy:
    """LocalEGA kubernetes deployment.

    Deployment configuration for LocalEGA to kubernetes.
    """

    def __init__(self, keys):
        """Setting things up."""
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
            api_core.create_namespace(self._namespace)
            LOG.info(f'Namespace: {self._namespace} created.')
        else:
            LOG.info(f'Namespace: {self._namespace} exists.')

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
        conf_map.data = {}
        conf_map.data["test"] = data

        try:
            api_core.create_namespaced_config_map(namespace=self._namespace, body=conf_map)
            LOG.info(f'ConfigMap: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_core.patch_namespaced_config_map(name=name, namespace=self._namespace, body=conf_map)
                LOG.info(f'ConfigMap: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def upload_deploy(self, name, data, patch=False):
        """Create and upload deployment, patch option also available."""
        deploy = client.AppsV1beta1Deployment()
        try:
            api_beta_app.create_namespaced_deployment(namespace=self._namespace, body=deploy)
            LOG.info(f'Deployment: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_app.patch_namespaced_deployement(name=name, namespace=self._namespace, body=deploy)
                LOG.info(f'Deployment: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def upload_service(self, name, data, patch=False):
        """Create and upload service, patch option also available."""
        svc_conf = client.V1Service()
        try:
            api_core.create_namespaced_service(namespace=self._namespace, body=svc_conf)
            LOG.info(f'Service: {name} created.')
        except ApiException as e:
            if e.status == 409 and patch:
                api_core.patch_namespaced_service(name=name, namespace=self._namespace, body=svc_conf)
                LOG.info(f'Service: {name} patched.')
            else:
                LOG.error(f'Exception message: {e}')

    def upload_stateful_set(self, name, data, patch=False):
        """Create and upload StatefulSet, patch option also available."""
        sts_conf = client.V1beta1StatefulSet()
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
        """"No need for the namespace delete everything."""
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
        'namespace': 'test',
        'role': 'lega',
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

    configure = ConfigGenerator(config_dir, 'Test PGP', 'test@csc.fi',  _localega['namespace'], _localega['services'])

    configure.create_conf_shared()
    # configure.add_conf_key('1', 'key.1', comment=None, passphrase=None, armor=True, active=False)
    configure.add_conf_key('1', 'key.2', comment=None, passphrase=None, armor=True, active=True)

    # deploy = LocalEGADeploy(_localega)
    #
    # deploy.create_namespace()
    # deploy.upload_secret('lega-db-secret', {'postgres_password': 32})
    # deploy.upload_secret('s3-keys', {'access': 16, 'secret': 32})
    # deploy.upload_secret('lega-password', {'password': 32})
    # with open(_here / 'config/ega.ini') as conf_file:
    #     data = conf_file.read()
    #     deploy.upload_config('test', data, patch=True)


if __name__ == '__main__':
    main()
