from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from model.Reservation import Reservation
from model.Availability import Availability
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import sqlite3
import datetime

"""
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
"""
current_patient = None

current_caregiver = None


def has_mixed_case(s: str) -> bool:
    return any(ch.isupper() for ch in s) and any(ch.islower() for ch in s)

def has_num_alpha(s: str) -> bool:
    return any(ch.isdigit() for ch in s) and any(ch.isalpha() for ch in s)


def has_special_character(s: str) -> bool:
    return (
        any(ch == "!" for ch in s)
        or any(ch == "@" for ch in s)
        or any(ch == "#" for ch in s)
        or any(ch == "?" for ch in s)
    )


def strong_password(password: str) -> bool:
    """
    bonus
    """
    if len(password) < 8:
        return False
    if has_mixed_case(password) == False:
        return False
    if has_num_alpha(password) == False:
        return False
    if has_special_character(password) == False:
        return False
    return True


def create_patient(tokens):
    """
    TODO: Part 1
    """
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Create patient failed")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again")
        return
    
    if not strong_password(password):
        print('Create patient failed, please use a strong password (8+ char, at least one upper and one lower, at least one letter and one number, and at least one special character, from "!", "@", "#", "?")')
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except sqlite3.Error as e:
        print("Create patient failed.")
        return
    except Exception as e:
        print("Create patient failed.")
        return
    print("Created user", username)


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again")
        return
    if not strong_password(password):
        print('Create caregiver failed, please use a strong password (8+ char, at least one upper and one lower, at least one letter and one number, and at least one special character, from "!", "@", "#", "?")')
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except sqlite3.Error as e:
        print("Failed to create user.")
        return
    except Exception as e:
        print("Failed to create user.")
        return
    print("Created user", username)


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(select_username, (username,))
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            cm.close_connection()
            return row["Username"] is not None
    except sqlite3.Error as e:
        print("Error occurred when checking username")
        cm.close_connection()
        return True
    except Exception as e:
        print("Error occurred when checking username")
        cm.close_connection()
        return True
    cm.close_connection()
    return False


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(select_username, (username,))
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            cm.close_connection()
            return row["Username"] is not None
    except sqlite3.Error as e:
        print("Error occurred when checking username")
        cm.close_connection()
        return True
    except Exception as e:
        print("Error occurred when checking username")
        cm.close_connection()
        return True
    cm.close_connection()
    return False


def login_patient(tokens):
    """
    TODO: Part 1
    """
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in, try again")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login patient failed")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except sqlite3.Error as e:
        print("Login patient failed")
        return
    except Exception as e:
        print("Login patient failed")
        return

    # check if the login was successful
    if patient is None:
        print("Login patient failed")
    else:
        print("Logged in as " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in, try again")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except sqlite3.Error as e:
        print("Login failed.")
        return
    except Exception as e:
        print("Login failed.")
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    """
    TODO: Part 2
    """
    # search_caregiver_schedule <date>
    # check 1: is the current logged-in user a patient? if not, they need to log in first
    if (current_caregiver is not None or current_patient is not None) == False:
        print("Please login first")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again")
        return

    date = tokens[1]
    try:
        availabilities = Availability.get_by_date(date)
    except sqlite3.Error as e:
        print("Please try again")
        return
    except Exception as e:
        print("Please try again")
        return

    try:
        vaccines = Vaccine.get_all_available()
    except sqlite3.Error as e:
        print("Please try again")
        return
    except Exception as e:
        print("Please try again")
        return

    # check availability and vaccine availability
    print("Caregiver:")
    if len(availabilities) == 0:
        print("No caregivers available")
    else:
        for availability in availabilities:
            print(f"{availability.caretaker_username}")
    print("Vaccines:")
    if len(vaccines) == 0:
        print("No vaccines available")
    else:
        for vaccine in vaccines:
            print(f"{vaccine.vaccine_name} {vaccine.available_doses}")


def reserve(tokens):
    """
    TODO: Part 2
    """
    # If no user is logged in, print “Please login first” and return.
    if (current_caregiver is not None or current_patient is not None) == False:
        print("Please login first")
        return
    # If the current user logged in is not a patient, print “Please login as a patient” and return.
    if current_patient is None:
        print("Please login as a patient")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again")
        return

    date = tokens[1]
    vaccine_name = tokens[2]
    try:
        availabilities = Availability.get_by_date(date)
    except sqlite3.Error as e:
        print("Please try again")
        return
    except Exception as e:
        print("Please try again")
        return

    try:
        vaccine = Vaccine(vaccine_name, None).get()
    except Exception:
        print("Please try again")
        return

    # check availability and vaccine availability
    if len(availabilities) == 0:
        print("No caregivers available")
    elif vaccine is None or vaccine.available_doses <= 0:
        print("Not enough available doses")
    else:
        avail = availabilities[0]
        reservation = Reservation(
            None, date, current_patient.username, vaccine_name, avail.caretaker_username
        )
        reservation.save_to_db()
        vaccine.decrease_available_doses(1)
        avail.delete_from_db()
        rid = reservation.get_rid()  # since it processed after save to db
        print(
            f"Appointment ID {rid}, Caregiver username {reservation.caretaker_username}"
        )


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format yyyy-mm-dd
    date_tokens = date.split("-")
    year = int(date_tokens[0])
    month = int(date_tokens[1])
    day = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except sqlite3.Error as e:
        print("Upload Availability Failed")
        return
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    # If no user is logged in, print “Please login first” and return.
    if (current_caregiver is not None or current_patient is not None) == False:
        print("Please login first")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again")
        return

    rid = tokens[1]
    try:
        rid = int(tokens[1])
        reservation = Reservation.get_by_rid(rid)
    except sqlite3.Error as e:
        print("Please try again")
        return
    except Exception as e:
        print("Please try again")
        return
    if reservation is None:
        print(f"Appointment ID {rid} does not exist")
        return
    
    patient = reservation.get_patient_username()
    caretaker = reservation.get_caretaker_username()
    
    
    if current_caregiver is not None:
        if current_caregiver.username == caretaker:
            time = reservation.get_time()
            vaccine_name = reservation.get_vaccine_name()
            vaccine = Vaccine(vaccine_name, None).get()
            if vaccine is not None:
                vaccine.increase_available_doses(1)
            avail = Availability(caretaker, time)
            avail.save_to_db()
            reservation.delete_from_db()
            print(f"Appointment ID {rid} has been successfully canceled")
            return
        else:
            print(f"Appointment ID {rid} does not exist")
            return
        
        
    elif current_patient is not None:
        if current_patient.username == patient:
            time = reservation.get_time()
            vaccine_name = reservation.get_vaccine_name()
            vaccine = Vaccine(vaccine_name, None).get()
            if vaccine is not None:
                vaccine.increase_available_doses(1)
            avail = Availability(caretaker, time)
            avail.save_to_db()
            reservation.delete_from_db()
            print(f"Appointment ID {rid} has been successfully canceled")
            return
        else:
            print(f"Appointment ID {rid} does not exist")
            return
    else:
        print(f"Appointment ID {rid} does not exist")
        return


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except sqlite3.Error as e:
        print("Error occurred when adding doses")
        return
    except Exception as e:
        print("Error occurred when adding doses")
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except sqlite3.Error as e:
            print("Error occurred when adding doses")
            return
        except Exception as e:
            print("Error occurred when adding doses")
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except sqlite3.Error as e:
            print("Error occurred when adding doses")
            return
        except Exception as e:
            print("Error occurred when adding doses")
            return
    print("Doses updated!")


def show_appointments(tokens):
    """
    TODO: Part 2
    """
    # If no user is logged in, print “Please login first” and return.
    if (current_caregiver is not None or current_patient is not None) == False:
        print("Please login first")
        return
    if len(tokens) != 1:
        print("Please try again")
        return
    # If the current user logged in is not a patient, print “Please login as a patient” and return.
    if current_patient is not None:
        # patient
        try:
            reservations = Reservation.get_by_patient(current_patient.username)
        except Exception as e:
            print("Please try again")
            return
        if len(reservations) == 0:
            print("No appointments found")
            return
        for r in reservations:
            print(f"{r.rid} {r.vaccine_name} {r.time} {r.caretaker_username}")
        return
    elif current_caregiver is not None:
        # caregiver
        try:
            reservations = Reservation.get_by_caretaker(current_caregiver.username)
        except Exception as e:
            print("Please try again")
            return
        if len(reservations) == 0:
            print("No appointments scheduled")
            return
        for r in reservations:
            print(f"{r.rid} {r.vaccine_name} {r.time} {r.patient_username}")
        return


def logout(tokens):
    """
    TODO: Part 2
    """
    global current_caregiver
    global current_patient
    # If no user is logged in, print “Please login first” and return.
    if (current_caregiver is not None or current_patient is not None) == False:
        print("Please login first")
        return
    if len(tokens) != 1:
        print("Please try again")
        return

    current_caregiver = None
    current_patient = None
    print("Successfully logged out")


def start():
    stop = False
    print("*** Please enter one of the following commands ***")
    print(
        "> create_patient <username> <password>"
    )  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print(
        "> login_patient <username> <password>"
    )  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print(
        "> search_caregiver_schedule <date>"
    )  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> quit")
    print()
    while not stop:
        response = ""
        print("> ", end="")

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
