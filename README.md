# NBIS repository for the Local EGA project

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3dd83b28ec2041889bfb13641da76c5b)](https://www.codacy.com/app/NBIS/LocalEGA?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=NBISweden/LocalEGA&amp;utm_campaign=Badge_Grade)
[![Build Status](https://travis-ci.org/NBISweden/LocalEGA.svg?branch=dev)](https://travis-ci.org/NBISweden/LocalEGA)

The [code](./src) is written in Python (3.6+).

You can provision and deploy the different components:

* locally, using [docker-compose](./docker).
* on an OpenStack cluster, using [terraform](./terraform).

# Architecture

LocalEGA is divided into several components, whether as docker
containers or as virtual machines.

| Components | Role |
|------------|------|
| db         | A Postgres database with appropriate schema |
| mq         | A RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| inbox      | SFTP server, acting as a dropbox, where user credentials are in the db component |
| monitors   | Gathers the logs of all components |
| keyserver  | Handles the encryption/decryption keys |
| workers    | Connect to the keys component (via SSL) and do the actual re-encryption work |
| vault      | Stores the files from the staging area to the vault. It includes a verification step afterwards. |
| frontend   | Documentation for the users |

The workflow is as follows and consists of two ordered parts.

### Handling users

Central EGA contains a database of users. The users' ID can be their Elixir-ID
(of which we handle the @elixir-europe.org suffix by stripping it).

We have developped some custom-made NSS and PAM modules, allow user
authentication via either a password or an RSA key against the
CentralEGA database itself. The user is chrooted into their home
folder.

The procedure is as follows. The inbox is started without any created
user. When a user wants log into the inbox (actually, only sftp
uploads are allowed), the NSS module looks up the username in a local
database, and, if not found, queries the CentralEGA database. Upon
return, we stores the user credentials in the local database and
create the user's home folder. The user now gets logged in if the
password or public key authentication succeeds. Upon subsequent login
attempts, only the local database is queried, until the user's
credentials expire, making the local database effectively acts as a
cache.

After proper configuration, there is no user maintenance, it is
automagic. The other advantage is to have a central location of the
EGA users.

Note that it is also possible to add non-EGA users if necessary, by
adding them to the local database, and specifing a
non-expiration/non-flush policy for those users.


### Ingesting files

Central EGA drops a message per file to ingest, containing the
username, the filename and the checksums (along with their related
algorithm) of the encrypted file and the decrypted content. The
message is picked up by some ingestion workers. Many ingestion workers
can be created.

For each file, if it is found in the inbox, checksums are computed to
verify the integrity of the file (ie. did we receive it entirely). If
the checksums are not provided, they will be derived from companion
files. That worker retrieves the decryption key in a secure
manner (from the keyserver) and decrypts the file.

To improve efficiency, each block that are decrypted are piped into a
separate process for re-encryption. This has the advantage to
constrain the memory usage per worker and save the re-encryption
time. In addition to the re-encryption, we also compute the checksum
of the decrypted content. After completion, the re-encrypted file is
located in the staging area, with a UUID name, and a message is
dropped into the local message broker to signal that the next step can
start.

The next step is to move the file from the staging area into the
vault. A verification step is included to ensure that the storing went
fine.  After that, a message of completion is sent to Central EGA.
