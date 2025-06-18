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
    try:
        # Initialize response early
        response = VoiceResponse()
        
        # Safely get question number with default
        try:
            q = int(request.args.get("q", "0"))
        except ValueError:
            logger.error("Invalid question number received")
            response.say("Error: Invalid question number")
            response.hangup()
            return str(response)
            
        logger.info(f"Processing question {q}")
        
        # Safely load questions
        try:
            with open("questions.json", "r", encoding='utf-8') as f:
                questions = json.load(f)
        except Exception as e:
            logger.error(f"Error loading questions: {str(e)}")
            response.say("Error loading questions")
            response.hangup()
            return str(response)

        if q == 0:
            response.say("Welcome to the HR interview. Let's begin.")
            response.redirect("/voice?q=1")
            return str(response)

        if request.method == "POST":
            try:
                # Get the speech result and clean it
                answer = request.values.get("SpeechResult", "").strip()
                logger.info(f"Received answer for question {q}: {answer}")
                
                if answer and q > 0:
                    try:
                        with open("responses.csv", "a", newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([f"Q{q}", questions[q-1], answer])
                            logger.info(f"Saved answer to responses.csv: Q{q}, {questions[q-1]}, {answer}")
                    except Exception as e:
                        logger.error(f"Error saving response: {str(e)}")
                        # Continue with the interview even if saving fails
            except Exception as e:
                logger.error(f"Error processing POST request: {str(e)}")
                # Continue with the interview even if processing fails

        if q < len(questions):
            try:
                # Simplified Gather configuration
                gather = Gather(
                    input='speech',
                    action=f"/voice?q={q+1}",
                    method="POST",
                    timeout=10,
                    language='en-US'
                )
                gather.say(questions[q])
                response.append(gather)
                response.redirect(f"/voice?q={q}")
            except Exception as e:
                logger.error(f"Error setting up gather: {str(e)}")
                response.say("Error setting up question. Please try again.")
                response.hangup()
        else:
            response.say("Thanks for your answers. We've recorded your responses. Goodbye!")
            response.hangup()

        return str(response)
    except Exception as e:
        logger.error(f"Critical error in voice route: {str(e)}")
        response = VoiceResponse()
        response.say("An error occurred. Please try again.")
        response.hangup()
        return str(response)

@app.route('/admin')
def admin():
    logger.info("Admin dashboard accessed")
    try:
        # Initialize empty responses list
        responses = []
        
        # Safely read responses from CSV
        try:
            with open("responses.csv", "r", encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:  # Ensure row has enough columns
                        responses.append({
                            "question_no": row[0],
                            "question": row[1],
                            "answer": row[2]
                        })
                    else:
                        logger.warning(f"Skipping invalid row in responses.csv: {row}")
        except FileNotFoundError:
            logger.warning("responses.csv not found - starting with empty responses")
        except Exception as e:
            logger.error(f"Error reading responses.csv: {str(e)}")
            # Continue with empty responses list
        
        # Safely read questions from JSON
        try:
            with open("questions.json", "r", encoding='utf-8') as f:
                questions = json.load(f)
        except FileNotFoundError:
            logger.error("questions.json not found")
            return "Error: Questions file not found", 500
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing questions.json: {str(e)}")
            return "Error: Invalid questions file format", 500
        except Exception as e:
            logger.error(f"Error reading questions.json: {str(e)}")
            return "Error: Could not read questions file", 500

        return render_template('dashboard.html', responses=responses, questions=questions)
    except Exception as e:
        logger.error(f"Critical error in admin dashboard: {str(e)}")
        return "An error occurred while loading the dashboard. Please try again.", 500

@app.route('/download')
def download():
    logger.info("Download route accessed")
    return send_file("responses.csv", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
