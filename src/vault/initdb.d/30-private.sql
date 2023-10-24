CREATE SCHEMA private;

CREATE TABLE private.user_password_table
(
    user_id             bigint NOT NULL PRIMARY KEY REFERENCES public.user_table(id),
    password_hash       text NOT NULL,
    is_enabled          boolean NOT NULL DEFAULT TRUE,

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);


CREATE TABLE private.dataset_permission_table (
    id          	bigserial NOT NULL PRIMARY KEY,

    dataset_stable_id  	text NOT NULL, --- REFERENCES public.dataset_table(stable_id),
    user_id     	bigint NOT NULL REFERENCES public.user_table(id),
    UNIQUE(dataset_stable_id, user_id),
    
    expires_at          timestamp(6) with time zone,

    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);

------------------------------
-- Private file information --
------------------------------

CREATE TABLE private.file_table (
    stable_id            text NOT NULL PRIMARY KEY REFERENCES public.file_table(stable_id),
    mount_point   text DEFAULT current_setting('vault.dirpath'),
    relative_path text,
    header        bytea,
    payload_size  bigint,

       payload_checksum       VARCHAR(128) NULL, -- NOT NULL, -- only sha256
       decrypted_checksum     VARCHAR(128) NULL, -- NOT NULL, -- only sha256


    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()
);
