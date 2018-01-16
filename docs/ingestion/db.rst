Database schema
---------------

We use a Postgres database (version 9.6) to store intermediate data,
in order to track progress in file ingestion. The ``lega`` database
schema is as follows.

.. literalinclude:: /../extras/db.sql
   :language: sql
   :lines: 5,6,14-23,94-110,130-136

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

   FUNCTION file_info(fname TEXT, eid TEXT) RETURNS JSON
    
   FUNCTION userfiles_info(eid TEXT) RETURNS JSON

Look at :doc:`the SQL definitions </../extras/db.sql>` if you are also
interested in the database triggers.


..
   .. code-block:: sql

      FUNCTION sanitize_id(elixir_id  users.elixir_id%TYPE)
      RETURNS users.elixir_id%TYPE

      FUNCTION insert_user(elixir_id     users.elixir_id%TYPE,
			   password_hash users.password_hash%TYPE,
			   public_key    users.pubkey%TYPE,
			   exp_int       users.expiration%TYPE DEFAULT INTERVAL '1' MONTH)
       RETURNS users.id%TYPE

       -- Delete other user entries that are too old
       FUNCTION refresh_user(elixir_id users.elixir_id%TYPE)
       RETURNS void

       -- Refresh expiration for user
       FUNCTION update_users()
       RETURNS trigger AS $update_users$ 
       BEGIN
	   DELETE FROM users WHERE last_accessed < current_timestamp - expiration;
	   RETURN NEW;
       END;
       $update_users$ LANGUAGE plpgsql;

       TRIGGER delete_expired_users_trigger AFTER UPDATE ON users EXECUTE PROCEDURE update_users();

       -- Remove user entry from the database cache
       FUNCTION flush_user(elixir_id users.elixir_id%TYPE)
       RETURNS void
