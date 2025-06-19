import time
import threading
import logging
from datetime import datetime
from excel_handler import ExcelHandler
from scheduler import CallScheduler

logger = logging.getLogger(__name__)

class TaskRunner:
    def __init__(self, twilio_client, twilio_phone_number):
        self.excel_handler = ExcelHandler()
        self.call_scheduler = CallScheduler(twilio_client, twilio_phone_number)
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background task runner"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("Task runner started")
    
    def stop(self):
        """Stop the background task runner"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.call_scheduler.shutdown()
        logger.info("Task runner stopped")
    
    def _run(self):
        """Main loop for checking and processing scheduled calls"""
        while self.running:
            try:
                # Check for pending calls every 30 seconds
                pending_calls = self.excel_handler.get_pending_calls()
                
                for call in pending_calls:
                    logger.info(f"Processing pending call for {call['Name']} at {call['Phone']}")
                    
                    # Update status to 'In Progress'
                    self.excel_handler.update_call_status(call['Phone'], 'In Progress')
                    
                    # Make the call
                    try:
                        call_sid = self.call_scheduler._make_call(call['Name'], call['Phone'])
                        if call_sid:
                            logger.info(f"Call initiated for {call['Name']} with SID: {call_sid}")
                        else:
                            logger.error(f"Failed to initiate call for {call['Name']}")
                            self.excel_handler.update_call_status(call['Phone'], 'Failed')
                    except Exception as e:
                        logger.error(f"Error making call to {call['Phone']}: {str(e)}")
                        self.excel_handler.update_call_status(call['Phone'], 'Failed')
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in task runner: {str(e)}")
                time.sleep(30)  # Continue running even if there's an error
    
    def get_status(self):
        """Get the current status of the task runner"""
        return {
            'running': self.running,
            'scheduled_jobs': len(self.call_scheduler.get_scheduled_jobs()),
            'pending_calls': len(self.excel_handler.get_pending_calls())
        } 