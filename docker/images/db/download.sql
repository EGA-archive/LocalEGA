CREATE SCHEMA local_ega_download;

SET search_path TO local_ega_download;

CREATE TABLE local_ega_download.status (
        id            INTEGER,
	code          VARCHAR(32) NOT NULL,
	description   TEXT,
	-- contraints
	PRIMARY KEY(id), UNIQUE (id), UNIQUE (code)
);

INSERT INTO local_ega_download.status(id,code,description)
VALUES (10, 'INIT'        , 'Initializing a download request'),
       (20, 'REENCRYPTING', 'Re-Encrypting the header for a given user'),
       (30, 'STREAMING'   , 'Streaming file from the Vault'),
       (40, 'DONE'        , 'Download completed'), -- checksums are in the Crypt4GH formatted file
                                                   -- and validated by the decryptor
       (0, 'ERROR'        , 'An Error occured, check the error table');


CREATE TABLE local_ega_download.main (
   id                 SERIAL, PRIMARY KEY(id), UNIQUE (id),

   -- which files was downloaded
   file_id            INTEGER NOT NULL REFERENCES local_ega.main(id), -- No "ON DELETE CASCADE"

   -- Status/Progress
   status             VARCHAR NOT NULL REFERENCES local_ega_download.status (code), -- No "ON DELETE CASCADE"
                      -- DEFAULT 'INIT' ?
   
   -- Stats
   start_timestamp   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
   end_timestamp     TIMESTAMP,
   bytes             INTEGER DEFAULT 0,
   speed             FLOAT   DEFAULT 0.0, -- bytes per seconds

   -- table logs
   created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
   last_modified     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);


-- Insert new request, and return some vault information
CREATE TYPE request_type AS (req_id     INTEGER, -- local_ega_download.main.id%TYPE,
                             file_id    INTEGER, -- local_ega.vault_files.id%TYPE,
			     header     TEXT,    -- local_ega.vault_files.header%TYPE,
			     vault_path TEXT,    -- local_ega.vault_files.vault_file_reference%TYPE,
			     vault_type local_ega.storage);--local_ega.vault_files.vault_file_type%TYPE);

CREATE FUNCTION make_request(sid local_ega.main.stable_id%TYPE)
RETURNS request_type AS $make_request$
#variable_conflict use_column
DECLARE
     req  local_ega_download.request_type;
     vault_rec local_ega.vault_files%ROWTYPE;
     rid  INTEGER;
BEGIN

     SELECT * INTO vault_rec FROM local_ega.vault_files WHERE stable_id = sid LIMIT 1;

     IF vault_rec IS NULL THEN
     	RAISE EXCEPTION 'Vault file not found for stable_id: % ', sid;
     END IF;

     INSERT INTO local_ega_download.main (file_id, status)
     VALUES (vault_rec.id, 'INIT')
     RETURNING local_ega_download.main.id INTO rid;

     req.req_id     := rid;
     req.file_id    := vault_rec.id;
     req.header     := vault_rec.header;
     req.vault_path := vault_rec.vault_file_reference;
     req.vault_type := vault_rec.vault_file_type;
     RETURN req;
END;
$make_request$ LANGUAGE plpgsql;

-- When there is an updated, remember the timestamp
CREATE FUNCTION download_updated()
RETURNS TRIGGER AS $download_updated$
BEGIN
     NEW.last_modified = clock_timestamp();
     RETURN NEW;
END;
$download_updated$ LANGUAGE plpgsql;

CREATE TRIGGER download_updated AFTER UPDATE ON local_ega_download.main FOR EACH ROW EXECUTE PROCEDURE download_updated();


-- Mark a download as complete, and calculate the speed
CREATE FUNCTION download_complete(reqid  local_ega_download.main.id%TYPE,
				  dlsize local_ega_download.main.bytes%TYPE)
RETURNS void AS $download_complete$
DECLARE
     fid local_ega.main.id%TYPE;
     curr_timestamp TIMESTAMP;
BEGIN
     curr_timestamp := clock_timestamp();
     UPDATE local_ega_download.main
     SET status = 'DONE',
         end_timestamp = curr_timestamp,
         bytes = dlsize,
	 speed = dlsize / extract( epoch from (curr_timestamp - start_timestamp)) -- extract (epoch for interval) = elapsed seconds
                                                                                  -- now pray for no div by zero
     WHERE id = reqid
     RETURNING file_id INTO fid;

     -- turn off active errors
     UPDATE local_ega_download.main_errors SET active = FALSE WHERE file_id = fid;
END;
$download_complete$ LANGUAGE plpgsql;


-- ##################################################
--                      ERRORS
-- ##################################################
CREATE TABLE local_ega_download.main_errors (
       id          SERIAL, PRIMARY KEY(id), UNIQUE (id),
       active      BOOLEAN NOT NULL DEFAULT TRUE,
       file_id     INTEGER NOT NULL REFERENCES local_ega.main(id), -- ON DELETE CASCADE,
       req_id      INTEGER NOT NULL REFERENCES local_ega_download.main(id), -- ON DELETE CASCADE,
			
       code        TEXT NOT NULL,
       description TEXT NOT NULL,

       client_ip   TEXT, -- where from
       hostname    TEXT, -- where it happened

       -- table logs
       occured_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

-- Just showing the current/active errors
CREATE VIEW local_ega_download.errors AS
SELECT id, code, description, client_ip, hostname, occured_at FROM local_ega_download.main_errors
WHERE active = TRUE;

CREATE FUNCTION insert_error(req_id    local_ega_download.main.id%TYPE,
                             h         local_ega_download.errors.hostname%TYPE,
                             etype     local_ega_download.errors.code%TYPE,
                             msg       local_ega_download.errors.description%TYPE,
                             client_ip local_ega_download.errors.client_ip%TYPE)
RETURNS void AS $download_error$
DECLARE
     fid local_ega_download.main.file_id%TYPE;
BEGIN

     UPDATE local_ega_download.main
     SET status = 'ERROR'
     WHERE id = req_id
     RETURNING file_id INTO fid;
		 
     IF fid IS NULL THEN
     	RAISE EXCEPTION 'Request id not found: %', req_id;
     END IF;

     INSERT INTO local_ega_download.main_errors (file_id,req_id,hostname,code,description,client_ip)
     VALUES (fid,req_id, h, etype, msg, client_ip);

END;
$download_error$ LANGUAGE plpgsql;
