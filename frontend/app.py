import streamlit as st
import requests
import pandas as pd

# Set page layout to be wide and professional
st.set_page_config(page_title="Clinical ETL Pipeline", layout="wide")

st.title("🏥 Clinical ETL & Data Mining Pipeline")

# Create two clean tabs for navigation
tab1, tab2 = st.tabs(["🩺 AI Extraction Engine", "📊 OLAP Data Mining Dashboard"])

# ==========================================
# TAB 1: THE EXTRACTION PIPELINE
# ==========================================
with tab1:
    st.header("Process New Clinical Note")
    st.markdown("Paste raw unstructured medical text below to extract entities and load them into the Star Schema.")
    
    # Input fields
    patient_id_input = st.text_input("Patient ID:", value="PT-001")
    note_text = st.text_area("Doctor's Note:", height=150)

    if st.button("Run ETL Pipeline"):
        if note_text and patient_id_input:
            try:
                # Payload matches exactly what FastAPI expects
                payload = {
                    "patient_id": patient_id_input,
                    "raw_text": note_text
                }
                
                # Send data to the Fast API backend
                response = requests.post("http://127.0.0.1:8000/extract", json=payload)
                
                if response.status_code == 200:
                    st.success("✅ Successfully processed and loaded into PostgreSQL Star Schema!")
                    st.json(response.json())
                else:
                    st.error(f"Backend Error: {response.status_code}")
                    st.json(response.json()) 
            except Exception as e:
                st.error("Could not connect to the Backend API. Is your FastAPI server running on port 8000?")
        else:
            st.warning("Please enter both a Patient ID and the Clinical Note before running.")

# ==========================================
# TAB 2: THE DATA MINING DASHBOARD
# ==========================================
with tab2:
    st.header("Historical Data Patterns")
    st.markdown("Querying the Star Schema for Frequency and Association Rules.")
    
    if st.button("Run Data Mining Analysis"):
        try:
            response = requests.get("http://127.0.0.1:8000/mine-data")
            
            if response.status_code == 200:
                data = response.json()["mining_results"]
                
                col1, col2 = st.columns(2)
                
                # Chart 1: Top Conditions
                with col1:
                    st.subheader("Top Conditions")
                    if data["top_conditions"]:
                        df_cond = pd.DataFrame(data["top_conditions"])
                        st.bar_chart(df_cond.set_index("condition"))
                    else:
                        st.info("No condition data found.")
                        
                # Chart 2: Top Medications
                with col2:
                    st.subheader("Top Medications")
                    if data["top_medications"]:
                        df_med = pd.DataFrame(data["top_medications"])
                        st.bar_chart(df_med.set_index("medication"))
                    else:
                        st.info("No medication data found.")
                
                st.divider()
                
                # Table: Association Rule Mining
                st.subheader("💊 Clinical Association Rules")
                st.markdown("*Which medications are most frequently prescribed for which conditions?*")
                
                if data["frequent_associations"]:
                    df_assoc = pd.DataFrame(data["frequent_associations"])
                    df_assoc.columns = ["Condition Diagnosed", "Medication Prescribed", "Co-occurrence (Count)"]
                    st.dataframe(df_assoc, use_container_width=True)
                else:
                    st.info("No association data found.")
                    
        except Exception as e:
            st.error(f"Could not fetch mining data. Error: {e}")