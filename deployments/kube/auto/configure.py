from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
import datetime
import os
import errno
import logging
import configparser
import secrets
import string
import hashlib
from base64 import b64encode

from pgpy import PGPKey, PGPUID
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes)

# Logging
FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)


class ConfigGenerator:
    """Configuration generator.

    For when one needs to do create configuration files.
    """

    def __init__(self, config_path, name, email, namespace, services,):
        """Set things up."""
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

    # Based on
    # https://www.pythonsheets.com/notes/python-crypto.html#aes-cbc-mode-encrypt-via-password-using-cryptography
    # Provided under MIT license: https://github.com/crazyguitar/pysheeet/blob/master/LICENSE

    def _EVP_ByteToKey(self, pwd, md, salt, key_len, iv_len):
        """Derive key and IV.

        Based on https://www.openssl.org/docs/man1.0.2/crypto/EVP_BytesToKey.html
        """
        buf = md(pwd + salt).digest()
        d = buf
        while len(buf) < (iv_len + key_len):
            d = md(d + pwd + salt).digest()
            buf += d
        return buf[:key_len], buf[key_len:key_len + iv_len]

    def aes_encrypt(self, pwd, ptext, md):
        """Encrypt AES."""
        key_len, iv_len = 32, 16

        # generate salt
        salt = os.urandom(8)

        # generate key, iv from password
        key, iv = self._EVP_ByteToKey(pwd, md, salt, key_len, iv_len)

        # pad plaintext
        pad = padding.PKCS7(128).padder()
        ptext = pad.update(ptext) + pad.finalize()

        # create an encryptor
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # encrypt plain text
        ctext = encryptor.update(ptext) + encryptor.finalize()
        ctext = b'Salted__' + salt + ctext

        # encode base64
        return ctext

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

    def generate_ssl_certs(self, country, country_code, location, org, email, org_unit="SysDevs", common_name="LocalEGA"):
        """Generate SSL self signed certificate."""
        # Following https://cryptography.io/en/latest/x509/tutorial/?highlight=certificate
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        priv_key = key.private_bytes(encoding=serialization.Encoding.PEM,
                                     format=serialization.PrivateFormat.TraditionalOpenSSL,
                                     encryption_algorithm=serialization.NoEncryption(),)

        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, country_code),
                                      x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, country),
                                      x509.NameAttribute(NameOID.LOCALITY_NAME, location),
                                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
                                      x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, org_unit),
                                      x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                                      x509.NameAttribute(NameOID.EMAIL_ADDRESS, email), ])
        cert = x509.CertificateBuilder().subject_name(
                    subject).issuer_name(
                    issuer).public_key(
                    key.public_key()).serial_number(
                    x509.random_serial_number()).not_valid_before(
                    datetime.datetime.utcnow()).not_valid_after(
                    datetime.datetime.utcnow() + datetime.timedelta(days=1000)).add_extension(
                    x509.SubjectAlternativeName([x509.DNSName(u"localhost")]), critical=False,).sign(
                    key, hashes.SHA256(), default_backend())
        return (cert.public_bytes(serialization.Encoding.PEM).decode('utf-8'), priv_key.decode('utf-8'))

    def _hash_pass(self, password):
        """Hashing password according to RabbitMQ specs."""
        # 1.Generate a random 32 bit salt:
        # This will generate 32 bits of random data:
        salt = os.urandom(4)

        # 2.Concatenate that with the UTF-8 representation of the password (in this case "simon")
        tmp0 = salt + password.encode('utf-8')

        # 3. Take the SHA256 hash and get the bytes back
        tmp1 = hashlib.sha256(tmp0).digest()

        # 4. Concatenate the salt again:
        salted_hash = salt + tmp1

        # 5. convert to base64 encoding:
        pass_hash = b64encode(salted_hash).decode("utf-8")

        return pass_hash

    def generate_user_auth(self, password):
        """Generate user auth for CEGA Users."""
        key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=4096)

        # get public key in OpenSSH format
        public_key = key.public_key().public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)

        # get private key in PEM container format
        pem = key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL,
                                encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8')))  # yeah not really that secret

        # decode to printable strings
        with open(self._config_path / 'user.key', "wb") as f:
            f.write(pem)
        return public_key.decode('utf-8')

    def generate_mq_auth(self):
        """Generate CEGA MQ auth."""
        generated_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(32))
        cega_defs_mq = """{{"rabbit_version":"3.6.11",\r\n     "users":[{{"name":"lega",
            "password_hash":"{0}","hashing_algorithm":"rabbit_password_hashing_sha256","tags":"administrator"}}],\r\n     "vhosts":[{{"name":"lega"}}],\r\n
            "permissions":[{{"user":"lega", "vhost":"lega", "configure":".*", "write":".*", "read":".*"}}],\r\n     "parameters":[],\r\n     "global_parameters":[{{"name":"cluster_name", "value":"rabbit@localhost"}}],\r\n     "policies":[],\r\n
            "queues":[{{"name":"inbox", "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{{}}}},\r\n
            {{"name":"inbox.checksums", "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{{}}}},\r\n
            {{"name":"files",           "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{{}}}},\r\n {{"name":"completed",       "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{{}}}},\r\n
            {{"name":"errors",          "vhost":"lega", "durable":true, "auto_delete":false, "arguments":{{}}}}],\r\n
            "exchanges":[{{"name":"localega.v1", "vhost":"lega", "type":"topic", "durable":true, "auto_delete":false, "internal":false, "arguments":{{}}}}],\r\n
            "bindings":[{{"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{{}},"destination":"inbox","routing_key":"files.inbox"}},\r\n    \t     {{"source":"localega.v1","vhost":"lega","destination_type":"queue",
            "arguments":{{}},"destination":"inbox.checksums","routing_key":"files.inbox.checksums"}},\r\n {{"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{{}},"destination":"files","routing_key":"files"}},\r\n
            {{"source":"localega.v1","vhost":"lega","destination_type":"queue","arguments":{{}},"destination":"completed","routing_key":"files.completed"}},\r\n
            {{"source":"localega.v1","vhost":"Flega","destination_type":"queue","arguments":{{}},"destination":"errors","routing_key":"files.error"}}]\r\n}}""".format(self._hash_pass(generated_secret))
        cega_config_mq = """%% -*- mode: erlang -*-
                         %%
                         [{rabbit,[{loopback_users, [ ] },
                          {disk_free_limit, "1GB"}]},
                             {rabbitmq_management, [ {load_definitions, "/etc/rabbitmq/defs.json"} ]}
                         ]."""
        return (generated_secret, cega_config_mq, cega_defs_mq)

    def create_conf_shared(self, scheme=None):
        """Create default configuration file, namely ```conf.ini`` file."""
        config = configparser.RawConfigParser()
        file_flag = 'w'
        scheme = scheme if scheme else ''
        config.set('DEFAULT', 'log', 'console')
        # keyserver
        config.add_section('keyserver')
        config.set('keyserver', 'port', '8443')
        # quality control
        config.add_section('quality_control')
        config.set('quality_control', 'keyserver_endpoint', f'https://{self._key_service}.{self.namespace}{scheme}:8443/retrieve/%s/private')
        # inbox
        config.add_section('inbox')
        config.set('inbox', 'location', '/ega/inbox/%s')
        config.set('inbox', 'mode', '2750')
        # vault
        config.add_section('vault')
        config.set('vault', 'driver', 'S3Storage')
        config.set('vault', 'url', f'http://{self._s3_service}.{self.namespace}{scheme}:9000')
        # outgestion
        config.add_section('outgestion')
        config.set('outgestion', 'keyserver_endpoint',  f'https://{self._key_service}.{self.namespace}{scheme}:8443/retrieve/%s/private')
        # broker
        config.add_section('broker')
        config.set('broker', 'host', f'{self._broker_service}.{self.namespace}{scheme}')
        config.set('broker', 'connection_attempts', '30')
        config.set('broker', 'retry_delay', '10')
        # Postgres
        config.add_section('postgres')
        config.set('postgres', 'host', f'{self._db_service}.{self.namespace}{scheme}')
        config.set('postgres', 'user', 'lega')
        config.set('postgres', 'try', '30')

        with open(self._config_path / 'conf.ini', file_flag) as configfile:
            config.write(configfile)

    def add_conf_key(self, expire, file_name, comment, passphrase, armor=True, active=False):
        """Create default configuration for keyserver.

        .. note: Information for the key is provided as dictionary for ``key_data``,
        and should be in the format ``{'comment': '','passphrase': None, 'armor': True}.
        If a passphrase is not provided it will generated.``
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


# if __name__ == '__main__':
    # main()
