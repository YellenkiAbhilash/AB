import os
import json
import logging
from datetime import datetime
import pytz
from flask import Flask, request, render_template, redirect, send_file
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from excel_handler import ExcelHandler
from scheduler import CallScheduler
from task_runner import TaskRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Timezone
IST = pytz.timezone('Asia/Kolkata')

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

# Initialize Excel handler, scheduler, and task runner
excel_handler = ExcelHandler()
call_scheduler = CallScheduler(client, TWILIO_PHONE_NUMBER)
task_runner = TaskRunner(client, TWILIO_PHONE_NUMBER)

# Start the task runner
task_runner.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info("Index route accessed")
    message = None
    message_type = None
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        scheduled_time_str = request.form.get('scheduled_time', '').strip()
        
        if not all([name, phone, scheduled_time_str]):
            message = "All fields are required!"
            message_type = "error"
        else:
            try:
                # Convert string to IST datetime
                naive_dt = datetime.strptime(scheduled_time_str.replace('T', ' '), '%Y-%m-%d %H:%M')
                ist_dt = IST.localize(naive_dt)
                # Remove tzinfo for Excel storage, but keep as IST
                scheduled_time = ist_dt.replace(tzinfo=None)
                
                add_result = excel_handler.add_contact(name, phone, scheduled_time)
                if add_result:
                    if call_scheduler.schedule_call(name, phone, ist_dt):
                        message = f"✅ Interview scheduled for {name} at {ist_dt.strftime('%Y-%m-%d %H:%M (IST)')}"
                        message_type = "success"
                    else:
                        message = "Contact added but failed to schedule call. Please try again."
                        message_type = "error"
                else:
                    logger.error(f"Failed to add contact: name={name}, phone={phone}, scheduled_time={scheduled_time}")
                    message = "Failed to add contact. Please try again."
                    message_type = "error"
            except ValueError as e:
                logger.error(f"ValueError: {e}")
                message = "Invalid date/time format. Please try again."
                message_type = "error"
            except Exception as e:
                logger.error(f"Error scheduling interview: {str(e)}")
                message = "An error occurred. Please try again."
                message_type = "error"
    # Always show dashboard data
    contacts = excel_handler.get_all_contacts()
    for contact in contacts:
        try:
            if contact['Scheduled_Time']:
                dt = datetime.strptime(str(contact['Scheduled_Time']), '%Y-%m-%d %H:%M:%S')
                contact['Scheduled_Time'] = dt.strftime('%Y-%m-%d %H:%M (IST)')
            if contact['Created_At']:
                dt = datetime.strptime(str(contact['Created_At']), '%Y-%m-%d %H:%M:%S')
                contact['Created_At'] = dt.strftime('%Y-%m-%d %H:%M (IST)')
        except Exception:
            pass
    scheduled_jobs = call_scheduler.get_scheduled_jobs()
    try:
        with open("questions.json", "r", encoding='utf-8') as f:
            questions = json.load(f)
    except Exception:
        questions = []
    return render_template('index.html', message=message, message_type=message_type, contacts=contacts, scheduled_jobs=scheduled_jobs, questions=questions)

@app.route('/voice', methods=['GET', 'POST'])
def voice():
    logger.info("Voice route accessed")
    try:
        response = VoiceResponse()
        
        # Get question number and name
        q = int(request.args.get("q", "0"))
        name = request.args.get("name", "there")
        logger.info(f"Processing question {q} for {name}")
        
        # Load questions
        with open("questions.json", "r", encoding='utf-8') as f:
            questions = json.load(f)

        if q == 0:
            response.say(f"Hello {name}, welcome to the HR interview. Let's begin.")
            response.redirect(f"/voice?q=1&name={name}")
            return str(response)

        if q < len(questions):
            gather = Gather(
                input='speech',
                action=f"/voice?q={q+1}&name={name}",
                method="POST",
                timeout=10,
                finishOnKey='#'
            )
            gather.say(questions[q])
            response.append(gather)
            # Add a fallback in case of timeout
            response.redirect(f"/voice?q={q}&name={name}")
        else:
            response.say(f"Thanks {name} for your answers. Goodbye!")
            response.hangup()
            
            # Update call status to completed
            phone = request.values.get("From", "")
            if phone:
                excel_handler.update_call_status(phone, "Completed")

        return str(response)
    except Exception as e:
        logger.error(f"Error in voice route: {str(e)}")
        response = VoiceResponse()
        response.say("An error occurred. Please try again.")
        response.hangup()
        return str(response)

@app.route('/cancel_call/<phone>')
def cancel_call(phone):
    """Cancel a scheduled call"""
    try:
        if call_scheduler.cancel_call(phone):
            return redirect('/')
        else:
            return "Failed to cancel call", 400
    except Exception as e:
        logger.error(f"Error cancelling call: {str(e)}")
        return "Error cancelling call", 500

@app.route('/delete_contact/<phone>')
def delete_contact(phone):
    """Delete a contact from Excel"""
    try:
        if excel_handler.delete_contact(phone):
            return redirect('/')
        else:
            return "Failed to delete contact", 400
    except Exception as e:
        logger.error(f"Error deleting contact: {str(e)}")
        return "Error deleting contact", 500

@app.route('/download_excel')
def download_excel():
    """Download the contacts Excel file"""
    logger.info("Download Excel route accessed")
    return send_file("contacts.xlsx", as_attachment=True)

@app.route('/status')
def status():
    """Get system status"""
    try:
        status_info = {
            'task_runner': task_runner.get_status(),
            'total_contacts': len(excel_handler.get_all_contacts()),
            'pending_calls': len(excel_handler.get_pending_calls()),
            'scheduled_jobs': len(call_scheduler.get_scheduled_jobs()),
            'server_time': datetime.now(IST).isoformat()
        }
        return status_info
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {'error': str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    finally:
        task_runner.stop()
        call_scheduler.shutdown()
