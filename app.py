import os
import json
import csv
import logging
from flask import Flask, request, render_template, redirect, send_file
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info("Index route accessed")
    if request.method == 'POST':
        to_number = request.form['phone']
        logger.info(f"Starting call to {to_number}")
        try:
            call = client.calls.create(
                url='https://ab-vaya.onrender.com/voice?q=0',
                to=to_number,
                from_=TWILIO_PHONE_NUMBER,
                record=True
            )
            logger.info(f"Call started with SID: {call.sid}")
            return f"✅ Call started! Call SID: {call.sid}"
        except Exception as e:
            logger.error(f"Error starting call: {str(e)}")
            return f"Error starting call: {str(e)}"
    return render_template('index.html')

@app.route('/voice', methods=['GET', 'POST'])
def voice():
    logger.info("Voice route accessed")
    q = int(request.args.get("q", 0))
    logger.info(f"Processing question {q}")
    
    try:
        with open("questions.json") as f:
            questions = json.load(f)
    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
        return str(VoiceResponse().say("Error loading questions"))

    response = VoiceResponse()

    if q == 0:
        response.say("Welcome to the HR interview. Let's begin.")
        response.redirect("/voice?q=1")
        return str(response)

    if request.method == "POST":
        # Get the speech result and clean it
        answer = request.values.get("SpeechResult", "").strip()
        confidence = request.values.get("Confidence", "0")
        logger.info(f"Received answer for question {q}: {answer} (Confidence: {confidence})")
        
        if answer and q > 0:
            try:
                with open("responses.csv", "a", newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([f"Q{q}", questions[q-1], answer, confidence])
                    logger.info(f"Saved answer to responses.csv: Q{q}, {questions[q-1]}, {answer}, {confidence}")
            except Exception as e:
                logger.error(f"Error saving response: {str(e)}")

    if q < len(questions):
        # Configure Gather with improved speech recognition settings
        gather = Gather(
            input='speech',
            action=f"/voice?q={q+1}",
            method="POST",
            timeout=10,  # Increased timeout
            speech_timeout='auto',  # Auto timeout for speech
            language='en-US',  # Specify language
            enhanced='true',  # Use enhanced speech recognition
            speech_model='phone_call'  # Optimize for phone calls
        )
        gather.say(questions[q], voice='Polly.Amy')  # Use a clearer voice
        response.append(gather)
        response.redirect(f"/voice?q={q}")
    else:
        response.say("Thanks for your answers. We've recorded your responses. Goodbye!")
        response.hangup()

    return str(response)

@app.route('/admin')
def admin():
    logger.info("Admin route accessed")
    data = []
    try:
        if os.path.exists("responses.csv"):
            with open("responses.csv", newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                data = list(reader)
    except Exception as e:
        logger.error(f"Error loading responses: {str(e)}")
    return render_template("dashboard.html", responses=data)

@app.route('/download')
def download():
    logger.info("Download route accessed")
    return send_file("responses.csv", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
