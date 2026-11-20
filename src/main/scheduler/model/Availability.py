import sqlite3
import sys
sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager

class Availability:
    pass

    def __init__(self, caretaker_username, time):
        self.caretaker_username = caretaker_username  
        self.time = time  
        
    def get(self):
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
    
            get_caregiver_details = "SELECT Salt, Hash FROM Caregivers WHERE Username = ?"