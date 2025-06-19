import pandas as pd
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExcelHandler:
    def __init__(self, filename="contacts.xlsx"):
        self.filename = filename
        self.columns = ['Name', 'Phone', 'Scheduled_Time', 'Status', 'Created_At']
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create Excel file if it doesn't exist"""
        if not os.path.exists(self.filename):
            df = pd.DataFrame(columns=self.columns)
            df.to_excel(self.filename, index=False)
            logger.info(f"Created new Excel file: {self.filename}")
    
    def add_contact(self, name, phone, scheduled_time):
        """Add a new contact to the Excel file"""
        try:
            # Read existing data
            df = pd.read_excel(self.filename)
            
            # Create new row
            new_row = {
                'Name': name,
                'Phone': phone,
                'Scheduled_Time': scheduled_time,
                'Status': 'Scheduled',
                'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Append new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save to Excel
            df.to_excel(self.filename, index=False)
            logger.info(f"Added contact: {name} - {phone} at {scheduled_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding contact: {str(e)}")
            return False
    
    def get_pending_calls(self):
        """Get all scheduled calls that are due"""
        try:
            df = pd.read_excel(self.filename)
            if df.empty:
                return []
            
            # Convert Scheduled_Time to datetime if it's not already
            df['Scheduled_Time'] = pd.to_datetime(df['Scheduled_Time'])
            
            # Filter for pending calls (Status = 'Scheduled' and time is due)
            now = datetime.now()
            pending = df[
                (df['Status'] == 'Scheduled') & 
                (df['Scheduled_Time'] <= now)
            ]
            
            return pending.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting pending calls: {str(e)}")
            return []
    
    def update_call_status(self, phone, status):
        """Update the status of a call"""
        try:
            df = pd.read_excel(self.filename)
            
            # Find the row with matching phone number
            mask = df['Phone'] == phone
            if mask.any():
                df.loc[mask, 'Status'] = status
                df.to_excel(self.filename, index=False)
                logger.info(f"Updated status for {phone} to {status}")
                return True
            else:
                logger.warning(f"Phone number {phone} not found in Excel file")
                return False
                
        except Exception as e:
            logger.error(f"Error updating call status: {str(e)}")
            return False
    
    def get_all_contacts(self):
        """Get all contacts from the Excel file"""
        try:
            df = pd.read_excel(self.filename)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error reading contacts: {str(e)}")
            return []
    
    def delete_contact(self, phone):
        """Delete a contact from the Excel file"""
        try:
            df = pd.read_excel(self.filename)
            
            # Remove rows with matching phone number
            df = df[df['Phone'] != phone]
            
            df.to_excel(self.filename, index=False)
            logger.info(f"Deleted contact with phone: {phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting contact: {str(e)}")
            return False 