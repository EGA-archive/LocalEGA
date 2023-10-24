CREATE FUNCTION public.sys2db_user_id(_sys_uid bigint)
RETURNS bigint
LANGUAGE SQL
AS $_$
   SELECT _sys_uid - 10000;
$_$;

CREATE FUNCTION public.db2sys_user_id(_db_uid bigint)
RETURNS bigint
LANGUAGE SQL
AS $_$
   SELECT _db_uid + 10000;
$_$;


------------
-- GROUPS --
------------

CREATE TABLE public.group_table (

  id      		BIGSERIAL PRIMARY KEY,
  name    		varchar(64),
  description 		text,
  is_enabled            boolean NOT NULL DEFAULT true,

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()

);


-----------
-- USERS --
-----------

CREATE TABLE public.user_table
(
    id                 BIGSERIAL PRIMARY KEY,
--    stable_id          text,
    username           text NOT NULL UNIQUE,
    gecos              text,
    group_id           bigint NOT NULL, -- main group
    is_enabled          boolean NOT NULL DEFAULT TRUE,

    -- info about the person
    full_name		text, -- NOT NULL,
    email		text UNIQUE, -- NOT NULL,
    institution		text,
    country		text, -- NOT NULL,

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);

CREATE TABLE public.user_group_table (
    id         		BIGSERIAL PRIMARY KEY,
    user_id    		bigint NOT NULL REFERENCES public.user_table(id),
    group_id    	bigint NOT NULL REFERENCES public.group_table(id),

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);


----------
-- KEYS --
----------

CREATE TYPE public.key_type AS ENUM(
       'ssh'
     , 'ssh-ed25519'
     , 'c4gh-v1'
);

CREATE TABLE public.user_key_table (

    id         		BIGSERIAL PRIMARY KEY,
    user_id    		bigint NOT NULL REFERENCES public.user_table(id),
 
    key        		text NOT NULL, -- public key content
    type       		public.key_type NOT NULL,

    --is_internal		bool NOT NULL DEFAULT FALSE,
    --expires_at 		timestamp(6) with time zone,

    -- Local column (not replicated)
    pubkey              bytea,

    --UNIQUE (user_id, key)
    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);


CREATE FUNCTION public.parse_crypt4gh_key()
    RETURNS trigger
    LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
	IF NEW.type IN ('ssh-ed25519', 'c4gh-v1') THEN
           NEW.pubkey = crypt4gh.parse_pubkey(NEW.key);
	END IF;
        RETURN NEW;
END;
$BODY$;


CREATE TRIGGER parse_crypt4gh_key
BEFORE INSERT OR UPDATE ON public.user_key_table
FOR EACH ROW
EXECUTE FUNCTION public.parse_crypt4gh_key();


--------------
-- DATASETS --
--------------


CREATE TYPE public.access_type AS ENUM('public', 'registered', 'controlled');

CREATE TABLE public.dataset_table(
        --id              BIGSERIAL PRIMARY KEY,

        stable_id       text NOT NULL PRIMARY KEY, -- UNIQUE,
	title		text, --NOT NULL,
	description	text,

        access_type     public.access_type NOT NULL DEFAULT 'controlled',
	is_released     boolean NOT NULL DEFAULT FALSE,
        is_deprecated   boolean NOT NULL DEFAULT FALSE,

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()

);

----------
-- DACS --
----------

CREATE TABLE public.dac_table(
        stable_id       text NOT NULL PRIMARY KEY,
        title           text NOT NULL,
	description 	text,

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()

);

CREATE TABLE public.dac_dataset_table (
	dac_stable_id		text NOT NULL REFERENCES public.dac_table(stable_id),
	dataset_stable_id	text NOT NULL REFERENCES Public.dataset_table(stable_id),
	PRIMARY KEY (dac_stable_id, dataset_stable_id),

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);

CREATE TYPE public.member_type AS ENUM ('member', 'admin');

CREATE TABLE IF NOT EXISTS public.dac_user_table
(
    dac_stable_id text NOT NULL REFERENCES public.dac_table(stable_id),
    user_id bigint NOT NULL REFERENCES public.user_table(id),
    PRIMARY KEY (dac_stable_id, user_id),

    is_main boolean NOT NULL,
    member_type public.member_type NOT NULL,

    created_by_db_user text NOT NULL DEFAULT CURRENT_USER,
    created_at timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user text NOT NULL DEFAULT CURRENT_USER,
    edited_at timestamp(6) with time zone NOT NULL DEFAULT now()
);


-----------
-- FILES --
-----------

CREATE TYPE checksum_algorithm AS ENUM ('MD5', 'SHA256', 'SHA384', 'SHA512'); -- md5 is bad. Use sha*!

-- this is the public info about the files
CREATE TABLE public.file_table (
--        id 		   BIGSERIAL PRIMARY KEY,

	stable_id          text NOT NULL PRIMARY KEY,

	filesize                  bigint,-- NOT NULL,

	display_name              text,
	extension                 text,

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);


CREATE TABLE public.dataset_file_table (

	PRIMARY KEY (dataset_stable_id, file_stable_id),
	dataset_stable_id  text NOT NULL, -- REFERENCES public.dataset_table(stable_id),
	file_stable_id     text NOT NULL REFERENCES public.file_table(stable_id),

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);

