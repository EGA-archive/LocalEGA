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
        self.filename = filename

    def __str__(self):
        return 'File not found in inbox'

    def __repr__(self):
        return f'Inbox missing file: {self.filename}'


class SessionKeyDecryptionError(FromUser):
    """Raised Exception when header decryption fails."""

    def __init__(self, h):
        self.header = h.hex().upper()

    def __str__(self):
        return 'Unable to decrypt header with master key'

    def __repr__(self):
        return f'Unable to decrypt header with master key: {self.header}'


# Is it really a user error?
class SessionKeyAlreadyUsedError(FromUser):
    """Raised Exception related a session key being already in use."""

    def __init__(self, checksum):
        self.checksum = checksum

    def __str__(self):
        return 'Session key (likely) already used.'

    def __repr__(self):
        return f'Session key (likely) already used [checksum: {self.checksum}].'


class Crypt4GHHeaderDecryptionError(FromUser):
    """Raised Exception when header decryption fails."""

    def __str__(self):
        return 'Error decrypting this Crypt4GH file'

class Crypt4GHPayloadDecryptionError(FromUser):
    """Raised Exception when payload decryption fails."""

    def __str__(self):
        return 'Error decrypting the content of this file'


#############################################################################
# Any other exception is caught by us
#############################################################################

class AlreadyProcessed(Warning):
    """Raised when a file has already been processed."""

    def __init__(self, user, filename, enc_checksum_hash, enc_checksum_algorithm):
        self.user = user
        self.filename = filename
        self.enc_checksum_hash = enc_checksum_hash
        self.enc_checksum_algorithm = enc_checksum_algorithm

    def __repr__(self):
        return (f'Warning: File already processed\n'
                f'\t* user: {self.user}\n'
                f'\t* name: {self.filename}\n'
                f'\t* Encrypted checksum: {self.enc_checksum_hash} (algorithm: {self.enc_checksum_algorithm}')


class AlreadyInProgress(Warning):
    """Raised when a file is already in progress."""

    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return f'Warning: File already in progress or existing: {self.path}'


class ChecksumsNotMatching(Exception):
    """Raised when 2 checksums don't match."""

    def __init__(self, path, md1, md2):
        self.path = path
        self.md1 = md1
        self.md2 = md2

    def __str__(self):
        return f'Checksums for {self.path} do not match'

    def __repr__(self):
        return f'Checksums for {self.path} do not match:\n* {self.md1}\n* {self.md2}'

class RejectMessage(Exception):
    pass

class InvalidBrokerMessage(Exception):
    pass
# do not extend from RejectMessage, otherwise we can an infinite loop
