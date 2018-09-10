.. _bootstrap:

Bootstrap & Deployments
=======================

In order to simplify the setup of LocalEGA's components, we have
developed a few bootstrap scripts (one for the `Docker`_ deployment
and one for the `OpenStack cloud`_ deployment).

Those script create random passwords, configuration files, PGP keys
and connect the different components together.

All interesting settings are found the respective ``private``
directory of the LocalEGA instance. Look especially at the ``.trace``
file there.

Moreover, we use different deployment strategies for environments
like Docker Swarm, Kubernetes, Openstack or a local-machine.


* locally, using `docker-compose <https://github.com/NBISweden/LocalEGA/tree/dev/docker>`_;
* on an OpenStack cluster, using `terraform <https://github.com/NBISweden/LocalEGA-deploy-terraform>`_;
* on a Kubernetes/OpenShift cluster, using `kubernetes <https://github.com/NBISweden/LocalEGA-deploy-k8s>`_;
* on a Docker Swarm cluster, using `Gradle <https://github.com/NBISweden/LocalEGA-deploy-swarm>`_.



.. _Docker: https://github.com/NBISweden/LocalEGA/tree/dev/docker
.. _OpenStack cloud: https://github.com/NBISweden/LocalEGA-deploy-terraform
