.. _`inbox login system`:

Inbox login system
==================

Central EGA contains a database of users, with IDs and passwords.

We have developed a solution allowing user authentication via either a
password or an RSA key against CentralEGA database itself:

The solution uses CentralEGA's user IDs but can also be extended to
use Elixir IDs (of which we strip the ``@elixir-europe.org`` suffix).

The procedure is as follows: the inbox is started without any created
user. When a user wants to log into the inbox (actually, only ``sftp``
uploads are allowed), the code looks up the username in a local
cache, and, if not found, queries the CentralEGA's REST endpoint. Upon
return, we store the user credentials in the local cache and create
the user's home directory. The user now gets logged in if the password
or public key authentication succeeds. Upon subsequent login attempts,
only the local cache is queried, until the user's credentials
expire. The cache has a default TTL of one hour, and is wiped clean
upon reboot (as a cache should).

We use the OpenSSH SFTP server (version 7.7p1), on a Linux
distribution (currently CentOS7).

Authentication is performed by the Operating System, using the classic
plugable mechanism (PAM), and username resolution module (NSS).

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

A `sample configuration file
<https://github.com/EGA-archive/EGA-auth/blob/master/auth.conf.sample>`_,
including comments, can be found on the `EGA-auth repository
<https://github.com/EGA-archive/EGA-auth>`_.

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
<https://github.com/EGA-archive/EGA-auth>`_. A makefile is provided
to compile and install the necessary shared libraries.

We copied the ``sshd`` into an ``/opt/openshh/sbin/ega`` binary and
configured the *ega* service by adding a file into the ``/etc/pam.d``
directory. In this case, the name of the file is ``/etc/pam.d/ega``.

.. literalinclude:: /../deploy/images/inbox/pam.ega

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
succeeds if the user exists at CentralEGA and has access to that
LocalEGA instance.
