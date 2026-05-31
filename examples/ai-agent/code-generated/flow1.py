import pandas as pd
from sqlalchemy import create_engine
import psycopg2
import requests
import smtplib
from email.mime.text import MIMEText

# --- Configuration --- 
# Database connection for sources and destinations
DB_CONNECTION_STRING = "postgresql://user:password@192.168.100.254:5432/analytics"

# Webhook configuration
WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAQA7vtBQmg/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=93Sj4kyRUKaazVs61p9_khic9HzSTkOWhwvxl1-RTjk"

# Email configuration
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "user@example.com"
SMTP_PASSWORD = "password"
EMAIL_FROM = "ilver.anache@gmail.com"
EMAIL_TO = "ilver.anache@gmail.com"
EMAIL_SUBJECT = "[RESULTADO] resultado de la integracion"

# --- Helper Functions ---
def get_db_engine(connection_string):
    return create_engine(connection_string)

def execute_query(engine, query):
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        raise

def transform_data(df1, df2, join_type="inner", join_key=None):
    if join_key is None:
        raise ValueError("join_key must be provided for transformation.")
    try:
        merged_df = pd.merge(df1, df2, on=join_key, how=join_type)
        return merged_df
    except Exception as e:
        print(f"Error during data transformation (merge): {e}")
        raise

def load_to_ods(df, schema, table, write_mode, identity_fields):
    try:
        engine = get_db_engine(DB_CONNECTION_STRING)
        if write_mode == "upsert":
            # For simplicity, we'll do a basic upsert logic. For production, consider a more robust solution.
            # This assumes primary keys are in identity_fields.
            # A common approach is to use a temporary table and then MERGE or INSERT ... ON CONFLICT.
            print(f"Performing upsert into {schema}.{table}... This is a simplified implementation.")
            
            # Create a temporary table for the new data
            temp_table_name = f"temp_{table}_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
            df.to_sql(temp_table_name, engine, schema=schema, if_exists='replace', index=False)

            # Construct the upsert query (PostgreSQL example)
            columns = ", ".join(df.columns)
            conflict_columns = ", ".join(identity_fields)
            update_set_clauses = [
                f"{col} = EXCLUDED.{col}"
                for col in df.columns if col not in identity_fields
            ]
            update_string = ", ".join(update_set_clauses)

            upsert_query = f"""
            INSERT INTO {schema}.{table} ({columns})
            SELECT {columns}
            FROM {schema}.{temp_table_name}
            ON CONFLICT ({conflict_columns})
            DO UPDATE SET {update_string};
            """
            
            with engine.connect() as connection:
                connection.execute(upsert_query)
                connection.execute(f"DROP TABLE {schema}.{temp_table_name}")
            
            print(f"Upsert completed for {schema}.{table}.")
        else:
            df.to_sql(table, engine, schema=schema, if_exists=write_mode, index=False, chunksize=int(1000))
        print(f"Data loaded successfully to {schema}.{table}")
    except Exception as e:
        print(f"Error loading data to ODS: {e}")
        raise

def send_webhook_notification(url, data):
    try:
        response = requests.post(url, json=data)
        response.raise_for_status() # Raise an exception for bad status codes
        print(f"Webhook notification sent successfully. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending webhook notification: {e}")

def send_email_notification(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("Email notification sent successfully.")
    except Exception as e:
        print(f"Error sending email notification: {e}")

# --- Main ETL/ELT Process ---
def main():
    engine = get_db_engine(DB_CONNECTION_STRING)

    # --- Source 1: Calendarios ---
    print("Fetching data from Calendarios...")
    query_calendarios = "SELECT id as id_calendario, dia, nrodia, horas FROM bronze.tb_calendario"
    df_calendarios = execute_query(engine, query_calendarios)
    print(f"Fetched {len(df_calendarios)} records from Calendarios.")

    # --- Source 2: Areas ---
    print("Fetching data from Areas...")
    query_areas = "SELECT * FROM bronze.tb_area"
    df_areas = execute_query(engine, query_areas)
    print(f"Fetched {len(df_areas)} records from Areas.")

    # --- Transformation 1: Combinar Datasets ---
    print("Combining datasets...")
    df_combined = transform_data(df_calendarios, df_areas, join_type="inner", join_key="id_calendario")
    print(f"Combined dataset has {len(df_combined)} records.")

    # --- Transformation 2: Preprocesamiento (JS Script translated to Python)
    # The original JS script returned the payload as is. Assuming some basic cleaning/structuring if needed.
    # For this example, we'll just ensure it's a DataFrame and prepare it.
    print("Performing preprocessing...")
    # Assuming df_combined is the payload from the previous step.
    processed_payload = df_combined # No complex transformation logic in the original JS script for this part.
    print(f"Preprocessing resulted in {len(processed_payload)} records.")

    # --- Destination: ODS PostgreSQL ---
    print("Loading data to ODS PostgreSQL...")
    load_to_ods(processed_payload, schema="silver", table="stg_area_data", write_mode="upsert", identity_fields=["id", "id_calendario", "nrodia"])

    # --- Notification Preparation ---
    print("Preparing notification payload...")
    # The JS script for notification preparation formats the message.
    # We'll recreate that logic here.
    total_registros = len(processed_payload)
    texto_mensaje = f"""📊 *Notificación de Sincronización*\n
                    • Estado: *Exitoso*\n
                    • Total de registros procesados: *{total_registros}* unidades.\n
                    • Fecha/Hora: _{pd.Timestamp.now().strftime('%d/%m/%Y, %H:%M:%S')}
                    """
    
    notification_data_for_webhook = {"text": texto_mensaje}
    notification_data_for_email = {"text": texto_mensaje} # For email body templating

    # --- Notification 1: Webhook ---
    print("Sending webhook notification...")
    send_webhook_notification(WEBHOOK_URL, notification_data_for_webhook)

    # --- Notification 2: Email ---
    print("Sending email notification...")
    # The email body is templated. We'll replace {{ text }} with the prepared message.
    email_body_final = f"Hola Ilver,\n{texto_mensaje}"
    send_email_notification(EMAIL_SUBJECT, email_body_final)

    print("ETL/ELT process completed successfully.")

if __name__ == "__main__":
    main()
