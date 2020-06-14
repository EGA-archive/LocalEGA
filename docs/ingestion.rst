.. _`ingestion process`:

Ingestion
=========

|Testsuite| | Version |version| | Generated |today|


Architecture
------------

Besides the :ref:`inbox login system`, the long-term database and
archive storage, the ingestion pipeline employs a microservice
architecture with the following components:

.. image:: /static/ingestion.png
   :target: ./_static/ingestion.png
   :alt: Ingestion Architecture and Connected Components

The reference implementation implements the ingestion using a
microservice architecture with an internal database, a staging area
and a local broker.

.. raw:: html
   :file: ingestion.html

We assume the files are already uploaded in the :ref:`inbox login
system`. For a given Local EGA, Central EGA selects the associated
``vhost`` and drops, in the upstream queue, one message per file to
ingest, with ``type=ingest``.

On the Local EGA side, an worker retrieves this message, finds the
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
POSIX compliant file system. In order to use an S3-backed storage, the
Local EGA system administrator can use `s3fs-fuse
<https://github.com/s3fs-fuse/s3fs-fuse>`_, or update the code (`as it
was once done
<https://github.com/EGA-archive/LocalEGA/blob/v0.3.0/lega/utils/storage.py>`_
and is now offload to our swedish and finnish partners).

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

See the `long-term database schema
<https://github.com/EGA-archive/LocalEGA/blob/master/ingestion/db/archive-db.sql>`_,
for an example.



Installation & Bootstrap
------------------------

.. highlight:: shell

A reference implementation can be found in the `Local EGA Github
repository`_. We containerized the code and use `Docker`_ to deploy
it.

Since there are several components with multiple settings, we also
created a bootstrap script to help deploy a LocalEGA instance, on your
local machine. The bootstrap generates random passwords, configuration files,
necessary public/secret keys, certificates for secure communication
and connect the different components together (via docker-compose
files).

Finally, the bootstrap creates a few test users and a fake Central EGA
instance, to demonstrate the connection, and allow to run the `testsuite`_

Once the source tree downloaded, in the ``deploy`` directory, run the following command:

.. code-block:: console

    $ make -C bootstrap


Once the bootstrap files are generated, all interesting settings are
found in the ``private`` sub-directory, and you can spin up the
Local EGA components, using:

.. code-block:: console

    $ make up

The docker images are automatically generated on `docker hub`_, and
will be pulled in when booting the LocalEGA instance. This includes a
reference implementation of the `inbox component`_, found in a
separate repository.

That said, you can also (pre/re)generate the images with ``make -j 4 images``.

Use ``make ps`` to see its status.

.. note:: **Production deployments**: `Our partners`_ developed
	  alternative bootstrap methods for `Docker Swarm`_ and
	  `Kubernetes`_. Those methods allow you to deploy a LocalEGA
	  instance in a production environment, including scaling and
	  monitoring/healthcheck.

.. _`testsuite`:

Testsuite
---------

We have implemented a testsuite, grouping tests into the following
categories: *integration tests*, *robustness tests*, *security tests*,
and *stress tests*.

`All tests`_ simulate real-case user scenarios on how they
will interact with the system. All tests are performed on GitHub
Actions runner, when there is a push to master or a Pull Request
creation (i.e., they are integrated to the CI).

+-----------------------+-------------------------------------------------------+
| Category              | Purpose                                               |
+=======================+=======================================================+
| `Integration Tests`_  | test the overall ingestion architecture               |
|                       | and simulate how a user will use the system           |
+-----------------------+-------------------------------------------------------+
| `Robustness Tests`_   | test the microservice architecture and how            |
|                       | the components are inter-connected. They, for example,|
|                       | check that if the database or one microservice        |
|                       | is restarted, the overall functionality remains.      |
+-----------------------+-------------------------------------------------------+
| `Security Tests`_     | increase confidence around security of the            |
|                       | implementation. They give some deployment guarantees, |
|                       | such as one user cannot see the inbox of another user,|
|                       | or the vault is not accessible from the inbox.        |
+-----------------------+-------------------------------------------------------+
| `Stress Tests`_       | "measure" performance                                 |
+-----------------------+-------------------------------------------------------+


.. _All tests: https://github.com/EGA-archive/LocalEGA/tree/master/tests
.. _Integration Tests: https://github.com/EGA-archive/LocalEGA/tree/master/tests#integration-tests
.. _Robustness Tests: https://github.com/EGA-archive/LocalEGA/tree/master/tests#robustness-tests
.. _Security Tests: https://github.com/EGA-archive/LocalEGA/tree/master/tests#security
.. _Stress Tests: https://github.com/EGA-archive/LocalEGA/tree/master/tests#stress
.. _Local EGA Github repository: https://github.com/EGA-archive/LocalEGA
.. _Docker: https://github.com/EGA-archive/LocalEGA/tree/master/deploy
.. _Docker Swarm: https://github.com/neicnordic/LocalEGA-deploy-swarm
.. _Kubernetes: https://github.com/neicnordic/LocalEGA-deploy-init
.. _Our partners: https://github.com/neicnordic/LocalEGA
.. _inbox component: https://github.com/EGA-archive/LocalEGA-inbox
.. _docker hub: https://hub.docker.com/orgs/egarchive/repositories

.. |Testsuite| image:: https://github.com/EGA-archive/LocalEGA/workflows/Testsuite/badge.svg
	:alt: Testsuite Status
	:class: inline-baseline
