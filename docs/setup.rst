Installation
============

.. highlight:: shell

The sources for LocalEGA can be downloaded and installed from the `EGA-archive Github repo`_.

.. code-block:: console

    $ pip install git+https://github.com/EGA-archive/LocalEGA.git

Local EGA uses a microservice architecture and we use `Docker`_ to deploy it.

In order to simplify the setup of LocalEGA's components, we have
developed a bootstrap script, taylored for a local `Docker`_
deployment. Prior to running the bootstrap script, a settings file
must be created, defining the following variables: (place them in a
newly created file ``deploy/bootstrap/settings.rc``).

.. csv-table::
   :header: "Key", "Value", "Example","Description"
   :widths: 2, 2, 1, 2

   "``DOCKER_PORT_inbox``", "integer", "2222", "Port mapping to access the container from the host or external network"
   "``DOCKER_PORT_outgest``", "integer", "10443", "Port mapping to access the container from the host or external network"
   "``CEGA_REST_PASSWORD``", "string", "", "Password to connect to the Central EGA Users ReST endpoint"
   "``CEGA_CONNECTION``", "string", "amqps://<user>:<password>@hellgate.crg.eu:5271/<vhost>", "CentralEGA [RabbitMQ URI](https://www.rabbitmq.com/uri-spec.html)"
   "``LEGA_MQ_PASSWORD``", "string", "``$(generate_password 16)``", "Password for the Local MQ broker admin user"
   "``SSL_SUBJ``", "string", "``/C=ES/ST=Spain/L=Barcelona/O=CRG/OU=SysDevs/CN=LocalEGA/emailAddress=all.ega@crg.eu``", "Used to create the self-signed certificates"
   "``EC_KEY_COMMENT``", "string", "LocalEGA@CRG", "For the elliptic key, used by Crypt4GH"
   "``EC_KEY_PASSPHRASE``", "string", "``$(generate_password 16)``", ""
   "``EC_KEY_COMMENT``", "string", "LocalEGA-signing@CRG", ""
   "``EC_KEY_PASSPHRASE``", "string", "``$(generate_password 16)``", ""
   "``DB_LEGA_IN_PASSWORD``", "string", "``$(generate_password 16)``", "Password for the ``lega_in`` database user"
   "``DB_LEGA_OUT_PASSWORD``", "string", "``$(generate_password 16)``", "Password for the ``lega_out`` database user"
   "``S3_ACCESS_KEY``", "string", "``$(generate_password 16)``", "Access key for the S3 storage"
   "``S3_SECRET_KEY``", "string", "``$(generate_password 32)``", "Secret key for the S3 storage"

You are now ready to run the bootstrap script:

.. code-block:: console

    $ make -C deploy bootstrap

This script creates random passwords, configuration files, necessary
public/secret keys and connect the different components together. All
interesting settings are found in the ``private`` directory. Look
especially at its ``.trace`` file.

Once the bootstrap files are generated, you can spin up the LocalEGA components, using:

.. code-block:: console

    $ make up

Use ``make ps`` to see its status.

.. note::
   You can find different deployment strategies, covered by our
   partners, for environments like `Docker Swarm`_, `Kubernetes`_, `Openstack`_.

.. _EGA-archive Github repo: https://github.com/EGA-archive/LocalEGA
.. _Docker: https://github.com/EGA-archive/LocalEGA/tree/master/deploy
.. _Docker Swarm: https://github.com/NBISweden/LocalEGA-deploy-swarm
.. _Kubernetes: https://github.com/NBISweden/LocalEGA-deploy-k8s
.. _Openstack: https://github.com/NBISweden/LocalEGA-deploy-terraform



