-- File generated automatically, do not modify by hand!
-- Use `make generate-schema-sql` instead
--
-- PostgreSQL database dump
--

-- Dumped from database version 17.3 (Debian 17.3-3.pgdg120+1)
-- Dumped by pg_dump version 17.3 (Debian 17.3-3.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: meta; Type: SCHEMA; Schema: -; Owner: trainlog
--

CREATE SCHEMA meta;


ALTER SCHEMA meta OWNER TO trainlog;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: migrations; Type: TABLE; Schema: meta; Owner: trainlog
--

CREATE TABLE meta.migrations (
    name character varying NOT NULL,
    applied timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE meta.migrations OWNER TO trainlog;

--
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: meta; Owner: trainlog
--

ALTER TABLE ONLY meta.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (name);


--
-- PostgreSQL database dump complete
--

SET search_path TO DEFAULT;
