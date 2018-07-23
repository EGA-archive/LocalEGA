.. _`inbox login system`:

Inbox login system
==================

Central EGA contains a database of users, with IDs and passwords.

We have developed two solutions both of them allowing user authentication via either a password or
an RSA key against CentralEGA database itself:

* :ref:`nss-pam-inbox` also known as FUSE based inbox;
* :ref:`apache-mina-inbox`.

Each solution uses CentralEGA's user IDs but can also be extended to
use Elixir IDs (of which we strip the ``@elixir-europe.org`` suffix).

The procedure is as follows: the inbox is started without any created
user. When a user wants to log into the inbox (actually, only ``sftp``
uploads are allowed), the code looks up the username in a local
cache, and, if not found, queries the CentralEGA REST endpoint. Upon
return, we store the user credentials in the local cache and create
the user's home directory. The user now gets logged in if the password
or public key authentication succeeds. Upon subsequent login attempts,
only the local cache is queried, until the user's credentials
expire. The cache has a default TTL of one hour, and is wiped clean
upon reboot (as a cache should).


.. _nss-pam-inbox:

NSS+PAM Inbox
-------------

The user's home directory is created when its credentials are retrieved
from CentralEGA. Moreover, for each user, we use FUSE mountpoint and
``chroot`` the user into it. The FUSE application is in charge of
detecting when the file upload is completed and computing its
checksum. This information is provided to CentralEGA via a
:doc:`shovel mechanism on the local message broker <connection>`.

Configuration
^^^^^^^^^^^^^

The NSS and PAM modules look at ``/etc/ega/auth.conf``.

Some configuration parameters can be specified, while others have
default values in case they are not specified. Some of the parameters must be
specified (mostly those for which we can invent a value!).

A sample configuration file can be found on the `LocalEGA-auth
repository
<https://github.com/NBISweden/LocalEGA-auth/blob/master/auth.conf.sample>`_,
eg:

.. code-block:: none

   ##################
   # Central EGA
   #
   # The username will be appended to the endpoint
   # eg the endpoint for 'john' will be
   # http://cega_users/user/john
   #
   # Note: Change the cega_creds !
   #
   ##################

   enable_cega = yes
   cega_endpoint = http://cega_users/user/
   cega_creds = user:password
   cega_json_passwd = .password
   cega_json_pubkey = .public_key

   ##################
   # NSS & PAM
   ##################

   cache_ttl = 36000.0 # Float in seconds... Here 10 hours
   prompt    = Knock Knock:
   cache_dir = /ega/cache
   ega_gecos = EGA User
   ega_shell = /sbin/nologin

   ega_uid = 1000
   ega_gid = 1000

   ega_dir = /ega/inbox
   ega_dir_attrs = 2750 # rwxr-s---

   ##################
   # FUSE mount
   ##################
   ega_fuse_exec = /usr/bin/ega-inbox
   ega_fuse_flags = nodev,noexec,suid,default_permissions,allow_other,uid=1000,gid=1000



We use the following default values if the option is not specified in
the configuration file.

.. code-block:: bash

   cache_ttl   = 3600.0 // 1 hour
   enable_cega = "yes"
   cache_dir   = "/ega/cache"
   prompt      = "Please, enter your EGA password: "
   ega_gecos   = "EGA User"
   ega_shell   = "/sbin/nologin"


.. note:: After proper configuration, there is no user maintenance, it is
   automagic. The other advantage is to have a central location of the
   EGA users.

   Moreover, it is also possible to add non-EGA users if necessary, by
   reproducing the same mechanism but outside the temporary
   cache. Those users will persist upon reboot.


Implementation
^^^^^^^^^^^^^^

The cache directory can be mounted as a ``ramfs`` partition of size
200M. We use a directory per user, containing files for the user's
password hash, ssh key and last access record. Files and directories
in the cache are stored in memory, not on disk, giving us an extra
performance boost. A ``ramfs`` partition does not survive a reboot, grow
dynamically and does not use the swap partition (as a ``tmpfs`` partition
would). By default such option is disabled but can be enabled in the `inbox`
entrypoint script.

We use OpenSSH (version 7.5p1) and its ``sftp`` component. The NSS+PAM
source code has its own `repository
<https://github.com/NBISweden/LocalEGA-auth>`_. A makefile is provided
to compile and install the necessary shared libraries.

We copied the ``/sbin/sshd`` into an ``/sbin/ega`` binary and
configured the *ega* service by adding a file into the ``/etc/pam.d``
directory. In this case, the name of the file is ``/etc/pam.d/ega``.

.. literalinclude:: /../deployments/docker/images/inbox/pam.ega

The *ega* service is configured just like ``sshd`` is. We only use the
``-c`` switch to specify where the configuration file is. The service
runs for the moment on port 9000.

Note that when PAM is configured as above, and a user is either not
found, or its authentication fails, the access to the service is
denied. No other user (not even root), other than Central EGA users,
have access to that service.

The authentication code of the library (ie the ``auth`` *type*) checks
whether the user has a valid ssh public key. If it is not the case,
the user is prompted to input a password. Central EGA stores password
hashes using the `BLOWFISH
<https://en.wikipedia.org/wiki/Blowfish_(cipher)>`_ hashing
algorithm. LocalEGA also supports the usual ``md5``, ``sha256`` and
``sha512`` algorithms available on most Linux distribution (They are
part of the C library).

Updating a user password is not allowed (ie therefore the ``password``
*type* is configure to deny every access).

The ``session`` *type* handles the FUSE mount and chrooting.

The ``account`` *type* of the PAM module is a pass-through. It
succeeds.

"Refreshing" the last access time is done by the ``setcred``
service. The latter is usually called before a session is open, and
after a session is closed. Since we are in a chrooted environment when
the session closes, ``setcred`` is bound to fail. However, it
succeeded on the original login, and it will again on the subsequent
logins. That way, if a user logs in again, within a cache TTL delay,
we do not re-query the CentralEGA database. After the TTL has elapsed,
we do query anew the CentralEGA database, eventually receiving new
credentials for that user.

Note that it is unlikely that a user will keep logging in and out,
while its password and/or ssh key have been reset. If so, we can
implement a flush mechanism, given to CentralEGA, if necessary (not
complicated, and ... not a priority).


.. _apache-mina-inbox:

Apache Mina Inbox
-----------------

This solution makes use of `Apache Mina SSHD project <https://mina.apache.org/sshd-project/>`_,
the user is locked within their home folder, which is done by using `RootedFileSystem
<https://github.com/apache/mina-sshd/blob/master/sshd-core/src/main/java/org/apache/sshd/common/file/root/RootedFileSystem.java>`_.

The user's home directory is created when its credentials upon successful login.
Moreover, for each user, we detect when the file upload is completed and compute its
checksum. This information is provided to CentralEGA via a
:doc:`shovel mechanism on the local message broker <connection>`.
We can configure default cache TTL via ``CACHE_TTL`` env var.

Configuration
^^^^^^^^^^^^^

Environment variables used:

+------------------+---------------+
| Variable name    | Default value |
+==================+===============+
| BROKER_USERNAME  | guest         |
+------------------+---------------+
| BROKER_PASSWORD  | guest         |
+------------------+---------------+
| BROKER_HOST      | mq            |
+------------------+---------------+
| BROKER_PORT      | 5672          |
+------------------+---------------+
| INBOX_PORT       | 2222          |
+------------------+---------------+
| INBOX_LOCATION   | /ega/inbox/   |
+------------------+---------------+
| CACHE_TTL        | 3600.0        |
+------------------+---------------+
| CEGA_ENDPOINT    |               |
+------------------+---------------+
| CACHE_TTL        |               |
+------------------+---------------+

Implementation
^^^^^^^^^^^^^^

As mentioned above, the implementation is based on Java library Apache Mina SSHD. It provides a scalable and high
performance asynchronous IO API to support the SSH (and SFPT) protocols on both the client and server side.

Sources are located at the separate repo: https://github.com/NBISweden/LocalEGA-inbox
Basically, it's a Spring-based Maven project, integrated to a common LocalEGA MQ bus.
