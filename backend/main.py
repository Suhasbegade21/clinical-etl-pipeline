from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from nlp_engine import extract_clinical_data
from database import engine, get_db, SessionLocal
import models

# This command automatically creates the tables in PostgreSQL if they don't exist!
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinical ETL Pipeline API", version="1.0")

class ClinicalNote(BaseModel):
    patient_id: str
    raw_text: str

@app.get("/")
def read_root():
    return {"Status": "API is online, AI is loaded, Database is connected. Ready for ETL."}

@app.post("/extract")
def process_clinical_note(note: ClinicalNote, db: Session = Depends(get_db)):
    # --- 1. EXTRACT & TRANSFORM (NLP AI) ---
    ai_results = extract_clinical_data(note.raw_text)
    
    # --- 2. LOAD (Database Insertion) ---
    
    # Check if Patient exists, if not, create them
    patient = db.query(models.DimPatient).filter(models.DimPatient.patient_id == note.patient_id).first()
    if not patient:
        patient = models.DimPatient(patient_id=note.patient_id, age_group="Unknown", gender="Unknown")
        db.add(patient)
        db.commit()
        db.refresh(patient)

    extracted_conditions = ai_results.get("Conditions", [])
    extracted_medications = ai_results.get("Medications", [])
    
    condition_keys = []
    medication_keys = []

    # Process Conditions
    for c_name in extracted_conditions:
        cond = db.query(models.DimCondition).filter(models.DimCondition.condition_name == c_name).first()
        if not cond:
            cond = models.DimCondition(condition_name=c_name)
            db.add(cond)
            db.commit()
            db.refresh(cond)
        condition_keys.append(cond.condition_key)

    # Process Medications
    for m_name in extracted_medications:
        med = db.query(models.DimMedication).filter(models.DimMedication.medication_name == m_name).first()
        if not med:
            med = models.DimMedication(medication_name=m_name)
            db.add(med)
            db.commit()
            db.refresh(med)
        medication_keys.append(med.medication_key)

    # If no conditions or meds were found, we still want to record the text, so we use None (Null)
    if not condition_keys: condition_keys = [None]
    if not medication_keys: medication_keys = [None]

    # Insert into the Fact Table
    for c_key in condition_keys:
        for m_key in medication_keys:
            fact_record = models.FactExtraction(
                patient_key=patient.patient_key,
                condition_key=c_key,
                medication_key=m_key,
                raw_text=note.raw_text
            )
            db.add(fact_record)
    
    db.commit()

    return {
        "message": "ETL Pipeline Executed Successfully. Data saved to Warehouse.",
        "patient_id": patient.patient_id,
        "extracted_data": ai_results
    }

from sqlalchemy import text
# (Make sure you already have your db connection imports at the top of the file, 
# like: from database import SessionLocal)

@app.get("/mine-data")
def mine_clinical_data():
    db = SessionLocal()
    try:
        # 1. Mine Top Conditions
        query_conditions = text("""
            SELECT c.condition_name, COUNT(*) as frequency
            FROM fact_clinical_extraction f
            JOIN dim_condition c ON f.condition_key = c.condition_key
            GROUP BY c.condition_name
            ORDER BY frequency DESC
            LIMIT 5;
        """)
        top_conditions = [{"condition": row[0], "count": row[1]} for row in db.execute(query_conditions).fetchall() if row[0]]

        # 2. Mine Top Medications
        query_meds = text("""
            SELECT m.medication_name, COUNT(*) as frequency
            FROM fact_clinical_extraction f
            JOIN dim_medication m ON f.medication_key = m.medication_key
            GROUP BY m.medication_name
            ORDER BY frequency DESC
            LIMIT 5;
        """)
        top_medications = [{"medication": row[0], "count": row[1]} for row in db.execute(query_meds).fetchall() if row[0]]

        # 3. Association Rule Mining
        query_associations = text("""
            SELECT c.condition_name, m.medication_name, COUNT(*) as co_occurrence
            FROM fact_clinical_extraction f
            JOIN dim_condition c ON f.condition_key = c.condition_key
            JOIN dim_medication m ON f.medication_key = m.medication_key
            GROUP BY c.condition_name, m.medication_name
            ORDER BY co_occurrence DESC
            LIMIT 10;
        """)
        associations = [{"condition": row[0], "medication": row[1], "frequency": row[2]} for row in db.execute(query_associations).fetchall() if row[0] and row[1]]

        return {
            "status": "success",
            "mining_results": {
                "top_conditions": top_conditions,
                "top_medications": top_medications,
                "frequent_associations": associations
            }
        }
    except Exception as e:
        print(f"SQL MINING ERROR: {str(e)}") 
        return {"error": str(e)}
    finally:
        db.close()