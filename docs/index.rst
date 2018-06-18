Throughout this documentation, we can refer to Central EGA as
``CEGA``, or ``CentralEGA``, and *any* Local EGA instance as ``LEGA``,
or ``LocalEGA``.  When two or more Local EGA instances are involved,
we will use ``LEGA<i>`` for Local EGA instance ``<i>``.

================
Local EGA
================

The Local EGA project is divided into several microservices.

.. raw:: html
   :file: table.html

The workflow consists of two ordered parts:

The user first logs onto the Local EGA's inbox and uploads its
files. He/She then goes to the Central EGA's interface to prepare a
submission. Upon completion, the files are ingested into the vault and
become searchable by the Central EGA's engine.

----

More concretely, Central EGA contains a database of users. The Central
EGA' ID is used to authenticate the user against either their EGA
password or an RSA key.

For every uploaded file, Central EGA receives a notification that the
file has landed. The file is checksumed and presented in the Central
EGA's interface in order for the user to double-check that it was
properly uploaded.

|moreabout| More details about the :ref:`inbox login system`.

When a submission is ready, Central EGA triggers an ingestion process
on the user-chosen Local EGA instance. The uploaded file must be
encrypted using the OpenPGP protocol and that Local EGA instance
key. The file is first decrypted by the LocalEGA instance and then
re-encrypted into its vault. Central EGA's interface is then updated
with notifications whether the ingestion went right, whether there was
an error or if the process is still under progress.

|moreabout| More details about the :ref:`ingestion process`.

----

Getting started
===============

.. toctree::
   :maxdepth: 2
   :name: setup

   Getting started      <setup>

Information about the Architecture
==================================

.. toctree::
   :maxdepth: 2
   :name: architecture

   Inbox                <inbox>
   Ingestion            <ingestion/overview.rst>
   Encryption           <ingestion/encryption.rst>
   Database             <ingestion/db.rst>
   CEGA from/to LEGA    <connection>

Miscellaneous
=============

.. toctree::
   :maxdepth: 1
   :name: extra

   Python Modules       <code>
   Contributing         <CONTRIBUTING>
   Testsuite            <tests/overview.rst>
   policies

|Codacy| | |Travis| | Version |version| | Generated |today|


.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/3dd83b28ec2041889bfb13641da76c5b
	:alt: Codacy Badge
	:class: inline-baseline

.. |Travis| image:: https://travis-ci.org/NBISweden/LocalEGA.svg?branch=dev
	:alt: Build Status
	:class: inline-baseline

.. |moreabout| unicode:: U+261E .. right pointing finger
.. |connect| unicode:: U+21cc .. <-_>
