# main.py
from datetime import datetime
import traceback
import torch  # Para la comprobación inicial de CUDA

# Importar módulos del proyecto
import Modulos.config as config
import Modulos.audio_processing as audio_processing
import Modulos.llm_interaction as llm_interaction
import Modulos.excel_processing as excel_processing


def perform_initial_checks():
    """Realiza y muestra comprobaciones iniciales del sistema."""
    print("--- Comprobaciones Iniciales ---")
    print(f"PyTorch version: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    if cuda_available:
        print(f"CUDA version: {torch.version.cuda}")
        try:
            print(f"GPU name: {torch.cuda.get_device_name(0)}")
            print(f"GPU capability: {torch.cuda.get_device_capability(0)}")
        except Exception as e:
            print(f"Error al obtener detalles de la GPU: {e}")
    print("-" * 30)


def main_workflow():
    """Flujo principal de la aplicación Bautagebuch."""
    print("--- Sistema de Llenado de Bautagebuch por Voz ---")

    # Seleccionar micrófono (actualiza config.SELECTED_MICROPHONE_INDEX)
    audio_processing.listar_y_seleccionar_microfono()

    # Si no se seleccionó un micro específico y el usuario no quiere usar el predeterminado
    if config.SELECTED_MICROPHONE_INDEX is None:  # listar_y_seleccionar_microfono ya imprimió "Usando predeterminado" o falló
        # Podemos reconfirmar si el usuario no eligió explícitamente el predeterminado
        # pero la lógica actual de listar_y_seleccionar_microfono ya maneja esto.
        # Si listar_y_seleccionar_microfono devolvió None (por ej. eligió predeterminado o falló),
        # config.SELECTED_MICROPHONE_INDEX será None.
        # Si falló al listar, ya habrá un mensaje de error.
        # Si se eligió predeterminado, se usará.
        pass  # La configuración del micrófono ya está gestionada.

    while True:
        current_date_str = config.get_current_date_str()
        print(f"\n--- Nueva Entrada para el Bautagebuch ({current_date_str}) ---")

        # 1. Grabar audio
        # record_audio_until_stopped usará config.SELECTED_MICROPHONE_INDEX internamente
        audio_data_combinado = audio_processing.record_audio_until_stopped(stop_event_text="parar")

        if audio_data_combinado == "STOP_PROGRAM":
            print("Programa finalizado por el usuario.")
            break
        if not audio_data_combinado:
            print("No se pudo obtener el audio.")
            if input("¿Quieres intentar grabar de nuevo? (s/n): ").lower() != 's':
                break
            continue

        # 2. Transcribir el audio combinado
        transcribed_text = audio_processing.transcribe_with_whisper(audio_data_combinado)
        if not transcribed_text:
            print("No se pudo obtener la transcripción.")
            if input("¿Quieres intentar grabar de nuevo (desde el principio)? (s/n): ").lower() != 's':
                break
            continue

        # 3. Extraer Datos con LLM
        bautagebuch_data = llm_interaction.extract_bautagebuch_data_with_llm(transcribed_text, current_date_str)
        if not bautagebuch_data:
            print("No se pudieron extraer los datos del Bautagebuch.")
            if input("¿Quieres intentar grabar de nuevo (desde el principio)? (s/n): ").lower() != 's':
                break
            continue

        # Asegurarse de que el campo "Datum" tenga un valor, usando el del schema y el actual.
        # El schema JSON ya tiene "Datum" como campo esperado.
        if "Datum" not in bautagebuch_data or not bautagebuch_data.get("Datum") \
                or bautagebuch_data.get("Datum") == "YYYY-MM-DD":  # Si el LLM no lo llenó
            bautagebuch_data["Datum"] = current_date_str

        # 4. Guardar detalles en archivo de texto y rellenar Excel
        excel_processing.save_extended_text_details(bautagebuch_data, current_date_str)

        if bautagebuch_data:  # Solo si tenemos datos
            excel_output_path = excel_processing.fill_excel_bautagebuch(bautagebuch_data)
            if excel_output_path:
                # El mensaje de éxito ya se imprime dentro de fill_excel_bautagebuch
                pass
            else:
                print("⚠️ No se pudo rellenar o guardar el archivo Excel.")
        else:  # Aunque este caso es poco probable si los pasos anteriores tuvieron éxito
            print("⚠️ No hay datos del Bautagebuch para procesar en Excel.")

        if input("\n¿Quieres realizar otra entrada para el Bautagebuch? (s/n): ").lower() != 's':
            break

    print("\n--- Sistema finalizado ---")


if __name__ == "__main__":
    perform_initial_checks()
    try:
        main_workflow()
    except KeyboardInterrupt:
        print("\n👋 Programa interrumpido por el usuario (Ctrl+C general).")
    except Exception as e_main:
        print(f"❌ Un error crítico ocurrió en el flujo principal: {e_main}")
        traceback.print_exc()