from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
import uvicorn
import sys

# 1. Bring back your AI Engine!
from nlp_engine import extract_clinical_data

# 2. Database Connection Import
try:
    from database import SessionLocal
except ImportError:
    print("CRITICAL ERROR: database.py not found or SessionLocal not defined.")
    sys.exit(1)

app = FastAPI(title="Clinical ETL Pipeline API", version="1.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class ExtractRequest(BaseModel):
    patient_id: str
    raw_text: str

class DeleteEntityRequest(BaseModel):
    patient_id: str
    entity_type: str
    entity_name: str

@app.get("/")
def read_root():
    return {"Status": "API is online, AI is loaded, Database is connected. Ready for ETL."}

# --- 1. EXTRACTION PIPELINE ---
@app.post("/extract")
def extract_clinical_data_endpoint(req: ExtractRequest):
    db = SessionLocal()
    try:
        # A. RUN THE REAL AI NLP ENGINE
        ai_results = extract_clinical_data(req.raw_text)
        extracted_conditions = ai_results.get("Conditions", [])
        extracted_medications = ai_results.get("Medications", [])

        # B. Handle Dim_Patient 
        db.execute(text("""
            INSERT INTO Dim_Patient (Patient_ID) 
            VALUES (:pid) 
            ON CONFLICT (Patient_ID) DO NOTHING
        """), {"pid": req.patient_id})
        db.commit()

        # Get the internal Patient_Key
        result = db.execute(text("SELECT Patient_Key FROM Dim_Patient WHERE Patient_ID = :pid"), {"pid": req.patient_id})
        row = result.fetchone()
        if not row:
            raise Exception("Patient could not be created or found.")
        p_key = row[0]

        # C. Save Conditions to Fact table
        for cond in extracted_conditions:
            db.execute(text("INSERT INTO Dim_Condition (Condition_Name) VALUES (:name) ON CONFLICT DO NOTHING"), {"name": cond})
            db.commit()
            db.execute(text("""
                INSERT INTO Fact_Clinical_Extraction (Patient_Key, Condition_Key, Raw_Text)
                SELECT :p_key, Condition_Key, :raw 
                FROM Dim_Condition WHERE Condition_Name = :name
            """), {"p_key": p_key, "name": cond, "raw": req.raw_text})

        # D. Save Medications to Fact table
        for med in extracted_medications:
            db.execute(text("INSERT INTO Dim_Medication (Medication_Name) VALUES (:name) ON CONFLICT DO NOTHING"), {"name": med})
            db.commit()
            db.execute(text("""
                INSERT INTO Fact_Clinical_Extraction (Patient_Key, Medication_Key, Raw_Text)
                SELECT :p_key, Medication_Key, :raw 
                FROM Dim_Medication WHERE Medication_Name = :name
            """), {"p_key": p_key, "name": med, "raw": req.raw_text})

        db.commit()
        
        # Send the LIVE AI results back to the frontend
        return {
            "message": "ETL Pipeline Executed Successfully.",
            "extraction": {
                "conditions": extracted_conditions,
                "medications": extracted_medications
            }
        }
    except Exception as e:
        db.rollback()
        print(f"DATABASE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# --- 2. ANALYTICS (MINING) ---
@app.get("/mine-data")
def mine_clinical_data():
    db = SessionLocal()
    try:
        # Count Conditions (LIMIT removed to show all)
        query_conditions = text("""
            SELECT c.Condition_Name, COUNT(*) as frequency
            FROM Fact_Clinical_Extraction f
            JOIN Dim_Condition c ON f.Condition_Key = c.Condition_Key
            GROUP BY c.Condition_Name ORDER BY frequency DESC;
        """)
        top_conditions = [{"condition": row[0], "count": row[1]} for row in db.execute(query_conditions).fetchall()]

        # Count Medications (LIMIT removed to show all)
        query_meds = text("""
            SELECT m.Medication_Name, COUNT(*) as frequency
            FROM Fact_Clinical_Extraction f
            JOIN Dim_Medication m ON f.Medication_Key = m.Medication_Key
            GROUP BY m.Medication_Name ORDER BY frequency DESC;
        """)
        top_medications = [{"medication": row[0], "count": row[1]} for row in db.execute(query_meds).fetchall()]

        # Association Rule Mining (LIMIT removed to show all connections)
        query_associations = text("""
            SELECT c.Condition_Name, m.Medication_Name, COUNT(*) as co_occurrence
            FROM Fact_Clinical_Extraction f
            JOIN Dim_Condition c ON f.Condition_Key = c.Condition_Key
            JOIN Dim_Medication m ON f.Medication_Key = m.Medication_Key
            GROUP BY c.Condition_Name, m.Medication_Name
            ORDER BY co_occurrence DESC;
        """)
        associations = [{"condition": row[0], "medication": row[1], "frequency": row[2]} for row in db.execute(query_associations).fetchall()]

        return {
            "status": "success",
            "mining_results": {
                "top_conditions": top_conditions,
                "top_medications": top_medications,
                "frequent_associations": associations
            }
        }
    except Exception as e:
        print(f"MINING ERROR: {e}")
        return {"error": str(e)}
    finally:
        db.close()

# --- 3. DELETE DATA ---
@app.delete("/delete-entity")
def delete_extracted_entity(req: DeleteEntityRequest):
    db = SessionLocal()
    try:
        if req.entity_type == "condition":
            sql = text("""
                DELETE FROM Fact_Clinical_Extraction 
                WHERE Patient_Key IN (SELECT Patient_Key FROM Dim_Patient WHERE Patient_ID = :pid)
                AND Condition_Key IN (SELECT Condition_Key FROM Dim_Condition WHERE Condition_Name = :name);
            """)
        else:
            sql = text("""
                DELETE FROM Fact_Clinical_Extraction 
                WHERE Patient_Key IN (SELECT Patient_Key FROM Dim_Patient WHERE Patient_ID = :pid)
                AND Medication_Key IN (SELECT Medication_Key FROM Dim_Medication WHERE Medication_Name = :name);
            """)
        
        db.execute(sql, {"pid": req.patient_id, "name": req.entity_name})
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        print(f"DELETE ERROR: {e}")
        return {"error": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)