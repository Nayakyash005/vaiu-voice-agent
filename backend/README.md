# VAIU Phone API

Install the backend dependencies and run the API from the repository root:

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.API.main:app --reload
```

The SQLite database is created automatically at `backend/phone_records.db`.
