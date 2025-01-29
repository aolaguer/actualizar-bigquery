import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import os

# Cargar credenciales desde la variable de entorno
credentials_json = os.environ.get("GCP_CREDENTIALS")
with open("credentials.json", "w") as f:
    f.write(credentials_json)

# Configuración
SPREADSHEET_ID = "1fabcNPfYaxhQYeUn6IW-j8Y9apFuMq7pTzRVHKFw1R0"
RANGE_NAME = "bq!A:C"  # Rango de datos en la hoja de cálculo
PROJECT_ID = "cedears-448818"
DATASET_ID = "cedears"
TABLE_ID = "cotizaciones"
CREDENTIALS_FILE = "credentials.json"

# Leer datos de Google Sheets
credentials = Credentials.from_service_account_file(
    CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
service = build("sheets", "v4", credentials=credentials)
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
rows = result.get("values", [])

# Convertir los datos a DataFrame
df = pd.DataFrame(rows[1:], columns=rows[0])  # Primera fila son los encabezados
df["fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y").dt.strftime("%Y-%m-%d")  # Convertir fecha a YYYY-MM-DD
df["precio"] = pd.to_numeric(df["Precio"], errors="coerce")  # Convertir precio a float

# Cargar datos en BigQuery
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")  # Reemplazar la tabla
job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
job.result()  # Esperar a que termine la carga

print(f"Datos actualizados en la tabla {TABLE_ID}")
