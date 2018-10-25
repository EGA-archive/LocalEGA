.. _`inbox login system`:

Inbox login system
==================

Central EGA contains a database of users, with IDs and passwords.

We have developed two solutions both of them allowing user authentication via either a password or
an RSA key against CentralEGA database itself:

* :ref:`openssh-inbox`;
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


.. _openssh-inbox:

OpenSSH Inbox
-------------

We use the OpenSSH SFTP server (version 7.7p1), on a Linux
distribution (currently CentOS7).

Authentication is performed by the Operating System, using the classic
plugable mechanism (PAM), and username resolution module (called NSS).

The user's home directory is created when its credentials are
retrieved from CentralEGA. Moreover, we isolate each user in its
respective home directory (i.e. we ``chroot`` the user into it).

We installed a hook inside the OpenSSH SFTP server to detect when a
file is (re)uploaded. The hook runs a checksum on the uploaded file
and notifies CentralEGA via a :doc:`shovel mechanism on the local
message broker <connection>`.

Configuration
^^^^^^^^^^^^^

The NSS and PAM modules are configured by the file ``/etc/ega/auth.conf``.

Some configuration parameters can be specified, while others have
default values in case they are not specified. Some of the parameters must be
specified (mostly those for which we can't invent a value!).

A sample configuration file can be found on the `LocalEGA-auth
repository
<https://github.com/NBISweden/LocalEGA-auth/blob/master/auth.conf.sample>`_,
eg:

.. code-block:: none

   ##########################################
   # Remote database settings (using ReST)
   ##########################################
   
   # The username will be appended to the endpoints
   cega_endpoint_name = http://cega_users/user/
   cega_endpoint_uid = http://cega_users/id/
   cega_creds = user:password
   
   # Selects where the JSON object is rooted
   # Use a dotted format à la JQ, eg level1.level2.level3
   # Default: empty
   cega_json_prefix = 
   
   ##########################################
   # Local database settings (for NSS & PAM)
   ##########################################

   # Absolute path to the SQLite database.
   # Required setting. No default value.
   db_path = /run/ega-users.db
   
   # Sets how long a cache entry is valid, in seconds.
   # Default: 3600 (ie 1h).
   # cache_ttl = 86400
   
   # Per site configuration, to shift the users id range
   # Default: 10000
   #ega_uid_shift = 1000
   
   # The group to which all users belong.
   # For the moment, only only.
   # Required setting. No default.
   ega_gid = 997
   
   # This causes the PAM sessions to be chrooted into the user's home directory.
   # Useful for SFTP connections, but complicated for regular ssh
   # connections (since no proper environment exists there).
   # Default: false
   chroot_sessions = yes
   
   # Per site configuration, where the home directories are located
   # The user's name will be appended.
   # Required setting. No default.
   ega_dir = /ega/inbox
   ega_dir_attrs = 2750 # rwxr-s---
   
   # sets the umask for each session (in octal format)
   # Default: 027 # world-denied
   #ega_dir_umask = 027
   
   # When the password is asked
   # Default: "Please, enter your EGA password: "
   #prompt = Knock Knock:
   
   # The user's login shell.
   # Default: /bin/bash
   #ega_shell = /bin/aspshell-r


.. note:: After proper configuration, there is no user maintenance, it is
   automagic. The other advantage is to have a central location of the
   EGA users.

   Moreover, it is also possible to add non-EGA users if necessary, by
   reproducing the same mechanism but outside the temporary
   cache. Those users will persist upon reboot.


Implementation
^^^^^^^^^^^^^^

The cache is a SQLite database, mounted in a ``ramfs`` partition (of
initial size 200M). A ``ramfs`` partition does not survive a reboot,
grows dynamically and does not use the swap partition (as a ``tmpfs``
partition would). By default such option is disabled but can be
enabled in the `inbox` entrypoint script.

The NSS+PAM source code has its own `repository
<https://github.com/NBISweden/LocalEGA-auth>`_. A makefile is provided
to compile and install the necessary shared libraries.
The repository also provides an automated build for a new image:
``nbisweden/ega-openssh``.

We copied the ``sshd`` into an ``/opt/openshh/sbin/ega`` binary and
configured the *ega* service by adding a file into the ``/etc/pam.d``
directory. In this case, the name of the file is ``/etc/pam.d/ega``.

.. literalinclude:: /../docker/images/inbox/pam.ega

The *ega* service is configured using the ``-c`` switch to specify
where the configuration file is. The service runs for the moment on
port 9000.

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
*type* is configured to deny every access).

The ``session`` *type* handles the chrooting.

The ``account`` *type* of the PAM module is a pass-through. It
succeeds. It also "refreshes" the cache information is case it has
expired. This cache expiration mechanism will capture the situation
where the user's credentials have been reset. If the user stays logged
in and idle, the ssh session will expire. If the user is not idle,
then it is the same behaviour as if the user account was created
locally (ie. in /etc/passwd and /etc/shadow).


.. _apache-mina-inbox:

Apache Mina Inbox
-----------------

This solution makes use of `Apache Mina SSHD project <https://mina.apache.org/sshd-project/>`_,
the user is locked within their home folder, which is done by using `RootedFileSystem
<https://github.com/apache/mina-sshd/blob/master/sshd-core/src/main/java/org/apache/sshd/common/file/root/RootedFileSystem.java>`_.

The user's home directory is created upon successful login.
Moreover, for each user, we detect when the file upload is completed and compute its
checksum. This information is provided to CentralEGA via a
:doc:`shovel mechanism on the local message broker <connection>`.
We can configure default cache TTL via ``CACHE_TTL`` environment variable.

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
performance asynchronous IO API to support the SSH (and SFTP) protocols.

Sources are located at the separate repo: https://github.com/NBISweden/LocalEGA-inbox
Essentially, it's a Spring-based Maven project, integrated to a common LocalEGA MQ bus.
