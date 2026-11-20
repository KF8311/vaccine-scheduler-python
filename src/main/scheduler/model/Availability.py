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
        
        get_availability = """
            SELECT *
            FROM Availabilities
            WHERE cname = ? AND Time = ?
        """
        try:
            cursor.execute(get_availability, (self.caretaker_username, self.time))
            row = cursor.fetchone()
            if row is None:
                return None

            self.caretaker_username = row["Username"]
            self.time = row["Time"]
            return self
        except sqlite3.Error as e:
            raise e
        finally:
            cm.close_connection()
            
    def save_to_db(self):
                cm = ConnectionManager()
                conn = cm.create_connection()
                cursor = conn.cursor()
    
                add_availability = "INSERT INTO Availabilities VALUES (?, ?)"
                try:
                    cursor.execute(add_availability, (self.caretaker_username, self.time))
                    # you must call commit() to persist your data if you don't set autocommit to True
                    conn.commit()
                except sqlite3.Error:
                    raise
                finally:
                    cm.close_connection()
    
    def delete_from_db(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        remove_availability = "DELETE FROM Availabilities WHERE Username = ? AND Time = ?"
        try:
            cursor.execute(remove_availability, (self.caretaker_username, self.time))
            conn.commit()
        except sqlite3.Error as e:
            raise e
        finally:
            cm.close_connection()