# -*- coding: utf-8 -*-
"""Exceptions."""

#############################################################################
# User Errors
#############################################################################


class FromUser(Exception):
    """Raised Exception on incorrect user input."""

    def __str__(self):  # Informal description
        """Return readable informal description."""
        return 'Incorrect user input'

    def __repr__(self):  # Technical description
        """Return detailed, technical description."""
        return str(self)


class NotFoundInInbox(FromUser):
    """Raised Exception on incorrect user input.

    Exception should be raised if the input file was not found in Inbox.
    """

    def __init__(self, filename):
        """Initialize NotFoundInInbox Exception."""
        self.filename = filename

    def __str__(self):
        """Return readable informal exception description."""
        return 'File not found in inbox'

    def __repr__(self):
        """Return the file name for the missing file."""
        return f'Inbox missing file: {self.filename}'


class UnsupportedHashAlgorithm(FromUser):
    """Raised Exception when a specific algorithm is not supported."""

    def __init__(self, algo):
        """Initialize UnsupportedHashAlgorithm Exception."""
        self.algo = algo

    def __str__(self):
        """Return the unsupported algorithm name."""
        return f'Unsupported hash algorithm: {self.algo!r}'


class CompanionNotFound(FromUser):
    """Raised Exception if Companion file is not found."""

    def __init__(self, name):
        """Initialize CompanionNotFound Exception."""
        self.name = name

    def __str__(self):
        """Return readable informal exception description."""
        return 'Companion file not found in inbox'

    def __repr__(self):
        """Return the missing companion file name."""
        return f'Companion file not found for {self.name}'


class Checksum(FromUser):
    """Raised Exception related to an invalid checksum."""

    def __init__(self, algo, file=None, decrypted=False):
        """Initialize Checksum Exception."""
        self.algo = algo
        self.decrypted = decrypted
        self.file = file

    def __str__(self):
        """Return readable informal exception description about checksumed exception."""
        return 'Invalid {} checksum for the {} file'.format(self.algo, 'original' if self.decrypted else 'encrypted')

    def __repr__(self):
        """Return readable informal exception description about checksumed exception, with file name."""
        return 'Invalid {} checksum for the {} file: {}'.format(self.algo, 'original' if self.decrypted else 'encrypted', self.file)


class SessionKeyDecryptionError(FromUser):
    """Raised Exception when header decryption fails."""

    def __init__(self, h):
        """Initialize Checksum Exception."""
        self.header = h.hex().upper()

    def __str__(self):
        """Return readable informal exception description."""
        return 'Unable to decrypt header with master key'

    def __repr__(self):
        """Return readable technical exception description."""
        return f'Unable to decrypt header with master key: {self.header}'


# Is it really a user error?
class SessionKeyAlreadyUsedError(FromUser):
    """Raised Exception related a session key being already in use."""

    def __init__(self, checksum):
        """Initialize Checksum in Exception."""
        self.checksum = checksum

    def __str__(self):
        """Return readable informal exception description."""
        return 'Session key (likely) already used.'

    def __repr__(self):
        """Return the checksum of the session key already used."""
        return f'Session key (likely) already used [checksum: {self.checksum}].'


#############################################################################
# Any other exception is caught by us
#############################################################################

class AlreadyProcessed(Warning):
    """Raised when a file has already been processed."""

    def __init__(self, user, filename, enc_checksum_hash, enc_checksum_algorithm):
        """Initialize AlreadyProcessed Exception."""
        self.user = user
        self.filename = filename
        self.enc_checksum_hash = enc_checksum_hash
        self.enc_checksum_algorithm = enc_checksum_algorithm

    def __repr__(self):
        """Return detailed information about the file already processed."""
        return (f'Warning: File already processed\n'
                f'\t* user: {self.user}\n'
                f'\t* name: {self.filename}\n'
                f'\t* Encrypted checksum: {self.enc_checksum_hash} (algorithm: {self.enc_checksum_algorithm}')
