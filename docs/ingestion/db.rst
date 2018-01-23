Database schema
---------------

We use a Postgres database (version 9.6) to store intermediate data,
in order to track progress in file ingestion. The ``lega`` database
schema is as follows.

.. literalinclude:: /../extras/db.sql
   :language: sql
   :lines: 5-7,13-30,49-55

We do not use any Object-Relational Model (ORM, such as
SQLAlchemy). Instead, we simply implemented, in SQL, a few functions
in order to insert or manipulate the database entry.

.. code-block:: sql

   FUNCTION insert_file(filename    files.filename%TYPE,
			eid         files.elixir_id%TYPE,
			status      files.status%TYPE) RETURNS files.id%TYPE

   FUNCTION insert_error(file_id    errors.file_id%TYPE,
                         msg        errors.msg%TYPE,
                         from_user  errors.from_user%TYPE) RETURNS void


Look at :doc:`the SQL definitions </../extras/db.sql>` if you are also
interested in the database triggers.
