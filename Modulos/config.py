# config.py
import os
from datetime import datetime

# --- Model and API Configurations ---
WHISPER_MODEL_NAME = "large-v2"
OLLAMA_MODEL_NAME = "llama3"
OLLAMA_HOST = "http://localhost:11434"

# --- Microphone Configuration ---
# Esta variable será actualizada en tiempo de ejecución por audio_processing.py
SELECTED_MICROPHONE_INDEX = None

# --- File and Directory Paths ---
# Es mejor definir las rutas absolutas o asegurarse de que sean relativas al script que las usa.
# Para este ejemplo, mantendremos las rutas que especificaste.
EXCEL_TEMPLATE_PATH = r"C:\Users\NARUO\Documents\test\BautagebuchVorlage.xlsx"
FILLED_EXCEL_DIR = r"C:\Users\NARUO\Documents\test\bautagebuch_filled_excel"
EXTENDED_TASKS_DIR = r"C:\Users\NARUO\Documents\test\bautagebuch_extended_logs" # Nombre consistente

# Crear directorios si no existen
os.makedirs(FILLED_EXCEL_DIR, exist_ok=True)
os.makedirs(EXTENDED_TASKS_DIR, exist_ok=True)

# --- JSON Schema for LLM ---
JSON_SCHEMA_FOR_LLM = """
{
  "Baustelle": "Unbekannt",
  "Auftraggeber_Bauleiter": "Unbekannt",
  "Bauueberwachung_Verantwortlicher": "Unbekannt",
  "Datum": "YYYY-MM-DD",
  "Auftrag": "Unbekannt",
  "Wetter": "Unbekannt",
  "Temperatur": "None",
  "Wind": "Unbekannt",
  "Personal": [
    {
      "Baustellenpersonal_Typ": "Unbekannt",
      "Name": "Unbekannt",
      "von": "HH:MM",
      "bis": "HH:MM",
      "Pause_Minuten": "0",
      "Arbeitszeit_Stunden": "0.0"
    }
  ],
  "Ausgefuehrte_Arbeiten": "Keine Details extrahiert.",
  "Montagegeraete": "Keine Details extrahiert.",
  "Sonstige_Geraeteeinsaetze": "Keine Details extrahiert.",
  "Materialanlieferungen": "Keine Details extrahiert.",
  "Kundenanweisungen": "Keine Details extrahiert.",
  "Informationen_Fremdfirmen_Fremdleistungen": "Keine Details extrahiert.",
  "Maengel_Nachtragsleistungen": "Keine Details extrahiert."
}
"""

# --- Helper for current date ---
def get_current_date_str():
    return datetime.now().strftime("%Y-%m-%d")