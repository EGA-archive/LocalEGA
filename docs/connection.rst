.. _cega_lega:

Connection CEGA |connect| LEGA
==============================

All Local EGA instances are connected to Central EGA using
`RabbitMQ`_, a message broker, that allows application components to
send and receive messages. Messages are queued, not lost, and resend
on network failure or connection problems. Naturally, this is configurable.

The RabbitMQ message brokers of each LocalEGA are the **only**
components with the necessary credentials to connect to Central
EGA, the other LocalEGA components are not.

We call ``CegaMQ`` and ``LegaMQ``, the RabbitMQ message brokers of,
respectively, Central EGA and Local EGA.

.. note:: We pinned the RabbitMQ version to ``3.6.14``.


``CegaMQ`` declares a ``vhost`` for each LocalEGA instance. It also
creates the credentials to connect to that ``vhost`` in the form of a
*username/password* pair. The connection uses the AMQP(S) protocol
(The S adds TLS encryption to the traffic).

``LegaMQ`` then uses a connection string with the following syntax:

.. code-block:: console
		
   amqp[s]://<user>:<password>@<cega-host>:<port>/<vhost>


``CegaMQ`` contains an exchange named ``localega.v1``. ``v1`` is used for
versioning and is internal to CentralEGA. The queues connected to that
exchange are also internal to CentralEGA. For this documentation, we
use the stub implementation of CentralEGA and the follwing queues, per
``vhost``:

+-----------------+------------------------------------+
| Name            | Purpose                            |
+=================+====================================+
| files           | Triggers for file ingestion        |
+-----------------+------------------------------------+
| completed       | When files are properly ingested   |
+-----------------+------------------------------------+
| errors          | User-related errors                |
+-----------------+------------------------------------+
| inbox           | Notifications of uploaded files    |
+-----------------+------------------------------------+
| inbox.checksums | Checksum values for uploaded files |
+-----------------+------------------------------------+

``LegaMQ`` contains two exchanges named ``lega`` and ``cega``, and the following queues, in the default ``vhost``:

+-----------------+-------------------------------------+
| Name            | Purpose                             |
+=================+=====================================+
| files           | Trigger for file ingestion          |
+-----------------+-------------------------------------+
| archived        | The file is in the vault            |
+-----------------+-------------------------------------+
| qc              | The file is "verified" in the vault |
|                 | and Quality Controllers can execute |
+-----------------+-------------------------------------+

``LegaMQ`` registers ``CegaMQ`` as an *upstream* and listens to the
incoming messages in ``files`` using a *federated queue*.  Ingestion
workers listen to the ``files`` queue of the local broker. If there
are no messages to work on, ``LegaMQ`` will ask its upstream queue if
it has messages. If so, messages are moved downstream. If not,
ingestion workers wait for messages to arrive.

.. note:: This gives us the ability to ingest files coming from
   CentralEGA, as well as files coming from other instances.  For
   example, we could drop an ingestion message into ``LegaMQ``'s files
   queue in order to ingest files that are external to CentralEGA.


``CegaMQ`` receives notifications from ``LegaMQ`` using a
*shovel*. Everything that is published to its ``cega`` exchange gets
forwarded to CentralEGA (using the same routing key). This is how we
propagate the different status of the workflow to CentralEGA, using
the following routing keys:

+-----------------------+----------------------------------------------------------------------------+
| Name                  | Purpose                                                                    |
+=======================+============================================================================+
| files.completed       | In case the file is properly ingested                                      |
+-----------------------+----------------------------------------------------------------------------+
| files.error           | In case a user-related error is detected                                   |
+-----------------------+----------------------------------------------------------------------------+
| files.inbox           | In case a file is (re)uploaded                                             |
+-----------------------+----------------------------------------------------------------------------+
| files.inbox.checksums | In case a file path ends in ``.<algo>``, where *algo* is                   |
|                       | one of the :doc:`supported checksum algorithm </lega/utils/checksum.py>`   |
+-----------------------+----------------------------------------------------------------------------+

Note that we do not need at the moment a queue to store the completed
message, nor the errors, as we directly forward them to Central
EGA. They can be added later on, if necessary.


.. image:: /static/CEGA-LEGA.png
   :target: _static/CEGA-LEGA.png
   :alt: RabbitMQ setup

.. _supported checksum algorithm: md5

Adding a new Local EGA instance
-------------------------------

Central EGA only has to prepare a user/password pair along with a
``vhost`` in their RabbitMQ.

When Central EGA has communicated these details to the given Local EGA
instance, the latter can contact Central EGA using the federated queue
and the shovel mechanism in their local broker.

CentralEGA should then see 2 incoming connections from that new
LocalEGA instance, on the given ``vhost``.

The exchanges and routing keys will be the same as all the other
LocalEGA instances, since the clustering is done per ``vhost``.

Message Format
--------------

It is necessary to agree on the format of the messages exchanged
between Central EGA and any Local EGAs. Central EGA's messages are
JSON-formatted and contain the following fields:

* ``user``
* ``filepath``
* ``stable_id``
* ``encrypted_integrity``:

  - ``checksum``
  - ``algorithm``

All fields but ``encrypted_integrity`` are compulsory.

LocalEGA instances must return messages containing:

* ``user``
* ``filepath``
* ``stable_id``
* ``status``:

  - ``state``
  - ``details``

where ``state`` is either 'COMPLETED' or 'ERROR' (in which case,
'details' contains an informal text description).

For example, CentralEGA could send:

.. code-block:: json

    {
      "user": "john",
      "filepath": "somedir/encrypted.file.gpg",
      "stable_id": "EGAF0123456789012345"
    }

and LocalEGA could respond with:

.. code-block:: json

		{
		   "user":"john",
		   "filepath":"somedir/encrypted.file.gpg",
		   "status":{
		      "state":"COMPLETED",
		      "details":"File ingested, refer to it with EGAF0123456789012345"
		   }
		}


.. |connect| unicode:: U+21cc .. <->
.. _RabbitMQ: http://www.rabbitmq.com
