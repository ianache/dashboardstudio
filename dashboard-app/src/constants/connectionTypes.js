/**
 * Single source of truth for connection types.
 * Imported by: ConnectionEditModal.vue, ConnectionsView.vue, FlowEditorCanvas.vue
 */

export const CONN_TYPES = [
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql',      label: 'MySQL / MariaDB' },
  { value: 'mssql',      label: 'SQL Server' },
  { value: 'oracle',     label: 'Oracle DB' },
  { value: 'mongodb',    label: 'MongoDB' },
  { value: 'redis',      label: 'Redis' },
  { value: 'rest_api',   label: 'REST API' },
  { value: 'sftp',       label: 'SFTP / FTP' },
  { value: 'ftp',        label: 'FTP' },
  { value: 's3',         label: 'Amazon S3' },
  { value: 'bigquery',   label: 'BigQuery' },
  { value: 'smtp',       label: 'SMTP (Email)' },
  { value: 'http',       label: 'HTTP (Basic Auth)' },
  { value: 'jwt',        label: 'JWT Token' },
  { value: 'database',   label: 'Base de Datos (Genérica)' },
]

/** Default connection_config shape per type */
export const CONN_DEFAULTS = {
  postgresql: { host: '', port: 5432,  username: '', password: '', database: '', schema: 'public' },
  mysql:      { host: '', port: 3306,  username: '', password: '', database: '' },
  mssql:      { host: '', port: 1433,  username: '', password: '', database: '', schema: 'dbo' },
  oracle:     { host: '', port: 1521,  username: '', password: '', database: '' },
  mongodb:    { host: '', port: 27017, username: '', password: '', database: '' },
  redis:      { host: '', port: 6379,  password: '', database: '0' },
  rest_api:   { url: '', api_key: '', auth_type: 'bearer' },
  sftp:       { host: '', port: 22,    username: '', password: '', protocol: 'sftp' },
  ftp:        { host: '', port: 21,    username: '', password: '', protocol: 'ftp' },
  s3:         { bucket: '', region: '', access_key: '', secret_key: '' },
  bigquery:   { project_id: '', dataset: '', credentials_json: '' },
  smtp:       { host: '', port: 587,   use_ssl: true, email: '', password: '' },
  http:       { url: '', username: '', password: '' },
  jwt:        { token_url: '', username: '', password: '', client_id: '', client_secret: '' },
  database:   { host: '', port: 5432,  username: '', password: '', database: '', schema: 'public' },
}

/** Visual metadata (icon, colors) per type — used in cards */
export const CONN_META = {
  postgresql: { icon: 'database',     bg: '#eff6ff', fg: '#2563eb', accent: '#2563eb' },
  mysql:      { icon: 'storage',      bg: '#f0fdf4', fg: '#16a34a', accent: '#16a34a' },
  mssql:      { icon: 'dns',          bg: '#fef3c7', fg: '#d97706', accent: '#d97706' },
  oracle:     { icon: 'database',     bg: '#fff7ed', fg: '#ea580c', accent: '#ea580c' },
  mongodb:    { icon: 'data_object',  bg: '#f0fdf4', fg: '#15803d', accent: '#15803d' },
  redis:      { icon: 'memory',       bg: '#fef2f2', fg: '#dc2626', accent: '#dc2626' },
  rest_api:   { icon: 'api',          bg: '#f5f3ff', fg: '#7c3aed', accent: '#7c3aed' },
  sftp:       { icon: 'folder_open',  bg: '#fafaf9', fg: '#57534e', accent: '#a8a29e' },
  ftp:        { icon: 'folder_open',  bg: '#fafaf9', fg: '#57534e', accent: '#a8a29e' },
  s3:         { icon: 'cloud_upload', bg: '#fff7ed', fg: '#c2410c', accent: '#c2410c' },
  bigquery:   { icon: 'analytics',    bg: '#eff6ff', fg: '#1d4ed8', accent: '#1d4ed8' },
  smtp:       { icon: 'email',        bg: '#fdf4ff', fg: '#9333ea', accent: '#9333ea' },
  http:       { icon: 'language',     bg: '#ecfdf5', fg: '#059669', accent: '#059669' },
  jwt:        { icon: 'vpn_key',      bg: '#fef9c3', fg: '#ca8a04', accent: '#ca8a04' },
  database:   { icon: 'database',     bg: '#eff6ff', fg: '#2563eb', accent: '#2563eb' },
}

export function connTypeMeta(type) {
  return CONN_META[type] || { icon: 'cable', bg: '#f8fafc', fg: '#64748b', accent: '#cbd5e1' }
}
export function connTypeLabel(type) {
  return CONN_TYPES.find(c => c.value === type)?.label || type
}
