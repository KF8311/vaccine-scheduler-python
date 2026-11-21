import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

# Resolve .../src relative to this test file.
THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[2]  # .../src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

SCHEDULER_DIR = SRC_DIR / "main" / "scheduler"
if str(SCHEDULER_DIR) not in sys.path:
    sys.path.insert(0, str(SCHEDULER_DIR))

SCHEMA_PATH = SRC_DIR / "main" / "resources" / "sqlite" / "create.sql"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_cmd(scheduler_mod, command_line: str) -> str:
    """Execute a single CLI command through Scheduler's handler and capture stdout."""
    buf = io.StringIO()
    tokens = command_line.strip().split()
    cmd = tokens[0]

    dispatch = {
        "create_patient": getattr(scheduler_mod, "create_patient", None),
        "create_caregiver": getattr(scheduler_mod, "create_caregiver", None),
        "login_patient": getattr(scheduler_mod, "login_patient", None),
        "login_caregiver": getattr(scheduler_mod, "login_caregiver", None),
        "search_caregiver_schedule": getattr(scheduler_mod, "search_caregiver_schedule", None),
        "reserve": getattr(scheduler_mod, "reserve", None),
        "upload_availability": getattr(scheduler_mod, "upload_availability", None),
        "cancel": getattr(scheduler_mod, "cancel", None),
        "add_doses": getattr(scheduler_mod, "add_doses", None),
        "show_appointments": getattr(scheduler_mod, "show_appointments", None),
        "logout": getattr(scheduler_mod, "logout", None),
    }

    handler = dispatch.get(cmd)
    if handler is None:
        raise AttributeError(f"Command handler '{cmd}' not found in Scheduler module.")

    with contextlib.redirect_stdout(buf):
        handler(tokens)

    return buf.getvalue().strip()


class TestVaccineScheduler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.test_db_path = str(Path(cls.tmp_dir.name) / "hw6.db")
        os.environ["DBPATH"] = cls.test_db_path

        if str(SRC_DIR) not in sys.path:
            sys.path.insert(0, str(SRC_DIR))

        scheduler_dir = THIS_FILE.parent
        if str(scheduler_dir) not in sys.path:
            sys.path.insert(0, str(scheduler_dir))

        seed_candidates = [
            scheduler_dir / "seed.py",
            SRC_DIR / "main" / "seed.py",
            SRC_DIR / "seed.py",
        ]
        seed_path = next((p for p in seed_candidates if p.exists()), None)
        if seed_path is None:
            raise FileNotFoundError(f"Could not find seed.py in: {seed_candidates}")
        cls.seed_mod = load_module("hw6_seed_under_test", seed_path)

        scheduler_candidates = [
            scheduler_dir / "scheduler.py",
            scheduler_dir / "Scheduler.py",
        ]
        scheduler_path = next((p for p in scheduler_candidates if p.exists()), None)
        if scheduler_path is None:
            raise FileNotFoundError(f"Could not find scheduler.py in: {scheduler_candidates}")
        cls.scheduler_mod = load_module("hw6_scheduler_under_test", scheduler_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    def setUp(self):
        # Fresh schema + clean seeded data before every test
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        self.seed_mod.seed(SCHEMA_PATH)

        # Reset session state if present
        if hasattr(self.scheduler_mod, "current_caregiver"):
            self.scheduler_mod.current_caregiver = None
        if hasattr(self.scheduler_mod, "current_patient"):
            self.scheduler_mod.current_patient = None

    def test_create_and_login_patient(self):
        out = run_cmd(self.scheduler_mod, "create_patient p3 Pass123!")
        self.assertEqual(out, "Created user p3")

        dup_out = run_cmd(self.scheduler_mod, "create_patient p3 Pass123!")
        self.assertEqual(dup_out, "Username taken, try again")

        login_out = run_cmd(self.scheduler_mod, "login_patient p3 Pass123!")
        self.assertEqual(login_out, "Logged in as p3")

        already_out = run_cmd(self.scheduler_mod, "login_patient p1 123456")
        self.assertEqual(already_out, "User already logged in, try again")

        logout_out = run_cmd(self.scheduler_mod, "logout")
        self.assertEqual(logout_out, "Successfully logged out")

    def test_search_caregiver_schedule(self):
        self.assertEqual(
            run_cmd(self.scheduler_mod, "search_caregiver_schedule 2026-12-03"),
            "Please login first",
        )

        run_cmd(self.scheduler_mod, "login_patient p1 123456")
        out = run_cmd(self.scheduler_mod, "search_caregiver_schedule 2026-12-03")
        expected = "\n".join([
            "Caregiver:",
            "c1",
            "c2",
            "Vaccines:",
            "covid 5",
            "flu 3",
            "hpv 2",
        ])
        self.assertEqual(out, expected)

    def test_reserve_and_show_appointments(self):
        self.assertEqual(
            run_cmd(self.scheduler_mod, "reserve 2026-12-03 covid"),
            "Please login first",
        )

        run_cmd(self.scheduler_mod, "login_caregiver c1 123456")
        self.assertEqual(
            run_cmd(self.scheduler_mod, "reserve 2026-12-03 covid"),
            "Please login as a patient",
        )
        run_cmd(self.scheduler_mod, "logout")

        run_cmd(self.scheduler_mod, "login_patient p1 123456")
        reserve_out = run_cmd(self.scheduler_mod, "reserve 2026-12-03 covid")
        self.assertTrue(reserve_out.startswith("Appointment ID "))
        self.assertIn(", Caregiver username c1", reserve_out)

        # c1 should no longer be available on 2026-12-03; only c2 remains
        sched_out = run_cmd(self.scheduler_mod, "search_caregiver_schedule 2026-12-03")
        self.assertIn("Caregiver:\nc2\nVaccines:", sched_out)

        # Seeded reservation is (1, '2026-12-02', 'p1', 'c1', 'covid'), plus new one
        appts_out = run_cmd(self.scheduler_mod, "show_appointments")
        lines = appts_out.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "1 covid 2026-12-02 c1")

    def test_cancel_appointment_extra_credit(self):
        # Unauthenticated
        self.assertEqual(
            run_cmd(self.scheduler_mod, "cancel 1"),
            "Please login first",
        )

        # Patient p1 owns seeded appointment 1 (2026-12-02, c1, covid)
        run_cmd(self.scheduler_mod, "login_patient p1 123456")
        cancel_out = run_cmd(self.scheduler_mod, "cancel 1")
        self.assertEqual(cancel_out, "Appointment ID 1 has been successfully canceled")

        # Nonexistent ID
        missing_out = run_cmd(self.scheduler_mod, "cancel 999")
        self.assertEqual(missing_out, "Appointment ID 999 does not exist")

        # Dose restored from 5 -> 6 and c1 available again on 2026-12-02
        sched_out = run_cmd(self.scheduler_mod, "search_caregiver_schedule 2026-12-02")
        self.assertEqual(
            sched_out,
            "\n".join([
                "Caregiver:",
                "c1",
                "Vaccines:",
                "covid 6",
                "flu 3",
                "hpv 2",
            ]),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
