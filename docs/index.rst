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
encrypted in the :download:`Crypt4GH file format
<./static/crypt4gh.pdf>` using that Local EGA's public PGP
key. Central EGA's interface is updated with progress notifications
whether the ingestion was successful, or whether there was an error.

|moreabout| More details about the :ref:`ingestion process`.

.. image:: /static/components.png
   :target: ./_static/components.png
   :alt: General Architecture and Connected Components

----

Getting started
===============

.. toctree::
   :maxdepth: 2
   :name: setup

   Getting started      <setup>
   Bootstrap & Deploy   <bootstrap>

Information about the Architecture
==================================

.. toctree::
   :maxdepth: 2
   :name: architecture

   Inbox                <inbox>
   Ingestion            <ingestion>
   Encryption           <encryption>
   Keyserver            <keyserver>
   Database             <db>
   CEGA from/to LEGA    <connection>

Miscellaneous
=============

.. toctree::
   :maxdepth: 1
   :name: extra

   Python Modules       <code>
   Testsuite            <tests>
   Contributing         <CONTRIBUTING>

|Codacy| | |Travis| | Version |version| | Generated |today|


.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/3dd83b28ec2041889bfb13641da76c5b
	:alt: Codacy Badge
	:class: inline-baseline

.. |Travis| image:: https://travis-ci.org/NBISweden/LocalEGA.svg?branch=dev
	:alt: Build Status
	:class: inline-baseline

.. |moreabout| unicode:: U+261E .. right pointing finger
.. |connect| unicode:: U+21cc .. <-_>
