-- \connect lega

-- We use schemas for isolation instead of multiple databases.
-- Look at the grants.sql file, for access user/role rights setup

CREATE SCHEMA local_ega; -- includes the main table, some views and errors

SET search_path TO local_ega;

CREATE TYPE checksum_algorithm AS ENUM ('MD5', 'SHA256', 'SHA384', 'SHA512'); -- md5 is bad. Use sha*!
CREATE TYPE storage AS ENUM ('S3', 'POSIX');
-- Note: This is an enum, because that's what the "provided" database supports
--       If a site has its own database already, let them define their keyword in the ENUM 
--       and use it (Notice that their code must be update to push this value into the table)
--       There is no need to agree on how each site should operate their own database
--       What we need is to document where they need to update and what.


-- ##################################################
--                  FILE STATUS
-- ##################################################
CREATE TABLE local_ega.status (
        id            INTEGER,
	code          VARCHAR(16) NOT NULL,
	description   TEXT,
	-- contraints
	PRIMARY KEY(id), UNIQUE (id), UNIQUE (code)
);

INSERT INTO local_ega.status(id,code,description)
VALUES (10, 'INIT'        , 'Initializing a file ingestion'),
       (20, 'VERIFIED'    , 'File copied to the staging area, and verified'),
       (30, 'BACKUP1'     , 'File in the vault'),
       (31, 'BACKUP2'     , 'File in the 2nd vault'),
       (40, 'COMPLETED'   , 'File backed up into the vault'),
       (0,  'ERROR'       , 'An Error occured, check the error table'),
       (1,  'CANCELED'    , 'Used for submissions that are stopped, overwritten, or to be cleaned up')
;

-- ##################################################
--                        FILES
-- ##################################################

CREATE TABLE local_ega.main (

       id                     SERIAL, PRIMARY KEY(id), UNIQUE (id),
       correlation_id         TEXT NOT NULL,
       occurences	      INTEGER NOT NULL DEFAULT 1,

       -- Original/Encrypted Submission file
       inbox_user             TEXT NOT NULL, -- Elixir ID, or internal user
       inbox_path             TEXT NOT NULL,

       inbox_path_encrypted_checksum       VARCHAR(128) NULL,
       inbox_path_encrypted_checksum_type  checksum_algorithm,

       inbox_path_size                     BIGINT NULL,

       -- constraint
       -- UNIQUE (correlation_id, inbox_user, inbox_path), --, inbox_path_encrypted_sha256),


       -- Status
       status                 VARCHAR NOT NULL REFERENCES local_ega.status (code) DEFAULT 'INIT',
       			      -- No "ON DELETE CASCADE": update to the new status in case the old one is deleted

       -- Staging information
       staging_relative_path  TEXT,

       -- Archive information
       header                 TEXT, -- Crypt4GH header
       encrypted_payload_size           BIGINT,
       encrypted_payload_checksum       VARCHAR(128) NULL, -- NOT NULL,
       encrypted_payload_checksum_type  checksum_algorithm,
       encrypted_payload_file_type      storage, -- S3 or POSIX file system
       
       accession_id           TEXT, UNIQUE (accession_id),

       -- Errors
       hostname      TEXT,
       error_type    TEXT,
       error_msg     TEXT,
       from_user     BOOLEAN DEFAULT FALSE,
       -- error_at    TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp()

       -- Table Audit / Logs
       created_by             NAME DEFAULT CURRENT_USER, -- Postgres users
       last_modified_by       NAME DEFAULT CURRENT_USER, --
       created_at             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
       last_modified          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);
CREATE UNIQUE INDEX main_idx ON local_ega.main(id);



-- When there is an updated, remember the timestamp
CREATE FUNCTION main_updated()
RETURNS TRIGGER AS $main_updated$
BEGIN
     NEW.last_modified = clock_timestamp();
		 RETURN NEW;
END;
$main_updated$ LANGUAGE plpgsql;

CREATE TRIGGER main_updated AFTER UPDATE ON local_ega.main FOR EACH ROW EXECUTE PROCEDURE main_updated();


-- ##################################################
--         Jobs View
-- ##################################################
-- 
CREATE VIEW local_ega.jobs AS
SELECT id,
       correlation_id,
       occurences,
       inbox_user                      AS user_id,
       inbox_path,
       inbox_path_encrypted_checksum   AS inbox_checksum,
       inbox_path_encrypted_checksum_type AS inbox_checksum_type,
       staging_relative_path,
       status,
       header,  -- Crypt4gh specific
       encrypted_payload_size          AS payload_size,
       encrypted_payload_checksum      AS payload_checksum,
       encrypted_payload_checksum_type AS payload_checksum_type,
       accession_id
FROM local_ega.main;

-- Insert into main
CREATE FUNCTION local_ega.insert_job(cid           local_ega.jobs.correlation_id%TYPE,
			             inpath        local_ega.jobs.inbox_path%TYPE,
			             uid           local_ega.jobs.user_id%TYPE,
			             checksum      local_ega.jobs.inbox_checksum%TYPE,
			             checksum_type local_ega.jobs.inbox_checksum_type%TYPE)
RETURNS local_ega.jobs.id%TYPE AS $insert_job$
    #variable_conflict use_column
    DECLARE
        job_id  local_ega.jobs.id%TYPE;
	found_updates INTEGER;
    BEGIN

	IF checksum IS NULL THEN
	   -- If sha256 is NULL, then we create a new job all the time and 
	   -- mark the other ongoing ones as canceled (ie not in error or completed state)
	   UPDATE local_ega.jobs SET status = 'CANCELED'
	                   WHERE correlation_id = cid AND
	  	                 inbox_path = inpath AND
	  	              	 user_id = uid AND
			      	 NOT (status = 'ERROR' OR status = 'COMPLETED');
	   -- Insert a new job anyhow
	   INSERT INTO local_ega.jobs (correlation_id,inbox_path,user_id)
	   VALUES(cid,inpath,uid) RETURNING local_ega.jobs.id INTO job_id;

	ELSE
	   -- If checksum is NOT NULL, then we know more about that particular file.
	   -- If a job is not CANCELED/ERROR, then we increment the occurences count and return -1 
	   -- (ie not need to work), otherwise, we insert a new job.
	   UPDATE local_ega.jobs SET occurences = occurences + 1
	                   WHERE correlation_id = cid AND
	  	                 inbox_path = inpath AND
				 user_id = uid AND
	  	              	 inbox_path_encrypted_checksum = checksum AND
	  	              	 inbox_path_encrypted_checksum_type = checksum_type AND
			      	 NOT (status = 'ERROR' OR status = 'CANCELED');
	   IF FOUND THEN RETURN -1; END IF;

	   -- If not found, make a new insertion
	   INSERT INTO local_ega.jobs (correlation_id,inbox_path,user_id,inbox_path_encrypted_checksum,inbox_path_encrypted_checksum_type)
	   VALUES(cid,inpath,uid,checksum,checksum_type)
	   ON CONFLICT -- ON CONSTRAINT (correlation_id,inbox_path,user_id,inbox_sha256)
	   DO NOTHING -- UPDATE SET status = 'CANCELED' -- data race here ?
	              --        WHEN NOT (status = 'ERROR' OR status = 'COMPLETED')
	   RETURNING local_ega.jobs.id
	   INTO job_id;
	END IF;

	RETURN job_id;
    END;
$insert_job$ LANGUAGE plpgsql;

-- Mark job as canceled
CREATE FUNCTION local_ega.cancel_job(cid           local_ega.jobs.correlation_id%TYPE,
		   	             inpath        local_ega.jobs.inbox_path%TYPE,
			             uid           local_ega.jobs.user_id%TYPE,
		     	             checksum      local_ega.jobs.inbox_checksum%TYPE,
			             checksum_type local_ega.jobs.inbox_checksum_type%TYPE)
RETURNS void AS $cancel_job$
    #variable_conflict use_column
    BEGIN
        UPDATE local_ega.jobs SET status = 'CANCELED'
	       		WHERE correlation_id = cid AND
			      inbox_path = inpath AND
			      inbox_user = uid AND
			      (CASE WHEN checksum is NULL
			            THEN TRUE
				    ELSE inbox_path_encrypted_checksum = checksum AND 
				         inbox_path_encrypted_checksum_type = checksum_type
			       END) AND
			      NOT (status = 'ERROR' OR status = 'COMPLETED');
    END;
$cancel_job$ LANGUAGE plpgsql;

CREATE FUNCTION has_status(fid local_ega.jobs.id%TYPE, statuses status[])
RETURNS boolean AS $has_status$
#variable_conflict use_column
BEGIN
   RETURN EXISTS(SELECT 1 FROM local_ega.jobs WHERE id = fid AND (status = ANY(statuses)));
END;
$has_status$ LANGUAGE plpgsql;


-- ##################################################
--                      ERRORS
-- ##################################################

-- Just showing the current/active errors
CREATE VIEW local_ega.errors AS
SELECT id,
       correlation_id,
       hostname,
       error_type,
       error_msg       AS message,
       from_user,
       last_modified   AS error_at
FROM local_ega.main;

CREATE FUNCTION insert_error(jid        local_ega.errors.id%TYPE,
                             h          local_ega.errors.hostname%TYPE,
                             etype      local_ega.errors.error_type%TYPE,
                             msg        local_ega.errors.message%TYPE,
                             from_user  local_ega.errors.from_user%TYPE)
    RETURNS void AS $insert_error$
    BEGIN
       UPDATE local_ega.jobs
              SET status = 'ERROR',
	          hostname = h,
		  error_type = etype,
		  error_msg = msg,
		  from_user = from_user
	      WHERE id = jid;
    END;
$insert_error$ LANGUAGE plpgsql;


-- ##################################################
--              Session Keys Checksums
-- ##################################################
-- To keep track of already used session keys,
-- we record their checksum
CREATE TABLE local_ega.session_key_checksums_sha256 (
       session_key_checksum      VARCHAR(128) NOT NULL, PRIMARY KEY(session_key_checksum), UNIQUE (session_key_checksum),
       job_id                    INTEGER NOT NULL REFERENCES local_ega.main(id) ON DELETE CASCADE
);


-- Returns if the session key checksums are already found in the database
CREATE FUNCTION check_session_keys_checksums_sha256(checksums text[]) --local_ega.session_key_checksums.session_key_checksum%TYPE []
    RETURNS boolean AS $check_session_keys_checksums_sha256$
    #variable_conflict use_column
    BEGIN
	RETURN EXISTS(SELECT 1
                      FROM local_ega.session_key_checksums_sha256 sk 
	              INNER JOIN local_ega.jobs f
		      ON f.id = sk.job_id 
		      WHERE (f.status <> 'ERROR' AND f.status <> 'CANCELED') AND -- no data-race on those values
		      	    sk.session_key_checksum = ANY(checksums));
    END;
$check_session_keys_checksums_sha256$ LANGUAGE plpgsql;


-- Insert all the checksums for a given job_id
CREATE FUNCTION insert_session_keys_checksums_sha256(jid        local_ega.jobs.id%TYPE,
                                                     checksums  text[])
    RETURNS VOID AS $insert_session_keys_checksums_sha256$
    #variable_conflict use_column
    BEGIN
	INSERT INTO local_ega.session_key_checksums_sha256(job_id,session_key_checksum)
               (SELECT jid AS job_id, t.session_key_checksum
	          FROM (SELECT unnest(checksums) AS session_key_checksum)
		   as t);
    END;
$insert_session_keys_checksums_sha256$ LANGUAGE plpgsql;


-- ##########################################################################
--                   User credentials
-- ##########################################################################

-- NOTE: since we only have one user: lega_in
-- we grant it access directly inside of setting up roles
CREATE USER lega;

-- Set up rights access for local_ega schema
GRANT USAGE ON SCHEMA local_ega TO lega;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA local_ega TO lega; -- Read/Write access on local_ega.* for lega
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA local_ega TO lega; -- Don't forget the sequences
