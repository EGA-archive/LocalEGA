# Docker Swarm Deployment

![](https://habrastorage.org/webt/zt/rm/bk/ztrmbknpfaz9ybmoy3j12x5tlcw.gif)

## Prerequisites

The deployment tool of LocalEGA for Docker Swarm is based on [Gradle](https://gradle.org/), so you will need Gradle to
be installed on your machine in order to use it. On MacOS with Homebrew it can be done by executing
`brew install gradle`. Please, refer to official documentation to find instruction for other platforms.

Make sure [Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy](http://www.oracle.com/technetwork/java/javase/downloads/jce8-download-2133166.html) is set up.

Also this tool doesn't (at least yet) create a Swarm cluster for you, so one needs to have it beforehand. Creation of
such a cluster is currently out of the scope of this instructions.

## Structure

Gradle project has the following structure:

![](https://habrastorage.org/webt/bp/6r/sh/bp6rshamdpwd53lhzbobpcqct6a.png)

- `cega` - "fake" CentralEGA
- `lega` - main LocalEGA microservices
- `LocalEGA` - root project aggregating both of the above

Also there are multiple groups of tasks in the project:
- `cega` - for spinning up Central EGA part
- `lega` - for spinning up Local EGA part
- `swarm` - for spinning up both
- `test` - for testing the setup

## Bootstrapping

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
deployment. It's accessible at http://localhost:30000/#/dashboard

![](https://habrastorage.org/webt/js/kv/6y/jskv6yxfauuw11qpiji4q3hjbw8.png)
