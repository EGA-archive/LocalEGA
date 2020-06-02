.. _cega_lega:

Connection CEGA |connect| LEGA
==============================

All Local EGA instances are connected to Central EGA using `AMQP, the
advanced message queueing protocol <http://www.amqp.org/>`_, that
allows application components to send and receive messages. Messages
are queued, not lost, and resend on network failure or connection
problems. Naturally, this is configurable.


In practice, the `reference implementation
<https://github.com/EGA-archive/LocalEGA/tree/master/ingestion/mq>`_
uses the RabbitMQ message broker for each LocalEGA, henceforth called
``LegaMQ`` or *local broker*, which is the **only** component with the
necessary credentials to connect to the Central EGA message broker,
henceforth called ``CegaMQ`` or *central broker*. The other LocalEGA
components are connected to their respective local broker.


.. image:: /static/CEGA-LEGA.png
   :target: ./_static/CEGA-LEGA.png
   :alt: RabbitMQ setup

.. note:: We pinned the RabbitMQ version to ``3.7.8``, so far, until
          both CegaMQ and LegaMQ can be upgraded simultaneously to the
          latest version.


For each LocalEGA instance, the central broker configures a ``vhost``,
and creates the credentials to connect to that ``vhost`` in the form
of a *username/password* pair. The local brokers then use a connection
string with the following syntax:

.. code-block:: console

   amqps://<user>:<password>@<cega-host>:<port>/<vhost>


The connection is a two-way connection using a combination of a
*federated queue* and a *shovel*.

``LegaMQ`` registers a *federated queue* with ``CegaMQ`` as *upstream*
and listens to the incoming messages. In order to minimize the number
of connection sockets, all Local EGAs only use *one* federated queue
towards the central broker, and all messages in the queue are
distinguished with a ``type``.

Ingestion workers listen to the downstream queue of the local broker. If there
are no messages to work on, ``LegaMQ`` will ask its upstream queue if
it has messages. If so, messages are moved downstream. If not,
ingestion workers wait for messages to arrive.

.. note:: This allows a Local EGA instance to *also* ingest files from
   other sources than Central EGA. For example, a message, external to
   Central EGA, could be dropped in the local broker in order to
   ingest non-EGA files.


``CegaMQ`` receives notifications from ``LegaMQ`` using a
*shovel*. ``LegaMQ`` has an exchange named ``cega`` configured such
that all messages published to it get forwarded to CentralEGA (using
the same routing key). This is how we propagate the different status
of the workflow to the central broker, using the following routing keys:

+-----------------------+-------------------------------------------------------+
| Name                  | Purpose                                               |
+=======================+=======================================================+
| files.archived        | In case the file is properly ingested                 |
+-----------------------+-------------------------------------------------------+
| files.completed       | In case the file is properly backed-up                |
+-----------------------+-------------------------------------------------------+
| files.error           | In case a user-related error is detected              |
+-----------------------+-------------------------------------------------------+
| files.inbox           | In case a file is (re)uploaded or removed             |
+-----------------------+-------------------------------------------------------+




Message interface (API)
=======================

It is necessary to agree on the format of the messages exchanged
between Central EGA and any Local EGAs. Central EGA's messages are
JSON-formatted and are distinguished with a field named ``type``.
There are 4 types of messages so far:

* ``type=ingest``: an ingestion trigger
* ``type=accession``: contains an accession id
* ``type=mapping``: contains a dataset to accession id mapping (they
  are known a the metadata release stage or when permissions are
  granted by a DAC
* ``type=heartbeat``: A mean to check if the Local EGA instance is "alive"

Ingestion 

* ``user``
* ``filepath``
* ``stable_id``
* (optionally) ``encrypted_integrity``:

  - ``checksum``
  - ``algorithm``

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
		   "stable_id": "EGAF0123456789012345",
		   "status":{
		      "state":"COMPLETED",
		      "details":"File ingested, refer to it with EGAF0123456789012345"
		   }
		}


.. |connect| unicode:: U+21cc .. <->
.. _RabbitMQ: http://www.rabbitmq.com
