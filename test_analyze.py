import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.api.routes import analyze_case, AnalyzeRequest
import json

request = AnalyzeRequest(case_text="A 58-year-old man with diabetes and hypertension presents with crushing chest pain radiating to the left arm, sweating, nausea, and shortness of breath. He takes metformin and lisinopril. No known drug allergies.")
response = analyze_case(request)

print(json.dumps(response, indent=2))
