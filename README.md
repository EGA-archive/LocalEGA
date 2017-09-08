# NBIS repository for the Local EGA project

The [code](./src) is written in Python (3.6+).

You can provision and deploy the different components:

* locally, using [docker-compose](./docker).
* on an OpenStack cluster, using [terraform](./terraform).

# Architecture

LocalEGA is divided into several components, whether as docker
containers or as virtual machines.

| Components | Role |
|------------|------|
| db         | Sets up a postgres database with appropriate schema |
| mq         | Sets up a RabbitMQ message broker with appropriate accounts, exchanges, queues and bindings |
| inbox      | SFTP server where user credentials are in the db component |
| frontend   | Documentation for the users |
| connectors | Back and Forth communication between CentralEGA and LocalEGA |
| monitors   | Gathers the logs of all components |
| keys       | Handles the GPG and master keys for encryption/decryption |
| workers    | Connect to the keys component (via SSL) and do the actual re-encryption work |
| vault      | Stores the files from the staging area to the vault. It includes a verification step afterwards. |

The workflow is as follows. We indicate the involved component in
between parenthesis.

Central EGA drops a message containing the user account information,
which is picked up (connectors) and forwarded internally (mq). 

Once in the internal message broker (mq), the inbox service gets the
message and creates the user account. It simply drops the information
into the database and creates a home folder with the right
permissions. The user ID can be its Elixir-ID (of which we strip the
@elixir-europe.org). The custom-made NSS and PAM modules allow user
authentication via either a password or an RSA key. The user is
chrooted into their home folder.

Central EGA drops a message per file to ingest, containing the
username, the filename and the checksums (along with their related
algorithm) of the encrypted file and the decrypted content. The
message is picked up (connectors) and forwarded internally (mq).

For each file, if it is found in the inbox (by a worker), checksums
are computed to verify the integrity of the file (ie. did we receive
it entirely). If the checksums are not provided, they will be derived
from companion files. That worker retrieves the decryption key (keys)
in a secure manner and decrypts the file.

To improve efficiency, each block that are decrypted are piped into a
separate process for re-encryption. This has the advantage to
constrain the memory usage per worker and save the re-encryption
time. Moreover, we compute the checksum of the decrypted
content. After completion, the re-encrypted file is located in the
staging area, with a UUID name, and a message is drop into the message
broker to signal that the next step can start.

The file is moved from the staging area into the vault. A verification
step is included to ensure that the storing went fine (vault+verify).
After that, a message of completion is sent (connector) to Central EGA
(mq).
