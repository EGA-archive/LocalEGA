CREATE SCHEMA request;

-- TODO
-- ################################
-- REQUESTS & PERMISSIONS
-- ################################

CREATE TYPE request.tuple_type AS
(
	id bigint,
	value text
);

CREATE TYPE request.tuple_text_type AS
(
	stable_id text,
	value text
);

CREATE TYPE request.request_type AS ENUM (
    'pending',
    'granted',
    'denied' --,
    --'blocked'
);

-- History of requests and actions performed on them
CREATE TABLE request.permission_action_table
(
    id                      bigserial NOT NULL PRIMARY KEY,
    dataset_stable_id       text NOT NULL REFERENCES public.dataset_table(stable_id),
    user_id                 bigint NOT NULL REFERENCES public.user_table(id),
    dac_stable_id           text NOT NULL REFERENCES public.dac_table(stable_id),
 
    status                  request.request_type NOT NULL DEFAULT 'pending'::request.request_type,

    expires_at              date,
    by_whom_stable_id	    text,

    comment                 text,   -- if denied, the reason will be saved here
    request_data            jsonb,-- NOT NULL,

    --is_blocked              boolean NOT NULL DEFAULT FALSE,
                                    -- true if the user has been denied
                                    -- for the same dataset too many times
    -- auditing
    created_by_db_user      text NOT NULL DEFAULT CURRENT_USER,
    created_at              timestamp(6) with time zone NOT NULL DEFAULT now(),
    edited_by_db_user       text NOT NULL DEFAULT CURRENT_USER,
    edited_at               timestamp(6) with time zone NOT NULL DEFAULT now()

);

