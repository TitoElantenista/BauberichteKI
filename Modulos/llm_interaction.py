# llm_interaction.py
import ollama
import json

# Importar configuraciones
import Modulos.config as config

def get_llm_prompt(transcribed_text, current_date_str):
    """Genera el prompt para el LLM."""
    prompt = f"""
Du bist ein KI-Assistent, der darauf spezialisiert ist, transkribierte deutsche Spracheingaben von Baustellen zu analysieren und die relevanten Informationen für ein Bautagebuch zu extrahieren.
Deine Aufgabe ist es, die Informationen gemäß der folgenden JSON-Struktur zu formatieren.
Achte genau auf Details wie Namen, Ränge und Stunden der Arbeiter, den gesamten Arbeitszeitraum sowie die detaillierten Beschreibungen der Tätigkeiten.
Das Datum für diesen Bericht ist {current_date_str}. Bitte verwende dieses Datum im Feld "Datum".
Das JSON-Format muss exakt eingehalten werden. Fülle alle Felder des JSON-Schemas bestmöglich aus. Wenn Informationen für bestimmte Felder nicht explizit genannt werden, verwende die Standardwerte aus dem Schema (z.B. "Unbekannt", "None", leere Listen [] oder 0).

Hier ist die transkribierte Spracheingabe:
"{transcribed_text}"

Bitte extrahiere die Informationen und gib sie im folgenden JSON-Format zurück.

Gewünschtes JSON-Schema (fülle dieses Schema mit den extrahierten Daten):
{config.JSON_SCHEMA_FOR_LLM}
"""
    return prompt


def extract_bautagebuch_data_with_llm(transcribed_text, current_date_str):
    """Extrae datos del texto transcrito usando el LLM."""
    if not transcribed_text:
        return None

    prompt = get_llm_prompt(transcribed_text, current_date_str)
    print(f"\n🧠 Enviando prompt a Ollama (modelo: {config.OLLAMA_MODEL_NAME})...")

    try:
        client = ollama.Client(host=config.OLLAMA_HOST)
        response = client.chat(
            model=config.OLLAMA_MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}]
        )
        llm_output_raw = response['message']['content']

        # Lógica para extraer el bloque JSON de la respuesta del LLM
        json_string_to_parse = None
        try:
            if "```json" in llm_output_raw:
                json_block_start = llm_output_raw.find("```json") + len("```json")
                json_block_end = llm_output_raw.rfind("```")
                if json_block_start != -1 and json_block_end != -1 and json_block_start < json_block_end:
                    json_string_to_parse = llm_output_raw[json_block_start:json_block_end].strip()

            if not json_string_to_parse: # Si no se encontró el bloque ```json
                json_start_index = llm_output_raw.find('{')
                json_end_index = llm_output_raw.rfind('}') + 1
                if json_start_index != -1 and json_end_index > json_start_index:
                    json_string_to_parse = llm_output_raw[json_start_index:json_end_index]
                else:
                    print("⚠️ No se pudo encontrar un objeto JSON válido en la respuesta del LLM (sin llaves {}).")
                    print("Respuesta recibida:", llm_output_raw)
                    return None

            extracted_data = json.loads(json_string_to_parse)
            print("\n📊 Datos JSON extraídos correctamente:")
            print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
            return extracted_data

        except json.JSONDecodeError as e:
            print(f"⚠️ Error al decodificar JSON de la respuesta del LLM: {e}")
            print("String que intentó parsear:", json_string_to_parse if json_string_to_parse else llm_output_raw)
            return None
        except Exception as e_parse: # Captura otras excepciones durante el parseo
            print(f"⚠️ Error inesperado al parsear la respuesta del LLM: {e_parse}")
            print("Respuesta cruda:", llm_output_raw)
            return None

    except Exception as e:
        print(f"❌ Error al comunicarse con Ollama: {e}")
        return None