import sqlite3
import sys

sys.path.append("../util")
sys.path.append("../db")
from util.Util import Util
from db.ConnectionManager import ConnectionManager


class Reservation:
    def __init__(
        self,
        rid,
        time=None,
        patient_username=None,
        vaccine_name=None,
        caretaker_username=None,
    ):
        self.rid = rid
        self.time = time
        self.patient_username = patient_username
        self.vaccine_name = vaccine_name
        self.caretaker_username = caretaker_username

    def get(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        get_reservation_details = "SELECT * FROM Reservations WHERE rid = ?"
        try:
            cursor.execute(get_reservation_details, (self.rid,))
            row = cursor.fetchone()
            if row is None:
                return None

            self.time = row["Time"]
            self.patient_username = row["pname"]
            self.vaccine_name = row["vname"]
            self.caretaker_username = row["cname"]
            return self
        except sqlite3.Error as e:
            raise e
        finally:
            cm.close_connection()
    
    def get_time(self):
        return self.time
    
    def get_rid(self):
        return self.rid

    def get_patient_username(self):
        return self.patient_username

    def get_vaccine_name(self):
        return self.vaccine_name

    def get_caretaker_username(self):
        return self.caretaker_username
    
    def save_to_db(self):
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()

            add_reservation = "INSERT INTO Reservations VALUES (?, ?, ?, ?, ?)"
            try:
                cursor.execute(add_reservation, (self.rid, self.time, self.patient_username, self.vaccine_name, self.caretaker_username))
                if self.rid is None:
                    self.rid = cursor.lastrowid
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

        remove_reservation = "DELETE FROM Reservations WHERE rid = ?"
        try:
            cursor.execute(remove_reservation, (self.rid,))
            conn.commit()
        except sqlite3.Error as e:
            raise e
        finally:
            cm.close_connection()
            
    @classmethod
    def get_by_patient(cls, patient_username):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        # Order the results by rid in ascending order
        get_reservations_by_patient = "SELECT * FROM Reservations WHERE pname = ? ORDER BY rid ASC"
        try:
            cursor.execute(get_reservations_by_patient, (patient_username,))
            rows = cursor.fetchall()
            return [
                cls(
                    rid=row["rid"],
                    time=row["Time"],
                    patient_username=row["pname"],
                    vaccine_name=row["vname"],
                    caretaker_username=row["cname"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            raise e
        finally:
            cm.close_connection()

    @classmethod
    def get_by_caretaker(cls, caretaker_username):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        # Order the results by rid in ascending order
        get_reservations_by_caretaker = "SELECT * FROM Reservations WHERE cname = ? ORDER BY rid ASC"
        try:
            cursor.execute(get_reservations_by_caretaker, (caretaker_username,))
            rows = cursor.fetchall()
            return [
                cls(
                    rid=row["rid"],
                    time=row["Time"],
                    patient_username=row["pname"],
                    vaccine_name=row["vname"],
                    caretaker_username=row["cname"],
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            raise e
        finally:
            cm.close_connection()