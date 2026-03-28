-- =============================================================
--  01_keycloak.sql
--  Crea el usuario y la base de datos para Keycloak.
--  Se ejecuta conectado a la base "analytics" (POSTGRES_DB),
--  que es la que levanta el contenedor por defecto.
-- =============================================================

-- Usuario dedicado para Keycloak
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'keycloak_user') THEN
    CREATE ROLE keycloak_user
      LOGIN
      PASSWORD 'keycloakpassword'   -- sobreescribe con KC_DB_PASSWORD en producción
      NOSUPERUSER
      NOCREATEDB
      NOCREATEROLE;
  END IF;
END
$$;

-- Base de datos propia de Keycloak
CREATE DATABASE keycloak
  OWNER       keycloak_user
  ENCODING    'UTF8'
  LC_COLLATE  'en_US.utf8'
  LC_CTYPE    'en_US.utf8'
  TEMPLATE    template0;

COMMENT ON DATABASE keycloak IS 'Base de datos exclusiva de Keycloak (Identity Provider)';

-- Conectar a la base keycloak para crear el schema
\connect keycloak

-- Schema dedicado dentro de la base keycloak
CREATE SCHEMA IF NOT EXISTS keycloak AUTHORIZATION keycloak_user;

-- Permisos completos sobre el schema
GRANT ALL PRIVILEGES ON SCHEMA keycloak TO keycloak_user;
ALTER ROLE keycloak_user SET search_path TO keycloak;
