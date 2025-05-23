# audio_processing.py
import speech_recognition as sr
import whisper
import os
import tempfile
from queue import Queue
import torch # Para la comprobación de CUDA en la transcripción

# Importar configuraciones
import Modulos.config as config

def listar_y_seleccionar_microfono():
    """Lista los micrófonos disponibles y permite al usuario seleccionar uno."""
    mic_names = []
    try:
        mic_names = sr.Microphone.list_microphone_names()
    except OSError as e:
        print(f"❌ Error al listar micrófonos (OSError): {e}")
        print("   Asegúrate de que PyAudio esté instalado y los controladores de audio funcionen.")
        return None
    except Exception as e:
        print(f"❌ Error inesperado al listar micrófonos: {e}")
        return None

    if not mic_names:
        print("❌ No se encontraron micrófonos. Asegúrate de que PyAudio esté instalado.")
        return None

    print("\n🎤 Micrófonos disponibles:")
    for index, name in enumerate(mic_names):
        print(f"  Índice: {index} - Nombre: {name}")

    while True:
        try:
            choice_str = input(
                f"Selecciona el ÍNDICE del micrófono (0-{len(mic_names) - 1}), o deja en blanco para el predeterminado: ")
            if not choice_str:
                print("Usando el micrófono predeterminado.")
                config.SELECTED_MICROPHONE_INDEX = None # Actualiza la config global
                return None
            device_idx = int(choice_str)
            if 0 <= device_idx < len(mic_names):
                print(f"Has seleccionado: {mic_names[device_idx]}")
                config.SELECTED_MICROPHONE_INDEX = device_idx # Actualiza la config global
                return device_idx
            else:
                print("Índice fuera de rango. Inténtalo de nuevo.")
        except ValueError:
            print("Entrada no válida. Por favor, introduce un número de índice.")
        except Exception as e:
            print(f"Un error inesperado ocurrió durante la selección: {e}")
            return None


def record_audio_until_stopped(stop_event_text="parar grabación"):
    """
    Graba audio continuamente usando el micrófono seleccionado en config
    hasta que el usuario escribe un texto de parada o presiona Ctrl+C.
    Devuelve el objeto AudioData combinado o una señal de parada.
    """
    r = sr.Recognizer()
    audio_queue = Queue()

    device_idx = config.SELECTED_MICROPHONE_INDEX

    try:
        if device_idx is not None:
            mic = sr.Microphone(device_index=device_idx)
            print(f"🎙️  Usando micrófono con índice: {device_idx}")
        else:
            mic = sr.Microphone()
            print("🎙️  Usando el micrófono predeterminado.")
    except Exception as e:
        print(f"❌ Error al inicializar el micrófono: {e}")
        return None

    print(f"   (Modelo Whisper a usar: {config.WHISPER_MODEL_NAME})")

    def record_callback(_, audio: sr.AudioData):
        audio_queue.put(audio.get_raw_data())

    stop_listening = r.listen_in_background(mic, record_callback, phrase_time_limit=5)

    print(f"🎤 ¡Grabación iniciada! Habla libremente.")
    print(f"   Cuando termines, escribe '{stop_event_text}' y presiona Enter, o presiona Ctrl+C para abortar.")

    recorded_data = []
    try:
        while True:
            user_input = input()
            if user_input.strip().lower() == stop_event_text.lower():
                print("🛑 Grabación finalizada por el usuario.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Programa detenido por el usuario (Ctrl+C) durante la espera de la señal de parada.")
        stop_listening(wait_for_stop=False)
        return "STOP_PROGRAM"
    except Exception as e:
        print(f"Error inesperado durante la espera de la señal de parada: {e}")
        stop_listening(wait_for_stop=False)
        return None
    finally:
        stop_listening(wait_for_stop=True)
        while not audio_queue.empty():
            recorded_data.append(audio_queue.get())

    if not recorded_data:
        print("No se grabó ningún audio.")
        return None

    sample_rate = mic.SAMPLE_RATE
    sample_width = mic.SAMPLE_WIDTH
    full_raw_data = b''.join(recorded_data)
    combined_audio_data = sr.AudioData(full_raw_data, sample_rate, sample_width)
    print("🎧 Audio completo capturado, procesando...")
    return combined_audio_data


def transcribe_with_whisper(audio_data):
    """Transcribe un objeto AudioData usando Whisper."""
    if not audio_data:
        return None

    tmp_audio_file_path = None
    try:
        # Guardar temporalmente el audio para Whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio_file:
            tmp_audio_file.write(audio_data.get_wav_data())
            tmp_audio_file_path = tmp_audio_file.name

        print(f"🤫 Transcribiendo con Whisper ({config.WHISPER_MODEL_NAME})...")
        model = whisper.load_model(config.WHISPER_MODEL_NAME)
        # Usar fp16 si CUDA está disponible y es soportado
        use_fp16 = torch.cuda.is_available()
        result = model.transcribe(tmp_audio_file_path, language="de", fp16=use_fp16)
        transcribed_text = result["text"]
        print(f"🗣️ Texto transcrito: {transcribed_text}")
        return transcribed_text
    except Exception as e:
        print(f"❌ Error durante la transcripción con Whisper: {e}")
        if "ffmpeg" in str(e).lower() or "winerror 2" in str(e).lower():
            print("🆘  Este error podría estar relacionado con FFmpeg. Asegúrate de que esté instalado y en el PATH.")
        elif "out of memory" in str(e).lower():
            print("🆘  ¡Error de falta de memoria! El modelo Whisper es demasiado grande para tu VRAM/RAM.")
            print("    Considera usar un modelo más pequeño (ej. 'base', 'small', 'medium').")
        return None
    finally:
        if tmp_audio_file_path and os.path.exists(tmp_audio_file_path):
            try:
                os.remove(tmp_audio_file_path)
            except Exception as e_del:
                print(f"Advertencia: No se pudo eliminar el archivo temporal {tmp_audio_file_path}: {e_del}")