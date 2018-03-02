# -*- coding: utf-8 -*-


# Errors for the users
class FromUser(Exception):
    def __str__(self): # Informal description
        return 'Incorrect user input'
    def __repr__(self): # Technical description
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
        
class GPGDecryption(FromUser):
    def __init__(self, retcode, errormsg, filename):
        self.retcode = retcode
        self.error = errormsg
        self.filename = filename
    def __str__(self):
        return f'Decryption error'
    def __repr__(self):
        return f'Decryption error ({self.retcode}): {self.error}'

class Checksum(FromUser):
    def __init__(self, algo, file=None, decrypted=False):
        self.algo = algo
        self.decrypted = decrypted
        self.file = file
    def __str__(self):
        return 'Invalid {} checksum for the {} file'.format(self.algo, 'original' if self.decrypted else 'encrypted')
    def __repr__(self):
        return 'Invalid {} checksum for the {} file: {}'.format(self.algo, 'original' if self.decrypted else 'encrypted', self.file)

# Any other exception is caught by us
class MessageError(Exception):
    def __str__(self):
        return f'Error decoding the message from the queue'

class VaultDecryption(Exception):
    def __init__(self, filename):
        self.filename = filename
    def __str__(self):
        return f'Decrypting archived file failed'
    def __repr__(self):
        return f'Decrypting {self.filename} from the vault failed'

class AlreadyProcessed(Warning):
    def __init__(self, filename, enc_checksum_hash, enc_checksum_algorithm, submission_id):
        #self.file_id = file_id
        self.filename = filename
        self.enc_checksum_hash = enc_checksum_hash
        self.enc_checksum_algorithm = enc_checksum_algorithm
        self.submission_id = submission_id
    def __repr__(self):
        return (f'Warning: File already processed\n'
                #f'\t* id: {self.file_id}\n'
                f'\t* name: {self.filename}\n'
                f'\t* submission id: {submission_id})\n'
                f'\t* Encrypted checksum: {enc_checksum_hash} (algorithm: {enc_checksum_algorithm}')
