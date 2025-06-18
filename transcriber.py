import whisper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe_audio(audio_path):
    logger.info(f"Transcribing audio from {audio_path}")
    model = whisper.load_model("base")  # Load model only when needed
    result = model.transcribe(audio_path)
    logger.info(f"Transcription result: {result['text']}")
    return result["text"]
