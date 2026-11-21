import hashlib
import os
from pathlib import Path
import sqlite3
import sys

# seed.py is in .../src/main, so parent is .../src (adjust to .parent.parent if db is at repo root)
SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from db.ConnectionManager import ConnectionManager

# Adjust path if create.sql lives in .../src/db, .../src/main, or repo root
SCHEMA_PATH = Path(
    r"C:\Users\lambo\UW\CSE414\homework\hw6\vaccine-scheduler-python\src\main\resources\sqlite\create.sql"
)


def hash_password(password: str):
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000,
        dklen=16,
    )
    return salt, pwd_hash


def apply_schema(cursor, schema_path: Path):
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    sql_script = schema_path.read_text(encoding="utf-8")
    cursor.executescript(sql_script)


def clear_database(cursor):
    tables_to_clear = [
        "Reservations",
        "Availabilities",
        "Vaccines",
        "Caregivers",
        "Patients",
    ]
    for table in tables_to_clear:
        cursor.execute(f"DELETE FROM {table}")

    try:
        cursor.execute("DELETE FROM sqlite_sequence")
    except sqlite3.OperationalError:
        pass


def seed(schema_path: Path = SCHEMA_PATH):
    cm = ConnectionManager()
    conn = cm.create_connection()
    if conn is None:
        raise RuntimeError("Failed to connect to database. Check DBPATH and ConnectionManager.")

    cursor = conn.cursor()

    try:
        # In SQLite, PRAGMA foreign_keys and executescript() work best outside an active transaction
        cursor.execute("PRAGMA foreign_keys = OFF;")
        apply_schema(cursor, schema_path)
        clear_database(cursor)

        # 1. Vaccines (Name, Doses)
        vaccines = [
            ("covid", 5),
            ("flu", 3),
            ("hpv", 2),
        ]
        cursor.executemany(
            "INSERT INTO Vaccines (Name, Doses) VALUES (?, ?)",
            vaccines,
        )

        # 2. Caregivers (Username, Salt, Hash)
        caregivers_raw = [
            ("c1", "123456"),
            ("c2", "123456"),
            ("c3", "123456"),
        ]
        for username, plain_pw in caregivers_raw:
            salt, pwd_hash = hash_password(plain_pw)
            cursor.execute(
                "INSERT INTO Caregivers (Username, Salt, Hash) VALUES (?, ?, ?)",
                (username, salt, pwd_hash),
            )

        # 3. Patients (Username, Salt, Hash)
        patients_raw = [
            ("p1", "123456"),
            ("p2", "123456"),
        ]
        for username, plain_pw in patients_raw:
            salt, pwd_hash = hash_password(plain_pw)
            cursor.execute(
                "INSERT INTO Patients (Username, Salt, Hash) VALUES (?, ?, ?)",
                (username, salt, pwd_hash),
            )

        # 4. Availabilities (Time, Username)
        availabilities = [
            ("2026-12-03", "c1"),
            ("2026-12-03", "c2"),
            ("2026-12-04", "c1"),
            ("2026-12-05", "c3"),
        ]
        cursor.executemany(
            "INSERT INTO Availabilities (Time, Username) VALUES (?, ?)",
            availabilities,
        )

        # 5. Reservations (rid, Time, pname, cname, vname)
        reservations = [
            (1, "2026-12-02", "p1", "c1", "covid"),
        ]
        cursor.executemany(
            """
            INSERT INTO Reservations (rid, Time, pname, cname, vname)
            VALUES (?, ?, ?, ?, ?)
            """,
            reservations,
        )

        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
        print(f"Applied schema from {schema_path} and seeded database successfully.")
    except Exception:
        conn.rollback()
        cursor.execute("PRAGMA foreign_keys = ON;")
        raise
    finally:
        cm.close_connection()


if __name__ == "__main__":
    seed()