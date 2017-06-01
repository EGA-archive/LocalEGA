# -*- coding: utf-8 -*-


# Errors for the users
class FromUser(Exception):
    def __str__(self):
        return repr(self)
    def __repr__(self):
        return 'Incorrect user input'

class NotFoundInInbox(FromUser):
    def __init__(self, filename):
        self.filename = filename
    def __str__(self):
        return f'File not found in inbox'
        
class GPGDecryption(FromUser):
    def __init__(self, retcode, filename):
        self.filename = filename
        self.retcode = retcode
    def __str__(self):
        return f'Error {self.retcode}: Decrypting {self.filename} failed'

class Checksum(FromUser):
    def __init__(self, algo, msg):
        self.msg = msg
        self.algo = algo
    def __str__(self):
        return f'Invalid {self.algo} checksum {self.msg}'

class Unauthorized(FromUser):
    def __init__(self, user_id):
        self.user_id = user_id
    def __str__(self):
        return f'Error: Unauthorized user {self.user_id}'


# Any other exception is caught by us
class UnsupportedTask(Exception):
    pass

class MessageError(Exception):
    def __str__(self):
        return f'Error decoding the message from the queue'

class VaultDecryption(Exception):
    def __init__(self, filename):
        self.filename = filename
    def __str__(self):
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

