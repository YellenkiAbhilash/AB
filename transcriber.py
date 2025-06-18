import whisper

def transcribe_audio(audio_path):
    model = whisper.load_model("base")  # Load model only when needed
    result = model.transcribe(audio_path)
    return result["text"]
