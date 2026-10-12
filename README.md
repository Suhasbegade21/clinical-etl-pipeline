# Clinical ETL Pipeline

NLP-powered ETL pipeline for unstructured clinical data. Paste a free-text clinical note, extract the conditions and medications it mentions with a biomedical NLP model, load them into a PostgreSQL star schema, and explore frequency statistics from a web dashboard.

> **Disclaimer:** This is a learning/demo project. Do not use it with real patient data (PHI), and do not use its output for clinical decisions.

## Features

- **Extraction** of medical entities from free text using scispaCy (`en_core_sci_sm`)
- **Transform** step that title-cases terms, sorts them into conditions vs. medications, and removes duplicates
- **Load** into a PostgreSQL star schema (patient, condition and medication dimensions plus an extraction fact table)
- **Analytics** endpoint that counts the most frequent conditions and medications
- **Web UI** with a patient sidebar, extraction results and chart, an analytics view (bar, doughnut and line charts), CSV export, dark mode, and per-entity delete

## How it works

```
Clinical note --> Extract --------> Transform ---------> Load ---------------> Mine
                  (scispaCy NER)    (classify, dedupe)   (PostgreSQL star       (counts,
                                                          schema)                co-occurrence)
```

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn, SQLAlchemy |
| NLP | spaCy, scispaCy (`en_core_sci_sm`) |
| Database | PostgreSQL |
| Web UI | Flask, Tailwind CSS, Chart.js, Lucide icons (loaded from CDNs) |
| Experimental UI | Streamlit (unfinished) |

## Project structure

```
clinical-etl-pipeline/
├── backend/
│   ├── main.py            # FastAPI app and endpoints
│   ├── nlp_engine.py      # scispaCy entity extraction and classification
│   ├── database.py        # SQLAlchemy engine and session factory
│   ├── models.py          # ORM models for the star schema
│   └── requirements.txt
├── database/
│   └── schema.sql         # PostgreSQL table definitions
└── frontend/
    ├── run_ui.py          # Flask server for the main web UI
    ├── templates/
    │   └── index.html     # Single-page UI
    └── app.py             # Experimental Streamlit UI
```

## Getting started

### Prerequisites

- Python 3.12 (the version the project was developed on)
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/vee-1745/clinical-etl-pipeline.git
cd clinical-etl-pipeline
```

### 2. Create a virtual environment and install dependencies

```bash
cd backend
python -m venv venv
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate

pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic spacy scispacy flask
```

Then install the `en_core_sci_sm` model. Use the download link that matches your scispaCy version from the model table in the [scispaCy README](https://github.com/allenai/scispacy).

### 3. Set up the database

```bash
psql -U postgres -c "CREATE DATABASE clinical_db;"
psql -U postgres -d clinical_db -f ../database/schema.sql
```

If `/extract` later fails with an `ON CONFLICT` error, the patient table is missing a unique constraint. Add it with:

```sql
ALTER TABLE Dim_Patient ADD CONSTRAINT dim_patient_patient_id_key UNIQUE (Patient_ID);
```

### 4. Configure the database connection

Open `backend/database.py` and set the connection string for your own PostgreSQL user, password and database (it defaults to host `localhost`, port `5432`, database `clinical_db`). Do not commit real credentials.

### 5. Start the backend

```bash
cd backend
python main.py
```

The API runs at http://127.0.0.1:8000 and interactive docs are at http://127.0.0.1:8000/docs.

### 6. Start the web UI

In a second terminal:

```bash
cd frontend
python run_ui.py
```

Open http://127.0.0.1:5001. The UI expects the backend at `http://127.0.0.1:8000`.

## Usage

1. Click **New Patient** (or pick one in the sidebar).
2. Type or paste a clinical note and press **Enter**.
3. Review the extracted **Conditions** and **Medications**. Use the trash icon to remove a wrongly extracted item.
4. Open the **Analytics** tab to see the most frequent conditions and medications across all notes, switch chart type, or download a CSV.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/extract` | Run the pipeline on a note and store the results |
| GET | `/mine-data` | Frequency counts for conditions, medications and condition-medication pairs |
| DELETE | `/delete-entity` | Remove one extracted condition or medication for a patient |

**Extract entities**

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "PT-001", "raw_text": "Patient has type 2 diabetes and hypertension. Prescribed metformin 500 mg daily."}'
```

Response shape (the exact entities depend on the scispaCy model):

```json
{
  "message": "ETL Pipeline Executed Successfully.",
  "extraction": { "conditions": ["..."], "medications": ["..."] }
}
```

**Delete an entity** (`entity_type` is `"condition"` or `"medication"`)

```bash
curl -X DELETE http://127.0.0.1:8000/delete-entity \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "PT-001", "entity_type": "condition", "entity_name": "Hypertension"}'
```

## Data model

```
Dim_Patient ----+
Dim_Condition --+--> Fact_Clinical_Extraction (Patient_Key, Condition_Key,
Dim_Medication -+                              Medication_Key, Raw_Text, Extraction_Date)
```

Each extracted condition or medication is stored as one row in `Fact_Clinical_Extraction`, together with the original note text.

## Known limitations

- Conditions and medications are separated with a keyword and word-ending heuristic, so some terms are put in the wrong list.
- The condition-medication association query in `/mine-data` currently returns no rows, because each fact row holds either a condition or a medication, not both.
- There is no authentication and CORS allows all origins, so run it locally only.
- Database credentials live in `backend/database.py` instead of environment variables.
- The patient list in the web UI lives in browser memory. Renaming or deleting a patient there does not change the database.
- The Streamlit app (`frontend/app.py`) is unfinished; use the Flask UI.

## Contributing

Issues and pull requests are welcome. Fork the repository, create a branch, make your change, and open a pull request that describes what you changed and why.
