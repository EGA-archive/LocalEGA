.. _`ingestion process`:

Ingestion
=========

Architecture
------------

Besides the :ref:`inbox login system`, the long-term database and
archive storage, the ingestion pipeline employs a microservice
architecture with the following components:

.. image:: /static/ingestion.png
   :target: ./_static/ingestion.png
   :alt: Ingestion Architecture and Connected Components

The reference implementation uses a microservice architecture with an
internal database, a staging area and a local broker, for the
ingestion pipeline.

.. raw:: html
   :file: ingestion.html

We assume the files are already uploaded in the :ref:`inbox login
system`. For a given Local EGA, Central EGA selects the associated
``vhost`` and drops, in the upstream queue, one message per file to
ingest, with ``type=ingest``.

On the Local EGA side, a worker retrieves this message, finds the
associated file in the inbox, splits its Crypt4GH header, decrypts its
data portion (aka its payload), checksums its content, and moves the
payload to a staging area (with a temporary name). The files are read
chunk by chunk in order to bound the memory usage.

A message is then sent to Central EGA with the checksum of the
decrypted content (ie the original file) requesting an Accession ID. A
message with ``type=accession`` comes back via the upstream queue.

The reference implementation includes a backup step, to store 2 copies
of the payload. This is obviously for illustration purposes only, as
all Local EGA instance will probably already have their own backup
system (such as Ceph, for example).

The backend store can be either a regular file system on disk, or an
S3 object storage. The reference implementation can interface to a
POSIX compliant file system. In order to use an S3-backed storage, 
the Local EGA system administrator can use `s3fs-fuse <https://github.com/s3fs-fuse/s3fs-fuse>`_, 
or update the code (`as it was once done <https://github.com/EGA-archive/LocalEGA/blob/v0.4.0/lega/utils/storage.py>`_
and is now offloaded to our swedish and finnish partners).

If any of the above steps generates an error, we exit the workflow and
log the error. In case the error is related to a misuse from the user,
such as submitting to the wrong Local EGA or tempering with the
encrypted file, the error is forwarded to Central EGA in order to be
displayed for the user. If not, the error is left for a Local EGA
system administrator to handle.

Upon completion, the accession id, the header, and the archive paths
are saved in a separate long-term database, specific for each Local
EGA. The reference implementation provides one for illustration, and
saves a few more useful bits of information such as the payload size
and checksum. This allows a system administrator to do data curation
regularly.

.. raw:: html
   :file: ingestion-save.html




Installation
------------

.. highlight:: shell

A reference implementation can be found in the `Local EGA Github
repository`_. We containerized the code and use `Docker`_ to deploy
it.

Since there are several components, we provide a docker-compose files
with some settings, and a README for the deployment.

Finally, there is also a `fake Central EGA instance <https://github.com/EGA-archive/LocalEGA/tree/master/deploy/docker/cega>`_, 
to demonstrate the connection by triggering some messages:

.. code-block:: console

    make example                  # Encrypt a random file
    make sftp                     # Connect user John with password: john
    put data/example.txt.c4gh     # Upload the file to the inbox


Fake CEGA will trigger the ingestion message as soon as it receives the upload of this new file. 
Fake CEGA will also send the accession message when requested, and, after the completed message is received, it will finally send the release message.
To verify that the communication went well, the database can be queried. First use ``make psql``, then run this SQL command:

.. code-block:: console  

   select * from file_table;

       stable_id     | filesize | display_name | extension | created_by_db_user |          created_at           | edited_by_db_user |           edited_at           
   ------------------+----------+--------------+-----------+--------------------+-------------------------------+-------------------+-------------------------------
    EGAF900000000001 |     2200 | example.txt  |           | lega               | 2024-01-30 14:59:15.862122+00 | lega              | 2024-01-30 14:59:15.862122+00
   (1 row)


If everything went well, the file ``example.txt`` must exist and have an accession. 
Please, note that accessions sent by Fake CEGA start at ``EGAF900000000001``, and any new file uploaded to the inbox will issue a new accession, 
regardless of its content (as opposed to what Central EGA does, as it issues content-based accessions). Bear in mind that this sequence will be restarted after a database rebuilding.

Then, run this other command:

.. code-block:: console   

   select * from dataset_table;

       stable_id    | title | description | access_type | is_released | is_deprecated | created_by_db_user |          created_at           | edited_by_db_user |          edited_at           
   -----------------+-------+-------------+-------------+-------------+---------------+--------------------+-------------------------------+-------------------+------------------------------
    EGAD90000000123 |       |             | controlled  | t           | f             | lega               | 2024-01-30 14:59:15.873562+00 | lega              | 2024-01-30 14:59:15.87962+00
   (1 row)


If the release message was received, this very same information should be returned. 
Fake CEGA always sends a release message for this dataset ``EGAD90000000123``, regardless the file uploaded to the inbox.

The reference implementation can be deployed locally, using
`docker-compose`_ (suitable for testing or local development).

There is no need to pre/re-generate the docker images, because
they are automatically generated on `docker hub`_, and will be pulled
in when booting the LocalEGA instance. This includes a reference
implementation of the :ref:`inbox login system`. That said, executing
``make -j 4 images`` will generate them locally.

You can clean up the local instance using ``make down``.

.. note:: **Production deployments**: `Our partners`_ developed
	  alternative bootstrap methods for `Docker Swarm`_ and
	  `Kubernetes`_. Those methods allow you to deploy a LocalEGA
	  instance in a production environment, including scaling and
	  monitoring/healthcheck.

.. _Local EGA Github repository: https://github.com/EGA-archive/LocalEGA
.. _Docker: https://github.com/EGA-archive/LocalEGA/tree/master/deploy
.. _Docker Swarm: https://github.com/neicnordic/LocalEGA-deploy-swarm
.. _Kubernetes: https://github.com/neicnordic/LocalEGA-deploy-init
.. _Our partners: https://github.com/neicnordic/LocalEGA
.. _docker hub: https://hub.docker.com/orgs/egarchive/repositories
.. _docker-compose: https://docs.docker.com/compose/