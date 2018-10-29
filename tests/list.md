File Upload
===========

* (U.1) User does not exist
* (U.2) User does not have rights to access this Local EGA
* (U.3) User authentication failed: password or ssh-key
* (U.4) User authentication succeeds but user inbox not created: ssh/sftp access denied
* (U.5) Database connection fails, so user information is not available
* (U.6) User tries to login via something else than ssh/sftp

File Ingestion
==============

* (I.1) User applies the wrong encryption protocol (ie not OpenPGP)
* (I.2) User uses the wrong GPG key or sends it to the wrong LocalEGA
* (I.3) Ingestion starts but inbox not created
* (I.4) Ingestion starts but file not found in inbox
* (I.5) File found but its checksum doesn't match with the supplied one
* (I.6) File found but its checksum doesn't match with the companion file
* (I.7) File found, no checksum supplied and no companion file
* (I.8) File found, its checksum is correct but the GPG decryption fails (and why)
  > To be expanded. That item comprises many tests!
  > eg Keyserver communication fails: Server down, SSL encryption channel is not set up...
  > GPG key not found, GPG key not unlocked etc
* (I.9) File found, its checkusum is valid, the GPG decryption succeed but the checksum of the decrypted doesn't match with the supplied one
* (I.10) File found, its checkusum is valid, the GPG decryption succeed but the checksum of the decrypted doesn't match with the companion file
* (I.11) File found, ...., but re-encryption fails (and why)
  > To be expanded. This item comprises many tests!
  > eg key not found
* (I.12) Re-encryption failure due shortage in the staging area
  > To be expanded. This item comprises many tests!
  > eg disk full, or mount failed, ...
* (I.13) Moving to staging area failed
  > Vault listener is down, vault disk is full, staging area mount failed, etc...
* (I.14) Verification of the copied file in the vault failed
  > The file was not fully copied, so its checksum failed (calculated at the re-encryption step).
* (I.15) Database connection failed, so information about the file is not available

Robustness
==========

* (R.1) Everything works after a system reboot (manually or power outage)
* (R.2) Some components are restarted (especially the database, but also the ingestion workers or the vault)
* (R.3) Stress tests:
  - (R.3a) ingesting a big file
  - (R.3b) ingesting many files
