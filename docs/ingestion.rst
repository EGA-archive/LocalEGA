.. _`ingestion process`:

Ingestion Procedure
===================

We describe in this section the architecture of the ingestion
procedure. We assume the files are already uploaded in the user inbox.

.. image:: /static/CEGA-LEGA.png
   :target: ./_static/CEGA-LEGA.png
   :alt: General Architecture

For a given LocalEGA, Central EGA selects the associated ``vhost`` and
drops, in the ``files`` queue, one message per file to ingest.  A
message contains the *username*, the *filename* and *stable
id*. Optionally, it can also contain a *checksum* (along with the
related algorithm) of the encrypted file. The message is picked up by
some ingestion workers. Several ingestion workers may be running
concurrently at any given time.

For each file, if it is found in the inbox, checksums are computed to
verify the integrity of the file (ie. whether the file was properly
uploaded), in case the ``do_checksum`` is set the ``True`` in the
configuration settings. If the checksum is not provided, it will be
derived from a companion file.

We leverage the Crypt4GH format. Each worker reads an inbox file and
strips the Crypt4GH header from the beginning of the file, puts it in
a database and sends the remainder to a backend store. There is no
decryption key retrieved during that step. The backend store can be
either a regular file system on disk, or an S3 object storage.

The files are read chunk by chunk in order to bound the memory
usage. After completion, the remainder of the file (the AES encrypted
bulk part) is in the vault and a message is dropped into the local
message broker to signal that the next step can start.

The next step is a verification step to ensure that the stored file is
decryptable and that the integrated checksum is valid. At that stage,
the associated decryption key is retrieved in a secure manner, from
the keyserver, and the header is decrypted using it. The output
contains the necessary information (such as the session key) to
recuperate the original file. If decryption completes and the checksum
is valid, a message of completion is sent to Central EGA: Ingestion
completed.

If any of the above steps generates an error, we exit the workflow and
log the error. In case the error is related to a misuse from the user,
such as submitting the wrong checksum or tempering with the encrypted
file, the error is forwarded to Central EGA in order to be displayed
for the user.
