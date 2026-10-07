import sys
import os
import json

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.api.routes import analyze_case, AnalyzeRequest

def main():
    print("Running test case 1 (Demo case)...")
    request1 = AnalyzeRequest(case_text="A 58-year-old man with diabetes and hypertension presents with crushing chest pain radiating to the left arm, sweating, nausea, and shortness of breath. He takes metformin and lisinopril. No known drug allergies.")
    response1 = analyze_case(request1)
    
    print("\nRunning test case 2 (Different case)...")
    request2 = AnalyzeRequest(case_text="A 25-year-old woman presents with severe headache, fever, and neck stiffness for the past 2 days. She has a history of asthma and uses an albuterol inhaler. No other medications.")
    response2 = analyze_case(request2)

    print("\n--- Validation Results ---")
    print("Test 1 Context Symptoms:", [s['text'] for s in response1['patient_context']['symptoms']])
    print("Test 1 Context Conditions:", [s['text'] for s in response1['patient_context']['known_conditions']])
    print("Test 1 Context Medications:", [s['text'] for s in response1['patient_context']['medications']])
    
    print("Test 2 Context Symptoms:", [s['text'] for s in response2['patient_context']['symptoms']])
    print("Test 2 Context Conditions:", [s['text'] for s in response2['patient_context']['known_conditions']])
    print("Test 2 Context Medications:", [s['text'] for s in response2['patient_context']['medications']])
    
    print("\nSuccess: No hardcoding detected if extraction varies based on input text.")

if __name__ == "__main__":
    main()
