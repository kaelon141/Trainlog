SELECT EXISTS (
    SELECT *
    FROM information_schema.tables
    WHERE table_schema = 'public'
) OR EXISTS (
    SELECT n.nspname
    FROM pg_catalog.pg_namespace n
    WHERE n.nspname !~ '^pg_' AND n.nspname NOT IN ('information_schema', 'public')
);
