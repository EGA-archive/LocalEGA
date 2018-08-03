import paramiko
import os
import pika
import secrets
from hashlib import md5
import json
import string
import uuid
import logging
from legacryptor.crypt4gh import encrypt
import pgpy
import argparse


FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def open_ssh_connection(hostname, user, key_path, key_pass='password', port=2222):
    """Open an ssh connection, test function."""
    try:
        client = paramiko.SSHClient()
        k = paramiko.RSAKey.from_private_key_file(key_path, password=key_pass)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, allow_agent=False, look_for_keys=False, port=port, timeout=0.3, username=user, pkey=k)
        LOG.info(f'ssh connected to {hostname}:{port} with {user}')
    except paramiko.BadHostKeyException as e:
        LOG.error(f'Something went wrong {e}')
        raise Exception('BadHostKeyException on ' + hostname)
    except paramiko.AuthenticationException as e:
        LOG.error(f'Something went wrong {e}')
        raise Exception('AuthenticationException on ' + hostname)
    except paramiko.SSHException as e:
        LOG.error(f'Something went wrong {e}')
        raise Exception('SSHException on ' + hostname)

    return client


def sftp_upload(hostname, user, file_path, key_path, key_pass='password', port=2222):
    """SFTP Client file upload."""
    try:
        k = paramiko.RSAKey.from_private_key_file(key_path, password=key_pass)
        transport = paramiko.Transport((hostname, port))
        transport.connect(username=user, pkey=k)
        LOG.info(f'sftp connected to {hostname}:{port} with {user}')
        sftp = paramiko.SFTPClient.from_transport(transport)
        filename, _ = os.path.splitext(file_path)
        sftp.put(file_path, f'{filename}.c4ga')
        LOG.info(f'file uploaded {filename}.c4ga')
    except Exception as e:
        LOG.error(f'Something went wrong {e}')
        raise e
    finally:
        LOG.debug('sftp done')
        transport.close()


def submit_cega(connection, user, file_path, c4ga_md5, file_md5=None):
    """Submit message to CEGA along with."""
    stableID = ''.join(secrets.choice(string.digits) for i in range(16))
    message = {'user': user, 'filepath': file_path, 'stable_id': f'EGA_{stableID}'}
    if c4ga_md5:
        message['encrypted_integrity'] = {'checksum': c4ga_md5, 'algorithm': 'md5'}
    if file_md5:
        message['unencrypted_integrity'] = {'checksum': file_md5, 'algorithm': 'md5'}

    try:
        parameters = pika.URLParameters(connection)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.basic_publish(exchange='localega.v1', routing_key='files',
                              body=json.dumps(message),
                              properties=pika.BasicProperties(correlation_id=str(uuid.uuid4()),
                                                              content_type='application/json',
                                                              delivery_mode=2))

        connection.close()
        LOG.info('Message published to CentralEGA')
    except Exception as e:
        LOG.error(f'Something went wrong {e}')
        raise e


def encrypt_file(file_path, pubkey):
    """Encrypt file and extract its md5."""
    file_size = os.path.getsize(file_path)
    filename, _ = os.path.splitext(file_path)
    output_base = os.path.basename(filename)
    c4ga_md5 = None
    output_file = os.path.expanduser(f'{output_base}.c4ga')

    try:
        encrypt(pubkey, open(file_path, 'rb'), file_size, open(f'{output_base}.c4ga', 'wb'))
        with open(output_file, 'rb') as read_file:
            c4ga_md5 = md5(read_file.read()).hexdigest()
        LOG.info(f'File {output_base}.c4ga is the encrypted file with md5: {c4ga_md5}.')
    except Exception as e:
        LOG.error(f'Something went wrong {e}')
        raise e
    return (output_file, c4ga_md5)


def main():
    """Do the sparkles and fireworks."""
    parser = argparse.ArgumentParser(description="Encrypting, uploading to inbox and sending message to CEGA.")

    parser.add_argument('input', help='Input file to be encrypted.')
    parser.add_argument('--u', help='Username to identify the elixir.', default='ega-box-999')
    parser.add_argument('--uk', help='User secret private RSA key.', default='/files/user.key')
    parser.add_argument('--pk', help='Public key file to encrypt file.', default='/files/key.1.pub')
    parser.add_argument('--inbox', help='Inbox address, or service name', default='inbox.lega.svc')
    parser.add_argument('--cm', help='CEGA MQ broker address')

    args = parser.parse_args()

    used_file = os.path.expanduser(args.input)
    key_pk = os.path.expanduser(args.uk)
    pub_key, _ = pgpy.PGPKey.from_file(os.path.expanduser(args.pk))

    inbox_host = args.inbox
    test_user = args.u
    connection = args.cm if args.cm else os.environ.get('CEGA_MQ', None)
    test_file, c4ga_md5 = encrypt_file(used_file, pub_key)
    if c4ga_md5:
        sftp_upload(inbox_host, test_user, test_file, key_pk)
        submit_cega(connection, test_user, test_file, c4ga_md5)
        LOG.info('Should be all!')


if __name__ == '__main__':
    main()
