import logging

LOG = logging.getLogger(__name__)

class Key():

    def __init__(self, config):
        """
        Initiliazing the Key object from a dict
        """
        self.config = config

    def public(self):
        """
        The public key part
        Return bytes
        """
        raise NotImplementedError('subclasses of Key must provide an public() method')

    def private(self):
        """
        The private key part
        Return bytes
        """
        raise NotImplementedError('subclasses of Key must provide an private() method')



class C4GHFileKey():
    '''Loading a Crypt4GH-formatted file, and unlocking it using a passphrase.

    See https://crypt4gh.readthedocs.io/en/latest/keys.html'''

    def __init__(self, config):
        
        filepath = config.get('filepath')
        passphrase = config.get('passphrase')
        assert(filepath and passphrase)

        # We use the parser provided in the crypt4gh.keys module
        from crypt4gh.keys import get_private_key
        LOG.debug('Unlocking private key: %s', filepath)
        self.seckey = get_private_key(filepath, lambda : passphrase) # callback

        # Don't bother reading the public key from file,
        # We can simply recompute it from the private key
        from nacl.public import PrivateKey
        self.pubkey = bytes(PrivateKey(self.seckey).public_key)
        LOG.debug('Setting public key: %s', self.pubkey.hex())

        LOG.info('Successfully loaded a Crypt4GH-formatted key from file')        

    def public(self):
        return self.pubkey

    def private(self):
        return self.seckey


class HashiCorpVaultKey():
    pass


class HTTPSKey():
    '''Retrive a public/private keypair from a remote server.'''

    def _convert_to_bool(value):
        assert value, "Can not convert an empty value"
        val = value.lower()
        if val in ('y', 'yes', 't', 'true', 'on', '1'):
            return True
        elif val in ('n', 'no', 'f', 'false', 'off', '0'):
            return False
        else:
            raise ValueError(f"Invalid truth value: {val}")


    class KeyserverError(Exception):
        pass

    class KeyNotFoundError(Exception):
        pass

    def _retrieve(keyurl):
        from urllib.request import urlopen
        from urllib.error import HTTPError
        try:
            context = self.context if keyurl.startswith('https') else None
            with urlopen(keyurl, context=context) as response:
                assert(response.status == 200)
                key = response.read()
                if not key:  # Correcting a bug in the EGA keyserver
                    # When key not found, it returns a 200 and an empty payload.
                    # It should probably be changed to a 404
                    raise KeyNotFoundError('No key found')
                return key
        except HTTPError as e:
            LOG.error(e)
            msg = str(e)
            if e.code == 404:  # If key not found, then probably wrong key.
                raise KeyNotFoundError(msg)
            # Otherwise
            raise KeyserverError(msg)

    def __init__(self, config):

        keyid = config.get('key_id')
        self.passphrase = config.get('passphrase')
        assert(keyid and passphrase)

        self.private_url = config.get('private_url', raw=True) % keyid
        LOG.info('Remote URL for private key: %s', self.private_url)
        self.public_url = config.get('public_url', raw=True) % keyid
        LOG.info('Remote URL for public key: %s', self.public_url)

        import ssl
        LOG.debug("Enforcing a TLS context")
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)  # Enforcing (highest) TLS version (so... 1.2?)

        context.verify_mode = ssl.CERT_NONE
        # Require server verification
        if self._convert_to_bool(config.get('verify_peer', 'no')):
            LOG.debug("Require server verification")
            context.verify_mode = ssl.CERT_REQUIRED
            cacertfile = CONF.get('cacertfile')
            if cacertfile:
                context.load_verify_locations(cafile=cacertfile)

        # Check the server's hostname
        server_hostname = config.get('server_hostname')
        verify_hostname = self._convert_to_bool(config.get('verify_hostname', 'no'))
        if verify_hostname:
            LOG.debug("Require hostname verification")
            assert server_hostname, "server_hostname must be set if verify_hostname is"
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
        
        # If client verification is required
        certfile = config.get('certfile')
        if certfile:
            LOG.debug("Prepare for client verification")
            keyfile = config.get('keyfile') # bark if not there
            context.load_cert_chain(certfile, keyfile=keyfile)
            
        self.context = context

    def public():
        key = self._retrieve(self.public_url)
        # Unlock with the passphrase
        # todo
        return key

    def private():
        key = self._retrieve(self.private_url)
        # Unlock with the passphrase
        # todo
        return key


