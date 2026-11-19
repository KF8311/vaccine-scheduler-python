# Python Application for Vaccine Scheduler

# Set up Guide
Create the conda env:
```bash
conda create -n hw6 python=3.10
```
Start it:
```bash
conda activate hw6
```
Deactivate the venv:
```bash
conda deactivate
```

Run the `Scheduler.py`
```bash
cd src/main/scheduler
python Scheduler.py
```
Init the db:
```bash
python -c "import sqlite3; conn = sqlite3.connect('database/hw6.db'); conn.executescript(open('src/main/resources/sqlite/create.sql', encoding='utf-8').read()); conn.commit(); conn.close()"
```

Set the path:
```conda env config vars set DBPATH="C:/Users/lambo/UW/CSE414/homework/hw6/vaccine-scheduler-python/database/hw6.db"```