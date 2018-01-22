.. _`ingestion process`:

Ingestion Procedure
===================

We decribe in this section the architecture of the ingestion
procedure. We assume the files are already uploaded in the user inbox.

.. image:: /static/CEGA-LEGA.png
   :target: ../_static/CEGA-LEGA.png
   :alt: General Architecture

For a given LocalEGA, Central EGA selects the associated ``vhost`` and
drops, in the ``files`` queue, one message per file to ingest.  A
message contains the *username*, the *filename* and the *checksums*
(along with their related algorithm) of the encrypted file and the
decrypted content. The message is picked up by some ingestion
workers. Several ingestion workers may be running concurrently at any
given time.

For each file, if it is found in the inbox, checksums are computed to
verify the integrity of the file (ie. whether the file was properly
uploaded). If the checksums are not provided, they will be derived
from companion files. Each worker retrieves the decryption key in a
secure manner, from the keyserver, and decrypts the file.

To improve efficiency, each block that is decrypted is piped into a
separate process for re-encryption. This has the advantage to
constrain the memory usage per worker and save the re-encryption
time. In addition to the re-encryption, we also compute the checksum
of the decrypted content.

After completion, the re-encrypted file is located in the staging
area, with a UUID name, and a message is dropped into the local
message broker to signal that the next step can start.

The next step is to move the file from the staging area into the
vault. A verification step is included to ensure that the storing went
fine.  After that, a message of completion is sent to Central EGA.

If any of the above steps generates an error, we exit the workflow and
log the error. In case the error is related to a misuse from the user,
such as submitting the wrong checksum or using an unrelated encryption
key, the error is forwarded to Central EGA in order to display for the
user.

