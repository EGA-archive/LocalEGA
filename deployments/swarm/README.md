# Docker Swarm Deployment

![](https://habrastorage.org/webt/zt/rm/bk/ztrmbknpfaz9ybmoy3j12x5tlcw.gif)

## Prerequisites

The deployment tool of LocalEGA for Docker Swarm is based on [Gradle](https://gradle.org/), so you will need Gradle to
be installed on your machine in order to use it. On MacOS with Homebrew it can be done by executing
`brew install gradle`. Please, refer to official documentation to find instruction for other platforms.

Make sure [Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy](http://www.oracle.com/technetwork/java/javase/downloads/jce8-download-2133166.html) is set up.

## Structure

Gradle project has the following groups of tasks:

- `cluster` - code related to Docker Machine and Docker Swarm cluster provisioning
- `cega` - "fake" CentralEGA bootstrapping and deployment code
- `lega` - main LocalEGA microservices bootstrapping and deployment code
- `swarm` - root project aggregating both `cega` and `lega` 
- `test` - sample test case: generating a file, encrypting it, uploading to the inbox and ingesting it

## Cluster provisioning

Docker Swarm cluster can be provisioned using `gradle provision` command. Provisioning is done via 
[Docker Machine](https://docs.docker.com/machine/). Two providers are supported at the moment: `virtualbox` (default 
one) and `openstack`. 

To provision cluster in the OpenStack one needs to have OpenStack configuration file with filled
settings from [this list](https://docs.docker.com/machine/drivers/openstack/) (there's a sample file called 
`openstack.properties.sample` in the project folder). Then the command will look like this:
`gradle provision -PopenStackConfig=/absolute/path/to/openstack.properties`. 

By default one manager and one worker node are created. To increase the amount of workers, `workers` option can be 
used, e.g.: `gradle provision -Pworkers=8 PopenStackConfig=/absolute/path/to/openstack.properties`. 

Note that it may take a while to provision the cluster in OpenStack. To see how many nodes are ready one can run
`gradle list`. 

`gradle destroy` will remove all the virtual machines and destroy the cluster.

## Bootstrapping

**NB**: before bootstrapping execute `gradle env` and the `eval`-command printed out. *This is required in order to
run all subsequent commands against the Docker Swarm Manager and not against the local Docker daemon.*

The bootstrapping (generating of required configuration files, keys, credentials, etc.) is as simple as
`gradle bootstrap`. You may also bootstrap `cega` or `lega` parts separately by calling `gradle createCEGAConfiguration`
and `gradle createLEGAConfiguration` correspondingly, or you can even bootstrap different microservices separately, e.g.
`gradle createLEGAInboxConfiguration`. To clear the configuration execute `gradle clean` (or you can clean only the
subprojects as well).

During bootstrapping, two test users are generated: `john` and `jane`. Credentials, keys and other config information
can be found under `.tmp` folder of each subproject.

## Deploying

After successful bootstrapping, deploying should be as simple as `gradle deploy`. Again, you can deploy `cega` and
`lega` parts separately, but because of dependency on `cega`, `lega` part can be deployed only after the deployment of
`cega`. Updating of stacks can be done completely independently though.

To make sure that the system is deploy you can execute `gradle ls`.

`gradle rm` will remove deployed stacks (yet preserving bootstrapped configuration).

## Testing

There's a built-in simple test to check that the basic scenario works fine. Try to execute `gradle ingest` after
successful deploying to check if ingestion works. It will automatically generate 10MBs file, encrypt it with `Crypt4GH`,
upload to the inbox of test-user `john`, ingest this file and check if it has successfully landed to the vault.

## Portainer

For convenience, as an analogue for Kubernetes Dashboard, the [Portainer](https://portainer.io/) was added to this
deployment. It's accessible at 30000 port. 

![](https://habrastorage.org/webt/js/kv/6y/jskv6yxfauuw11qpiji4q3hjbw8.png)

## Demo

There's a short demo recorded with explanations on provisioning and deployment process:
[![Demo](https://img.youtube.com/vi/8hvXxqW8uP0/0.jpg)](https://www.youtube.com/watch?v=8hvXxqW8uP0)