<<<<<<< HEAD
# HR Interview Automation System

An automated HR interview system that schedules and conducts phone interviews using Twilio, with Excel-based contact management and automated calling.

## Features

- **Excel-based Contact Management**: Store and manage interview candidates in an Excel file
- **Automated Scheduling**: Schedule interviews for specific dates and times
- **Personalized Calls**: Calls start with the candidate's name
- **Automated Questioning**: Pre-configured questions are asked automatically
- **Response Recording**: All interview responses are recorded and stored
- **Admin Dashboard**: Comprehensive dashboard to manage contacts, view responses, and monitor scheduled calls
- **Background Processing**: Automated task runner handles scheduled calls in the background

## Setup

### Prerequisites

- Python 3.7+
- Twilio account with phone number
- Required environment variables

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env` file:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

4. Configure interview questions in `questions.json`

### Running the Application

```bash
python app.py
```

The application will start on port 10000 (or the PORT environment variable).

## Usage

### Scheduling Interviews

1. Visit the home page (`/`)
2. Fill out the form with:
   - **Name**: Candidate's full name
   - **Phone Number**: Candidate's phone number (with country code)
   - **Scheduled Time**: Date and time for the interview
3. Click "Schedule Interview"

The system will:
- Add the contact to the Excel file (`contacts.xlsx`)
- Schedule the call for the specified time
- Automatically make the call when the time arrives

### Admin Dashboard

Visit `/admin` to access the comprehensive dashboard with:

- **Scheduled Contacts**: View all contacts with their status
- **Active Scheduled Calls**: Monitor scheduled call jobs
- **Interview Responses**: View all recorded responses
- **Interview Questions**: See configured questions
- **Actions**: Cancel calls or delete contacts

### File Downloads

- `/download` - Download interview responses as CSV
- `/download_excel` - Download contacts Excel file
- `/status` - Get system status (JSON API)

## File Structure

- `app.py` - Main Flask application
- `excel_handler.py` - Excel file operations
- `scheduler.py` - Call scheduling functionality
- `task_runner.py` - Background task processing
- `questions.json` - Interview questions configuration
- `contacts.xlsx` - Contact database (auto-generated)
- `responses.csv` - Interview responses storage
- `templates/` - HTML templates

## Contact Status Tracking

Contacts in the Excel file have the following statuses:

- **Scheduled**: Call is scheduled for future
- **In Progress**: Call is currently being made
- **Completed**: Interview completed successfully
- **Failed**: Call failed to connect
- **Cancelled**: Call was cancelled

## Background Processing

The system uses a background task runner that:

- Checks for pending calls every 30 seconds
- Automatically initiates calls when scheduled time arrives
- Updates contact status in real-time
- Handles errors gracefully

## API Endpoints

- `GET /` - Home page with scheduling form
- `POST /` - Schedule new interview
- `GET /admin` - Admin dashboard
- `GET /download` - Download responses CSV
- `GET /download_excel` - Download contacts Excel
- `GET /status` - System status (JSON)
- `POST /voice` - Twilio webhook for call handling
- `GET /cancel_call/<phone>` - Cancel scheduled call
- `GET /delete_contact/<phone>` - Delete contact

## Deployment

The application is configured for deployment on Render with the provided `render.yaml` file.

## Troubleshooting

1. **Calls not being made**: Check the task runner status at `/status`
2. **Excel file issues**: Ensure write permissions in the application directory
3. **Twilio errors**: Verify environment variables and Twilio account status
4. **Scheduling issues**: Check system time and timezone settings

## Security Notes

- Store sensitive environment variables securely
- Regularly backup the Excel file and responses
- Monitor call logs for any suspicious activity
- Ensure proper access controls for the admin dashboard
=======
# HR
>>>>>>> origin/master
