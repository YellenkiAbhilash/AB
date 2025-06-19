import threading
import time
from datetime import datetime
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import logging
from excel_handler import ExcelHandler

logger = logging.getLogger(__name__)

class CallScheduler:
    def __init__(self, twilio_client, twilio_phone_number):
        self.twilio_client = twilio_client
        self.twilio_phone_number = twilio_phone_number
        self.excel_handler = ExcelHandler()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._schedule_existing_calls()
    
    def _schedule_existing_calls(self):
        """Schedule all existing calls from Excel file"""
        try:
            contacts = self.excel_handler.get_all_contacts()
            for contact in contacts:
                if contact['Status'] == 'Scheduled':
                    scheduled_time = pd.to_datetime(contact['Scheduled_Time'])
                    if scheduled_time > datetime.now():
                        self.schedule_call(contact['Name'], contact['Phone'], scheduled_time)
                        logger.info(f"Scheduled existing call for {contact['Name']} at {scheduled_time}")
        except Exception as e:
            logger.error(f"Error scheduling existing calls: {str(e)}")
    
    def schedule_call(self, name, phone, scheduled_time):
        """Schedule a call for a specific time"""
        try:
            # Schedule the call
            self.scheduler.add_job(
                func=self._make_call,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[name, phone],
                id=f"call_{phone}_{scheduled_time.timestamp()}",
                replace_existing=True
            )
            logger.info(f"Scheduled call for {name} ({phone}) at {scheduled_time}")
            return True
        except Exception as e:
            logger.error(f"Error scheduling call: {str(e)}")
            return False
    
    def _make_call(self, name, phone):
        """Make the actual call"""
        try:
            logger.info(f"Making scheduled call to {name} at {phone}")
            
            # Update status to 'In Progress'
            self.excel_handler.update_call_status(phone, 'In Progress')
            
            # Make the call
            call = self.twilio_client.calls.create(
                url=f'https://ab-vaya.onrender.com/voice?q=0&name={name}',
                to=phone,
                from_=self.twilio_phone_number,
                record=True
            )
            
            logger.info(f"Call initiated for {name} with SID: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Error making call to {phone}: {str(e)}")
            self.excel_handler.update_call_status(phone, 'Failed')
            return None
    
    def get_scheduled_jobs(self):
        """Get all scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def cancel_call(self, phone):
        """Cancel a scheduled call"""
        try:
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                if phone in job.id:
                    job.remove()
                    self.excel_handler.update_call_status(phone, 'Cancelled')
                    logger.info(f"Cancelled call for {phone}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling call: {str(e)}")
            return False
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown() 