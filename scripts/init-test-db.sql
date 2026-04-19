SELECT 'CREATE DATABASE sub_test'
WHERE NOT EXISTS (
    SELECT FROM pg_database
    WHERE datname = 'sub_test'
) \gexec