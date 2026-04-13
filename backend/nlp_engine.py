import spacy
import scispacy

# Load the medical specialist model
# It might take a few seconds to load the first time
nlp = spacy.load("en_core_sci_sm")

def extract_clinical_data(text):
    """
    Uses scispaCy Named Entity Recognition to find 
    medical conditions and medications automatically.
    """
    doc = nlp(text)
    
    extracted_conditions = []
    extracted_medications = []
    
    # scispaCy identifies 'ENTITIES' based on clinical context
    for ent in doc.ents:
        term = ent.text.title()
        lower_term = ent.text.lower()
        
        # Sorting logic:
        # We look for common drug indicators to separate meds from conditions.
        drug_hints = [
            'mg', 'tablet', 'capsule', 'pill', 'dose', 'mcg', 
            'solution', 'intravenous', 'iv', 'oral', 'daily', 'bid', 'tid'
        ]
        
        # Check if it looks like a drug or has a common pharmaceutical suffix
        if any(hint in lower_term for hint in drug_hints) or lower_term.endswith(('in', 'ol', 'id', 'pam')):
            extracted_medications.append(term)
        else:
            # Otherwise, categorize as a condition/diagnosis/symptom
            extracted_conditions.append(term)

    return {
        "Conditions": list(set(extracted_conditions)),
        "Medications": list(set(extracted_medications))
    }