"""add diagram_types, editor_tools, integration_flows tables

Revision ID: 008
Revises: 007
Create Date: 2026-04-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import json


revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'
NOW = datetime.utcnow()


def upgrade() -> None:
    # ── diagram_types ──────────────────────────────────────────────────────────
    op.create_table(
        'diagram_types',
        sa.Column('id',          sa.String(50),  primary_key=True),
        sa.Column('name',        sa.String(100), nullable=False),
        sa.Column('description', sa.Text(),      nullable=True),
        sa.Column('icon',        sa.String(50),  nullable=False, server_default='schema'),
        sa.Column('color',       sa.String(20),  nullable=False, server_default='#2563eb'),
        sa.Column('created_at',  sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at',  sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )

    # ── editor_tools ───────────────────────────────────────────────────────────
    op.create_table(
        'editor_tools',
        sa.Column('id',                      sa.String(50),  primary_key=True),
        sa.Column('type',                    sa.String(50),  nullable=False, unique=True),
        sa.Column('name',                    sa.String(100), nullable=False),
        sa.Column('description',             sa.Text(),      nullable=True),
        sa.Column('subtitle',               sa.String(200), nullable=True),
        sa.Column('icon',                    sa.String(50),  nullable=False, server_default='storage'),
        sa.Column('category',               sa.String(50),  nullable=False, server_default='source'),
        sa.Column('applicable_diagram_types', sa.JSON(),    nullable=False, server_default='[]'),
        sa.Column('prop_defs',              sa.JSON(),      nullable=False, server_default='{}'),
        sa.Column('default_props',          sa.JSON(),      nullable=False, server_default='{}'),
        sa.Column('created_at',             sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at',             sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )
    op.create_index('idx_editor_tools_type', 'editor_tools', ['type'], unique=True, schema=SCHEMA)

    # ── integration_flows ──────────────────────────────────────────────────────
    op.create_table(
        'integration_flows',
        sa.Column('id',              sa.String(50),  primary_key=True),
        sa.Column('name',            sa.String(255), nullable=False),
        sa.Column('description',     sa.Text(),      nullable=True),
        sa.Column('diagram_type',   sa.String(50),  nullable=False, server_default='data-integration'),
        sa.Column('status',          sa.String(20),  nullable=False, server_default='draft'),
        sa.Column('flow_type',       sa.String(50),  nullable=True),
        sa.Column('schedule',        sa.String(100), nullable=True),
        sa.Column('source_system',   sa.String(100), nullable=True),
        sa.Column('target_system',   sa.String(100), nullable=True),
        sa.Column('flow_nodes',      sa.JSON(),      nullable=False, server_default='[]'),
        sa.Column('flow_connections', sa.JSON(),     nullable=False, server_default='[]'),
        sa.Column('flow_metadata',   sa.JSON(),      nullable=False, server_default='{}'),
        sa.Column('last_run',        sa.DateTime(),  nullable=True),
        sa.Column('last_run_success', sa.Boolean(),  nullable=True),
        sa.Column('created_by',      sa.String(50),  sa.ForeignKey(f'{SCHEMA}.users.id'), nullable=True),
        sa.Column('created_at',      sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at',      sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )
    op.create_index('idx_integration_flows_status', 'integration_flows', ['status'], schema=SCHEMA)

    # ── Seed: diagram_types ────────────────────────────────────────────────────
    diagram_types_table = sa.table(
        'diagram_types',
        sa.column('id', sa.String), sa.column('name', sa.String),
        sa.column('description', sa.Text), sa.column('icon', sa.String),
        sa.column('color', sa.String), sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
        schema=SCHEMA,
    )
    op.bulk_insert(diagram_types_table, [
        {'id': 'data-integration', 'name': 'Data Integration Flow',
         'description': 'Flujos ETL/ELT de integración entre sistemas transaccionales y ODS',
         'icon': 'sync_alt', 'color': '#2563eb', 'created_at': NOW, 'updated_at': NOW},
        {'id': 'process-flow', 'name': 'Process Flow',
         'description': 'Diagramas de flujo de procesos de negocio',
         'icon': 'account_tree', 'color': '#7c3aed', 'created_at': NOW, 'updated_at': NOW},
        {'id': 'data-quality', 'name': 'Data Quality',
         'description': 'Flujos de validación y calidad de datos',
         'icon': 'verified', 'color': '#059669', 'created_at': NOW, 'updated_at': NOW},
    ])

    # ── Seed: editor_tools ─────────────────────────────────────────────────────
    tools_table = sa.table(
        'editor_tools',
        sa.column('id', sa.String), sa.column('type', sa.String),
        sa.column('name', sa.String), sa.column('description', sa.Text),
        sa.column('subtitle', sa.String), sa.column('icon', sa.String),
        sa.column('category', sa.String),
        sa.column('applicable_diagram_types', sa.JSON),
        sa.column('prop_defs', sa.JSON), sa.column('default_props', sa.JSON),
        sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime),
        schema=SCHEMA,
    )

    def t(id_, type_, name, desc, subtitle, icon, cat, diagrams, prop_defs, default_props):
        return {
            'id': id_, 'type': type_, 'name': name, 'description': desc,
            'subtitle': subtitle, 'icon': icon, 'category': cat,
            'applicable_diagram_types': diagrams,
            'prop_defs': prop_defs, 'default_props': default_props,
            'created_at': NOW, 'updated_at': NOW,
        }

    op.bulk_insert(tools_table, [
        # ── Sources ────────────────────────────────────────────────────────────
        t('tool-postgresql', 'postgresql', 'PostgreSQL',
          'Conector de lectura para PostgreSQL', 'Base de datos relacional', 'storage', 'source',
          ['data-integration', 'data-quality'],
          {'host':     {'label':'Host',           'type':'text',     'placeholder':'localhost'},
           'port':     {'label':'Puerto',         'type':'text',     'placeholder':'5432'},
           'database': {'label':'Base de datos',  'type':'text',     'placeholder':'mydb'},
           'schema':   {'label':'Schema',         'type':'text',     'placeholder':'public'},
           'table':    {'label':'Tabla',          'type':'text',     'placeholder':'my_table'},
           'query':    {'label':'Query SQL',      'type':'textarea', 'placeholder':'SELECT * FROM ...', 'rows':4}},
          {'host':'', 'port':'5432', 'database':'', 'schema':'public', 'table':'', 'query':''}),

        t('tool-mysql', 'mysql', 'MySQL',
          'Conector de lectura para MySQL', 'Base de datos relacional', 'storage', 'source',
          ['data-integration', 'data-quality'],
          {'host':     {'label':'Host',          'type':'text', 'placeholder':'localhost'},
           'port':     {'label':'Puerto',        'type':'text', 'placeholder':'3306'},
           'database': {'label':'Base de datos', 'type':'text', 'placeholder':'mydb'},
           'table':    {'label':'Tabla',         'type':'text', 'placeholder':'my_table'}},
          {'host':'', 'port':'3306', 'database':'', 'table':''}),

        t('tool-rest-api', 'rest_api', 'REST API',
          'Consume datos desde un endpoint REST', 'Endpoint HTTP/REST', 'api', 'source',
          ['data-integration'],
          {'url':       {'label':'URL',            'type':'text',     'placeholder':'https://api.example.com/data'},
           'method':    {'label':'Método HTTP',    'type':'select',   'options':[{'value':'GET','label':'GET'},{'value':'POST','label':'POST'},{'value':'PUT','label':'PUT'}]},
           'auth_type': {'label':'Autenticación',  'type':'select',   'options':[{'value':'none','label':'Ninguna'},{'value':'bearer','label':'Bearer Token'},{'value':'basic','label':'Basic Auth'}]},
           'headers':   {'label':'Headers (JSON)', 'type':'textarea', 'placeholder':'{"Content-Type": "application/json"}'}},
          {'url':'', 'method':'GET', 'auth_type':'none', 'headers':''}),

        t('tool-csv-file', 'csv_file', 'CSV / Excel',
          'Importa datos desde CSV o Excel', 'Archivo plano', 'description', 'source',
          ['data-integration', 'data-quality'],
          {'path':       {'label':'Ruta del archivo', 'type':'text',   'placeholder':'/data/file.csv'},
           'delimiter':  {'label':'Delimitador',      'type':'text',   'placeholder':','},
           'has_header': {'label':'Tiene cabecera',   'type':'select', 'options':[{'value':'true','label':'Sí'},{'value':'false','label':'No'}]},
           'encoding':   {'label':'Codificación',     'type':'select', 'options':[{'value':'UTF-8','label':'UTF-8'},{'value':'ISO-8859-1','label':'ISO-8859-1'}]}},
          {'path':'', 'delimiter':',', 'has_header':'true', 'encoding':'UTF-8'}),

        t('tool-erp-sap', 'erp_sap', 'SAP ERP',
          'Extrae datos desde módulos SAP via BAPI/RFC', 'Conector ERP SAP', 'business_center', 'source',
          ['data-integration'],
          {'host':   {'label':'Host SAP', 'type':'text',   'placeholder':'sap.company.com'},
           'client': {'label':'Cliente',  'type':'text',   'placeholder':'100'},
           'module': {'label':'Módulo',   'type':'select', 'options':[{'value':'SD','label':'SD - Ventas'},{'value':'MM','label':'MM - Materiales'},{'value':'FI','label':'FI - Finanzas'},{'value':'HR','label':'HR - Recursos Humanos'}]},
           'bapi':   {'label':'BAPI / RFC','type':'text',  'placeholder':'BAPI_SALESORDER_GETLIST'}},
          {'host':'', 'client':'100', 'module':'SD', 'bapi':''}),

        # ── Transforms ────────────────────────────────────────────────────────
        t('tool-filter', 'filter', 'Filtro',
          'Filtra filas según condición', 'Filtrar registros', 'filter_alt', 'transform',
          ['data-integration', 'data-quality', 'process-flow'],
          {'field':    {'label':'Campo',    'type':'text',   'placeholder':'status'},
           'operator': {'label':'Operador', 'type':'select', 'options':[{'value':'=','label':'= Igual'},{'value':'!=','label':'≠ Diferente'},{'value':'>','label':'> Mayor'},{'value':'<','label':'< Menor'},{'value':'contains','label':'Contiene'},{'value':'not_null','label':'No es nulo'}]},
           'value':    {'label':'Valor',    'type':'text',   'placeholder':'active'}},
          {'field':'', 'operator':'=', 'value':''}),

        t('tool-field-map', 'field_map', 'Mapeo de campos',
          'Renombra o transforma columnas', 'Renombrar / mapear', 'schema', 'transform',
          ['data-integration', 'data-quality'],
          {'mappings': {'label':'Mapeos (origen:destino)', 'type':'textarea', 'placeholder':'txn_id:transaction_id\namt_usd:amount', 'rows':5}},
          {'mappings':''}),

        t('tool-join', 'join', 'Join',
          'Une dos flujos de datos por una clave', 'Unir datasets', 'merge', 'transform',
          ['data-integration'],
          {'join_type': {'label':'Tipo de Join',   'type':'select', 'options':[{'value':'inner','label':'INNER JOIN'},{'value':'left','label':'LEFT JOIN'},{'value':'right','label':'RIGHT JOIN'},{'value':'full','label':'FULL OUTER JOIN'}]},
           'join_key':  {'label':'Clave de unión', 'type':'text',   'placeholder':'id'}},
          {'join_type':'inner', 'join_key':''}),

        t('tool-aggregate', 'aggregate', 'Agregación',
          'Agrupa y calcula métricas', 'Group by / Sum', 'functions', 'transform',
          ['data-integration'],
          {'group_by':     {'label':'Group By',     'type':'text',     'placeholder':'category, region'},
           'aggregations': {'label':'Agregaciones', 'type':'textarea', 'placeholder':'SUM(amount) as total\nCOUNT(*) as count', 'rows':4}},
          {'group_by':'', 'aggregations':''}),

        t('tool-data-clean', 'data_clean', 'Limpieza',
          'Normaliza y limpia datos', 'Normalizar datos', 'cleaning_services', 'transform',
          ['data-integration', 'data-quality'],
          {'remove_nulls':    {'label':'Eliminar nulos',      'type':'select', 'options':[{'value':'true','label':'Sí'},{'value':'false','label':'No'}]},
           'normalize_dates': {'label':'Normalizar fechas',   'type':'select', 'options':[{'value':'true','label':'Sí'},{'value':'false','label':'No'}]},
           'trim_strings':    {'label':'Trim strings',        'type':'select', 'options':[{'value':'true','label':'Sí'},{'value':'false','label':'No'}]},
           'dedup':           {'label':'Eliminar duplicados', 'type':'select', 'options':[{'value':'true','label':'Sí'},{'value':'false','label':'No'}]}},
          {'remove_nulls':'true', 'normalize_dates':'true', 'trim_strings':'true', 'dedup':'false'}),

        t('tool-sql-custom', 'sql_custom', 'SQL Custom',
          'Transforma con SQL ad-hoc', 'SQL personalizado', 'code', 'transform',
          ['data-integration', 'data-quality'],
          {'query':  {'label':'SQL',    'type':'textarea', 'placeholder':"SELECT *\nFROM input_stream\nWHERE ...", 'rows':6},
           'engine': {'label':'Motor',  'type':'select',   'options':[{'value':'sql','label':'SQL Estándar'},{'value':'spark','label':'Spark SQL'},{'value':'pandas','label':'Pandas'}]}},
          {'query':'', 'engine':'sql'}),

        # ── Destinations ──────────────────────────────────────────────────────
        t('tool-ods-pg', 'ods_pg', 'ODS PostgreSQL',
          'Carga datos en el ODS PostgreSQL', 'Capa ODS', 'database', 'destination',
          ['data-integration'],
          {'schema':     {'label':'Schema destino',  'type':'text',   'placeholder':'ods'},
           'table':      {'label':'Tabla destino',   'type':'text',   'placeholder':'fact_ventas'},
           'write_mode': {'label':'Modo escritura',  'type':'select', 'options':[{'value':'append','label':'Append'},{'value':'upsert','label':'Upsert'},{'value':'overwrite','label':'Overwrite'},{'value':'merge','label':'Merge (SCD2)'}]},
           'batch_size': {'label':'Tamaño de batch', 'type':'text',   'placeholder':'1000'}},
          {'schema':'ods', 'table':'', 'write_mode':'upsert', 'batch_size':'1000'}),

        t('tool-snowflake', 'snowflake', 'Snowflake',
          'Carga datos en Snowflake', 'Data warehouse', 'ac_unit', 'destination',
          ['data-integration'],
          {'account':   {'label':'Account',   'type':'text', 'placeholder':'myorg.us-east-1'},
           'warehouse': {'label':'Warehouse', 'type':'text', 'placeholder':'COMPUTE_WH'},
           'database':  {'label':'Database',  'type':'text', 'placeholder':'MY_DB'},
           'schema':    {'label':'Schema',    'type':'text', 'placeholder':'PUBLIC'},
           'table':     {'label':'Tabla',     'type':'text', 'placeholder':'FACT_TABLE'}},
          {'account':'', 'warehouse':'COMPUTE_WH', 'database':'', 'schema':'PUBLIC', 'table':''}),

        t('tool-bigquery', 'bigquery', 'BigQuery',
          'Carga datos en BigQuery', 'GCP analytics', 'analytics', 'destination',
          ['data-integration'],
          {'project':    {'label':'Proyecto GCP', 'type':'text',   'placeholder':'my-project'},
           'dataset':    {'label':'Dataset',      'type':'text',   'placeholder':'my_dataset'},
           'table':      {'label':'Tabla',        'type':'text',   'placeholder':'my_table'},
           'write_mode': {'label':'Modo',         'type':'select', 'options':[{'value':'append','label':'Append'},{'value':'truncate','label':'Truncate+Load'}]}},
          {'project':'', 'dataset':'', 'table':'', 'write_mode':'append'}),

        # ── Notifications ─────────────────────────────────────────────────────
        t('tool-webhook', 'webhook', 'Webhook',
          'Envía notificación via HTTP', 'HTTP callback', 'webhook', 'notification',
          ['data-integration', 'process-flow'],
          {'url':        {'label':'URL',         'type':'text',   'placeholder':'https://hooks.example.com/...'},
           'method':     {'label':'Método',      'type':'select', 'options':[{'value':'POST','label':'POST'},{'value':'GET','label':'GET'}]},
           'trigger_on': {'label':'Disparar en', 'type':'select', 'options':[{'value':'success','label':'Éxito'},{'value':'error','label':'Error'},{'value':'always','label':'Siempre'}]}},
          {'url':'', 'method':'POST', 'trigger_on':'success'}),

        t('tool-email', 'email', 'Email',
          'Envía alerta por email', 'Notificación email', 'email', 'notification',
          ['data-integration', 'process-flow'],
          {'to':         {'label':'Para',        'type':'text',   'placeholder':'admin@company.com'},
           'subject':    {'label':'Asunto',      'type':'text',   'placeholder':'Flow ejecutado'},
           'trigger_on': {'label':'Disparar en', 'type':'select', 'options':[{'value':'success','label':'Éxito'},{'value':'error','label':'Error'},{'value':'always','label':'Siempre'}]}},
          {'to':'', 'subject':'', 'trigger_on':'success'}),
    ])

    # ── Seed: integration_flows ────────────────────────────────────────────────
    flows_table = sa.table(
        'integration_flows',
        sa.column('id', sa.String), sa.column('name', sa.String),
        sa.column('description', sa.Text), sa.column('diagram_type', sa.String),
        sa.column('status', sa.String), sa.column('flow_type', sa.String),
        sa.column('schedule', sa.String), sa.column('source_system', sa.String),
        sa.column('target_system', sa.String),
        sa.column('flow_nodes', sa.JSON), sa.column('flow_connections', sa.JSON),
        sa.column('flow_metadata', sa.JSON),
        sa.column('last_run', sa.DateTime), sa.column('last_run_success', sa.Boolean),
        sa.column('created_by', sa.String),
        sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime),
        schema=SCHEMA,
    )

    default_nodes = [
        {'id':'n1','toolType':'postgresql','category':'source','label':'Fuente PostgreSQL','x':120,'y':280,'props':{'host':'','port':'5432','database':'','schema':'public','table':'','query':''}},
        {'id':'n2','toolType':'data_clean','category':'transform','label':'Limpieza de datos','x':440,'y':280,'props':{'remove_nulls':'true','normalize_dates':'true','trim_strings':'true','dedup':'false'}},
        {'id':'n3','toolType':'ods_pg','category':'destination','label':'ODS PostgreSQL','x':760,'y':280,'props':{'schema':'ods','table':'','write_mode':'upsert','batch_size':'1000'}},
    ]
    default_connections = [
        {'id':'c1','from':'n1','to':'n2'},
        {'id':'c2','from':'n2','to':'n3'},
    ]

    op.bulk_insert(flows_table, [
        {'id':'flow-001','name':'ERP → ODS Ventas','description':'Sincronización diaria de transacciones de venta',
         'diagram_type':'data-integration','status':'active','flow_type':'Batch ETL',
         'schedule':'0 6 * * *','source_system':'ERP SAP','target_system':'ODS PostgreSQL',
         'flow_nodes':default_nodes,'flow_connections':default_connections,'flow_metadata':{},
         'last_run':datetime(2026,4,28,6,0,0),'last_run_success':True,'created_by':None,'created_at':NOW,'updated_at':NOW},
        {'id':'flow-002','name':'CRM → ODS Clientes','description':'Actualización en tiempo real de datos de clientes',
         'diagram_type':'data-integration','status':'active','flow_type':'CDC',
         'schedule':'*/5 * * * *','source_system':'CRM Salesforce','target_system':'ODS PostgreSQL',
         'flow_nodes':default_nodes,'flow_connections':default_connections,'flow_metadata':{},
         'last_run':datetime(2026,4,28,5,30,0),'last_run_success':True,'created_by':None,'created_at':NOW,'updated_at':NOW},
        {'id':'flow-003','name':'WMS → ODS Inventario','description':'Carga de movimientos de inventario y stock',
         'diagram_type':'data-integration','status':'error','flow_type':'Batch ETL',
         'schedule':'0 22 * * *','source_system':'WMS Oracle','target_system':'ODS PostgreSQL',
         'flow_nodes':default_nodes,'flow_connections':default_connections,'flow_metadata':{},
         'last_run':datetime(2026,4,27,22,0,0),'last_run_success':False,'created_by':None,'created_at':NOW,'updated_at':NOW},
        {'id':'flow-004','name':'SAP FI → ODS Contabilidad','description':'Extracción de asientos contables y balances',
         'diagram_type':'data-integration','status':'scheduled','flow_type':'API Pull',
         'schedule':'0 18 * * *','source_system':'SAP FI','target_system':'ODS PostgreSQL',
         'flow_nodes':default_nodes,'flow_connections':default_connections,'flow_metadata':{},
         'last_run':datetime(2026,4,27,18,0,0),'last_run_success':True,'created_by':None,'created_at':NOW,'updated_at':NOW},
        {'id':'flow-005','name':'HRMS → ODS Personal','description':'Sincronización de empleados y estructura organizacional',
         'diagram_type':'data-integration','status':'paused','flow_type':'File Import',
         'schedule':'0 10 1 * *','source_system':'SuccessFactors','target_system':'ODS PostgreSQL',
         'flow_nodes':default_nodes,'flow_connections':default_connections,'flow_metadata':{},
         'last_run':datetime(2026,4,25,10,0,0),'last_run_success':True,'created_by':None,'created_at':NOW,'updated_at':NOW},
    ])


def downgrade() -> None:
    op.drop_index('idx_integration_flows_status', table_name='integration_flows', schema=SCHEMA)
    op.drop_table('integration_flows', schema=SCHEMA)
    op.drop_index('idx_editor_tools_type', table_name='editor_tools', schema=SCHEMA)
    op.drop_table('editor_tools', schema=SCHEMA)
    op.drop_table('diagram_types', schema=SCHEMA)
