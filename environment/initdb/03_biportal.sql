-- Create biportal database and user for BI Backend
-- This script runs after initdb/01_keycloak.sql and 02_analytics.sql

-- Create user if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles
        WHERE  rolname = 'biportal'
    ) THEN
        CREATE ROLE biportal WITH LOGIN PASSWORD 'biportal_password';
    END IF;
END
$$;

-- Create database if not exists
SELECT 'CREATE DATABASE biportal'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'biportal')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE biportal TO biportal;

-- Connect to biportal and create schema
\c biportal

CREATE SCHEMA IF NOT EXISTS biportal AUTHORIZATION biportal;

-- Grant schema privileges
GRANT USAGE ON SCHEMA biportal TO biportal;
GRANT ALL ON SCHEMA biportal TO biportal;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA biportal GRANT ALL ON TABLES TO biportal;
ALTER DEFAULT PRIVILEGES IN SCHEMA biportal GRANT ALL ON SEQUENCES TO biportal;