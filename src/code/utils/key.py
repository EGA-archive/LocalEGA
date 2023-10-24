import logging

LOG = logging.getLogger(__name__)

class Key():
    """Base class holding the information about a keypair."""

    __slots__ = ('config', 'section', 'pubkey', 'seckey')

    def __init__(self, config, section):
        """Initiliaze the Key object from a dict."""
        self.config = config
        self.section = section
        self.pubkey = None
        self.seckey = None

    def public(self):
        """Get the public key part.

        Returns bytes
        """
        raise NotImplementedError('subclasses of Key must provide an public() method')

    def private(self):
        """Get the private key part.

        Returns bytes
        """
        raise NotImplementedError('subclasses of Key must provide an private() method')


class C4GHFileKey(Key):
    """Loading a Crypt4GH-formatted file, and unlocking it using a passphrase.

    See https://crypt4gh.readthedocs.io/en/latest/keys.html
    """

    def _load(self):
        """Initiliaze the Key object from a dict."""
        filepath = self.config.get(self.section, 'filepath')
        LOG.debug('Loading %s from %s', type(self), filepath)
        passphrase = self.config.getsensitive(self.section, 'passphrase')
        assert(filepath and passphrase)

        if isinstance(passphrase, bytes):  # to str
            passphrase = passphrase.decode()

        # We use the parser provided in the crypt4gh.keys module
        from crypt4gh.keys import get_private_key
        LOG.debug('Unlocking private key: %s', filepath)
        self.seckey = get_private_key(filepath, lambda: passphrase)  # callback

        # Don't bother reading the public key from file,
        # We can simply recompute it from the private key
        from nacl.public import PrivateKey
        self.pubkey = bytes(PrivateKey(self.seckey).public_key)

        LOG.info('Successfully loaded from %s', filepath)

    def public(self):
        """Get the public key part.

        Returns 32 bytes
        """
        if not self.pubkey:
            self._load()
        return self.pubkey

    def private(self):
        """Get the private key part.

        Returns 32 bytes
        """
        if not self.seckey:
            self._load()
        return self.seckey

class C4GHFilePubKey(Key):
    """Loading a Crypt4GH-formatted public key from a file.
    """

    def public(self):
        """Get the public key part.

        Returns 32 bytes
        """
        if not self.pubkey:
            filepath = self.config.get(self.section, 'filepath')
            LOG.debug('Loading %s from %s', type(self), filepath)
            # We use the parser provided in the crypt4gh.keys module
            from crypt4gh.keys import get_public_key
            self.pubkey = get_public_key(filepath)
            LOG.info('Successfully loaded from %s', filepath)
        return self.pubkey

    def private(self):
        raise NotImplementedError('Not accessible')
