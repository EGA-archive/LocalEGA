# Generating the GPG_HOME

A proper GnuPG homedir includes `pubring.kbx`, `trustdb.gpg`,
`private-keys-v1.d` and `openpgp-revocs.d`.

Create the following `gen_key` file:

```
%echo Generating a basic OpenPGP key
Key-Type: RSA
Key-Length: 4096
Name-Real: EGA Sweden
Name-Comment: @NBIS
Name-Email: ega@nbis.se
Expire-Date: 0
Passphrase: YourSECRETpassphrase
# Do a commit here, so that we can later print "done" :-)
%commit
%echo done
```

In a terminal, issue the command:

	gpg --homedir <path/to/some/folder/to/be/the/gpg/home> --batch --generate-key <path/to/gen_key>

Make sure you have GnuPG version 2.2.0 (or higher)

Use now `<path/to/some/folder/to/be/the/gpg/home>` in the `.env` file
for the variable `GPG_HOME`. Use also `YourSECRETpassphrase` in the
`.env.d/gpg` file for the variable `GPG_PASSPHRASE`.

# Generating the RSA public and private keys


	openssl genpkey -algorithm RSA -out rsa.sec -pkeyopt rsa_keygen_bits:2048
	openssl rsa -pubout -in rsa.sec -out rsa.pubb
	
Use then the location of `rsa.pub` and `rsa.sec` for the .env
variables `RSA_PUB` and `RSA_SEC` respectively.


# Generating the SSL certificates

	openssl req -x509 -newkey rsa:2048 -keyout ssl.key -nodes -out ssl.cert -sha256 -days 1000
	
Use then the location of `ssl.cert` and `ssl.key` for the .env
variables `SSL_CERT` and `SSL_KEY` respectively.

# Generating some password hash for a user

	openssl passwd -1 -salt <some-salt> <some-password>
	
The `-1` switch makes it use MD5.

# Generating some password hash for a rabbitMQ user

Follow the instructions from: https://www.rabbitmq.com/passwords.html
