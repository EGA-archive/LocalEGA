SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET default_tablespace = '';



-- To input data
CREATE USER lega WITH LOGIN ENCRYPTED PASSWORD 'change-me-please';

-- To distribute data
CREATE USER distribution WITH LOGIN ENCRYPTED PASSWORD 'change-me-please';

-- To manage permissions
CREATE USER permission WITH LOGIN ENCRYPTED PASSWORD 'change-me-please';
