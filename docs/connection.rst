.. _cega_lega:

Connection CEGA |connect| LEGA
==============================

All Local EGA instances are connected to Central EGA using
`RabbitMQ`_, a message broker, that allows application components to
send and receive messages asynchronously. Messages are queued, and
resend on network failure or connection problems. Naturally, this is
configurable.

The RabbitMQ message brokers of each LocalEGA are the **only**
components with the necessary credentials to connect to Central
EGA, the other LocalEGA components are not.

We call ``CegaMQ`` and ``LegaMQ``, the RabbitMQ message brokers of,
respectively, Central EGA and Local EGA.

.. note:: We use RabbitMQ version to ``3.7.8``.

``CegaMQ`` declares a ``vhost`` for each LocalEGA instance. It also
creates the credentials to connect to that ``vhost`` in the form of a
*username/password* pair. The connection uses the AMQP(S) protocol
(The S adds TLS encryption to the traffic).

``LegaMQ`` then uses a connection string with the following syntax:

.. code-block:: console

   amqp[s]://<user>:<password>@<cega-host>:<port>/<vhost>


``CegaMQ`` contains an exchange named ``localega.v1``. ``v1`` is used
for versioning and is internal to CentralEGA. The queues connected to
that exchange are also internal to CentralEGA. The queues are, per
``vhost``:

+---------------------+---------------------------------------------------------------+
| Name                | Purpose                                                       |
+=====================+===============================================================+
| v1.files            | Triggers for file ingestion                                   |
+---------------------+---------------------------------------------------------------+
| v1.files.completed  | When files are properly ingested                              |
+---------------------+---------------------------------------------------------------+
| v1.files.errors     | User-related errors                                           |
+---------------------+---------------------------------------------------------------+
| v1.files.inbox      | Notifications of uploaded files                               |
+---------------------+---------------------------------------------------------------+
| v1.files.processing | Notifications that files are started to be ingested           |
+---------------------+---------------------------------------------------------------+
| v1.stableIDs        | Upon completion, a stable ID is created and communicated here |
+---------------------+---------------------------------------------------------------+

``LegaMQ`` contains two exchanges named ``lega`` and ``cega``, and the following queues, in the default ``vhost``:

+-----------------+-------------------------------------+
| Name            | Purpose                             |
+=================+=====================================+
| files           | Trigger for file ingestion          |
+-----------------+-------------------------------------+
| archived        | The file is in the vault            |
+-----------------+-------------------------------------+
| stableIDs       | The stable ID is created            |
+-----------------+-------------------------------------+
| qc              | The file is "verified" in the vault |
|                 | and Quality Controllers can execute |
+-----------------+-------------------------------------+

``LegaMQ`` registers ``CegaMQ`` as an *upstream* and listens to the
incoming messages in ``v1.files`` using a *federated queue*.  Ingestion
workers listen to the ``files`` queue of the local broker. If there
are no messages to work on, ``LegaMQ`` will ask its upstream queue if
it has messages. If so, messages are moved downstream. If not,
ingestion workers wait for messages to arrive.

.. note:: This gives us the ability to ingest files coming from
   CentralEGA, as well as files coming from other instances.  For
   example, we could drop an ingestion message into ``LegaMQ`` files
   queue in order to ingest files that are external to CentralEGA.


``CegaMQ`` receives notifications from ``LegaMQ`` using a
*shovel*. Everything that is published to its ``cega`` exchange gets
forwarded to CentralEGA (using the same routing key). This is how we
propagate the different status of the workflow to CentralEGA.

Note that we do not need at the moment a queue to store the completed
message, nor the errors, as we directly forward them to Central
EGA. They can be added later on, if necessary.


.. image:: /static/CEGA-LEGA.png
   :target: ./_static/CEGA-LEGA.png
   :alt: RabbitMQ setup

Adding a new Local EGA instance
-------------------------------

Central EGA only has to prepare a user/password pair along with a
``vhost`` and the related queues in RabbitMQ.

When Central EGA has communicated these credentials to the given Local EGA
instance, the latter can contact Central EGA using the federated queue
and the shovel mechanism in their local broker.

CentralEGA should then see 3 incoming connections from that new
LocalEGA instance, on the given ``vhost`` (2 federated queues and one
shovel).

The exchanges and routing keys will be the same as all the other
LocalEGA instances, since the clustering is done per ``vhost``.

Message Format
--------------

It is necessary to agree on the format of the messages exchanged
between Central EGA and any Local EGAs. Central EGA's messages are
JSON-formatted.

The interface between the LocalEGAs and CentralEGA is at the level of
the messages dropped in the ``v1.*`` queues at CentralEGA. Internally,
LocalEGAs can use what message format they see fit.

The message arriving in the ``v1.files`` queue contains the following fields

* ``user``
* ``file_path``

The message arriving in ``v1.files.completed`` (from LocalEGA instances) must contain:

* ``user``
* ``file_path``
* ``decrypted_checksums``, as an array of JSON object with:

  - ``type`` (md5 or sha256)
  - ``value``

The md5 should be present since it is used to compute the stable ID.

The message arriving in ``v1.stableIDs`` contains:

* ``user``
* ``file_path``
* ``stable_id``
* ``decrypted_checksums``, as an array of JSON object with:

  - ``type``
  - ``value``

.. note:: This allows not to leak out any internal file ID.

An error message arriving in the ``v1.files.errors`` queue contains the following fields:

* ``user``
* ``file_path``
* ``reason``

Examples
--------

CentralEGA gets notified of an inbox upload with:

.. code-block:: json

    {
      "user": "john",
      "file_path": "somedir/encrypted.file.c4gh",
      "file_size": 123456,
      "encrypted_checksums": [{"type": "sha256", "value": "8ce5a6fd145f758c49a8e2e6028fb8654b5545f5eb27a051026f8f5e83426f76"}]
    }

CentralEGA could send:

.. code-block:: json

    {
      "user": "john",
      "file_path": "somedir/encrypted.file.c4gh",
    }

and LocalEGA could respond with:

.. code-block:: json

   {
     "user":"john",
     "file_path":"somedir/encrypted.file.c4gh",
     "decrypted_checksums": [{"type": "sha256", "value": "e5b844cc57f57094ea4585e235f36c78c1cd222262bb89d53c94dcb4d6b3e55d"},
		             {"type": "md5", "value": "f1c9645dbc14efddc7d8a322685f26eb"}]
   }

and the stable ID message would be:

.. code-block:: json

   {
     "user" : "john",
     "stable_id" : "EGAF00000000003",
     "file_path" : "somedir/encrypted.file.c4gh",
     "decrypted_checksums" : [{ "type" : "sha256", "value" : "e5b844cc57f57094ea4585e235f36c78c1cd222262bb89d53c94dcb4d6b3e55d" }]
   }

In case of errors, Central EGA receives:

.. code-block:: json

    {
      "user": "john",
      "file_path": "somedir/encrypted.file.c4gh",
      "reason": "Some user related error, like Decryption failed: wrong key signature"
    }


.. |connect| unicode:: U+21cc .. <->
.. _RabbitMQ: http://www.rabbitmq.com
