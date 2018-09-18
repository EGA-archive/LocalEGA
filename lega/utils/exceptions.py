# -*- coding: utf-8 -*-
"""Exceptions."""

#############################################################################
# User Errors
#############################################################################


class FromUser(Exception):
    """Raised Exception on incorrect user input."""

    def __str__(self):  # Informal description
        """Return readale informal description."""
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
        """Return readale informal exception description."""
        return f'File not found in inbox'

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
        """Return readale informal exception description."""
        return f'Companion file not found in inbox'

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
        """Return readale informal exception description about checksumed exception."""
        return 'Invalid {} checksum for the {} file'.format(self.algo, 'original' if self.decrypted else 'encrypted')

    def __repr__(self):
        """Return readale informal exception description about checksumed exception, with file name."""
        return 'Invalid {} checksum for the {} file: {}'.format(self.algo, 'original' if self.decrypted else 'encrypted', self.file)


#############################################################################
# PGP Key Error. Not all are from the user
#############################################################################

class PGPKeyError(Exception):
    """Raised Exception related to PGP keys."""

    def __init__(self, msg):
        """Initialize PGPKeyError Exception."""
        self.msg = msg

    def __str__(self):
        """Return readale informal exception description."""
        return 'PGP Key error'

    def __repr__(self):
        """Return PGP error message."""
        return f'PGP Key error: {self.msg}'


class KeyserverError(Exception):
    """Raised Exception in case communication with Keyserver fails."""

    def __init__(self, msg):
        """Initialize KeyserverError Exception."""
        self.msg = msg

    def __str__(self):
        """Return readale informal exception description."""
        return 'Keyserver error'

    def __repr__(self):
        """Return Keyserver error message."""
        return f'Keyserver error: {self.msg}'


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
