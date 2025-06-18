import os
import json
import csv
from flask import Flask, request, render_template, redirect, send_file
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from transcriber import transcribe_audio
import logging

load_dotenv()
app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        to_number = request.form['phone']
        logger.info(f"Starting call to {to_number}")
        call = client.calls.create(
            url='https://ab-vaya.onrender.com/voice?q=0',
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            record=True
        )
        logger.info(f"Call started with SID: {call.sid}")
        return f"✅ Call started! Call SID: {call.sid}"
    return render_template('index.html')

@app.route('/voice', methods=['GET', 'POST'])
def voice():
    q = int(request.args.get("q", 0))
    logger.info(f"Voice route called with q={q}")
    with open("questions.json") as f:
        questions = json.load(f)

    response = VoiceResponse()

    if q == 0:
        response.say("Welcome to the HR interview. Let's begin.")
        response.redirect("/voice?q=1")
        return str(response)

    if request.method == "POST":
        answer = request.values.get("SpeechResult", "").strip()
        logger.info(f"Received answer for question {q}: {answer}")
        if answer and q > 0:
            with open("responses.csv", "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([f"Q{q}", questions[q-1], answer])
                logger.info(f"Saved answer to responses.csv: Q{q}, {questions[q-1]}, {answer}")

    if q < len(questions):
        gather = Gather(input='speech', action=f"/voice?q={q+1}", method="POST", timeout=5)
        gather.say(questions[q])
        response.append(gather)
        response.redirect(f"/voice?q={q}")
    else:
        response.say("Thanks for your answers. We've recorded your responses. Goodbye!")
        response.hangup()

    return str(response)

@app.route('/admin')
def admin():
    data = []
    if os.path.exists("responses.csv"):
        with open("responses.csv", newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = list(reader)
    return render_template("dashboard.html", responses=data)

@app.route('/download')
def download():
    return send_file("responses.csv", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render uses PORT=10000
    app.run(host="0.0.0.0", port=port, debug=False)  # Disable debug mode for production
