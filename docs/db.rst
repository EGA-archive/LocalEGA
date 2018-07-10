Database schema
---------------

We use a Postgres database (version 9.6) to store intermediate data,
in order to track progress in file ingestion. The ``lega`` database
schema is as follows.

.. literalinclude:: /../extras/db.sql
   :language: sql
   :lines: 5,12-25,44-53

We do not use any Object-Relational Model (ORM, such as
SQLAlchemy). Instead, we simply implemented, in SQL, a few functions
in order to insert or manipulate the database entry.

.. code-block:: sql

   FUNCTION insert_file(inpath files.inbox_path%TYPE,
		        eid    files.elixir_id%TYPE,
			sid    files.stable_id%TYPE,
			status files.status%TYPE) RETURNS files.id%TYPE

   FUNCTION insert_error(fid   errors.file_id%TYPE,
                         h     errors.hostname%TYPE,
                         etype errors.error_type%TYPE,
                         msg   errors.msg%TYPE,
                         from_user  errors.from_user%TYPE) RETURNS void


Look at `the SQL definitions
<https://github.com/NBISweden/LocalEGA/blob/dev/extras/db.sql>`_ if
you are also interested in the database triggers.
