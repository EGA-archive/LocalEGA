# -*- coding: utf-8 -*-
'''
Exceptions
'''

#############################################################################
# User Errors
#############################################################################

class FromUser(Exception):
    def __str__(self):  # Informal description
        return 'Incorrect user input'

    def __repr__(self):  # Technical description
        return str(self)

class NotFoundInInbox(FromUser):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f'File not found in inbox'

    def __repr__(self):
        return f'Inbox missing file: {self.filename}'

class UnsupportedHashAlgorithm(FromUser):
    def __init__(self, algo):
        self.algo = algo

    def __str__(self):
        return f'Unsupported hash algorithm: {self.algo!r}'

class CompanionNotFound(FromUser):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'Companion file not found in inbox'

    def __repr__(self):
        return f'Companion file not found for {self.name}'

class Checksum(FromUser):
    def __init__(self, algo, file=None, decrypted=False):
        self.algo = algo
        self.decrypted = decrypted
        self.file = file

    def __str__(self):
        return 'Invalid {} checksum for the {} file'.format(self.algo, 'original' if self.decrypted else 'encrypted')

    def __repr__(self):
        return 'Invalid {} checksum for the {} file: {}'.format(self.algo, 'original' if self.decrypted else 'encrypted', self.file)

#############################################################################
# PGP Key Error. Not all are from the user
#############################################################################

class PGPKeyError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'PGP Key error'

    def __repr__(self):
        return f'PGP Key error: {self.msg}'

class KeyserverError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Keyserver error'

    def __repr__(self):
        return f'Keyserver error: {self.msg}'

#############################################################################
# Any other exception is caught by us
#############################################################################

class AlreadyProcessed(Warning):
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
