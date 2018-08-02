import logging
from kube import kubernetes_deployment
import click

# Logging
FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


@click.command()
@click.option('--config', is_flag=True,
              help='Flag for generating configuration if does not exist, or generating a new one.')
@click.option('--deploy', multiple=True,
              help='Deploying the configuration secrets and pods. Options available: "all" (default), "secrets" or "sc", "services" or "svc", "configmap" or "cm" and "pods" or "pd".')
@click.option('--ns', default="testing", help='Deployment namespace, defaults to "testing".')
@click.option('--cega-ip', help='CEGA MQ IP, for fake CEGA MQ it is set up with a default for testing namespace.')
@click.option('--cega-pwd', help='CEGA MQ Password, for fake CEGA MQ it is set up with a default.')
@click.option('--key-pass', default='password', help='CEGA Users RSA key password.')
@click.option('--fake-cega', is_flag=True,
              help='Fake CEGA-Users and CEGA MQ.')
def main(config, deploy, ns, fake_cega, cega_ip, cega_pwd, key_pass):
    """Local EGA deployment script."""
    _localega = {
        'role': 'LocalEGA',
        'email': 'test@csc.fi',
        'services': {'keys': 'keys',
                     'inbox': 'inbox',
                     'ingest': 'ingest',
                     's3': 'minio',
                     'broker': 'mq',
                     'db': 'db',
                     'verify': 'verify'},
        # Only using one key
        'key': {'name': 'Test PGP',
                'comment': None,
                'expire': '30/DEC/19 08:00:00',
                'id': 'key.1'},
        'ssl': {'country': 'Finland', 'country_code': 'FI', 'location': 'Espoo', 'org': 'CSC'},
        'cega': {'user': 'lega',
                 'endpoint': 'http://cega-users.testing:8001/user/'}
    }

    kubernetes_deployment(_localega, config, deploy, ns, fake_cega, cega_ip, cega_pwd, key_pass)


if __name__ == '__main__':
    main()
