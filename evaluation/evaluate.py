import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from rapidfuzz import fuzz

def load_medbullets_test(file_path: str) -> List[Dict[str, Any]]:
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def format_case_text(record: Dict[str, Any]) -> str:
    question = record.get("question", "")
    choices = [
        f"A. {record.get('choicesA', '')}",
        f"B. {record.get('choicesB', '')}",
        f"C. {record.get('choicesC', '')}",
        f"D. {record.get('choicesD', '')}",
        f"E. {record.get('choicesE', '')}"
    ]
    # Filter out empty choices
    choices = [c for c in choices if not c.endswith(". ")]
    return f"{question}\n\n" + "\n".join(choices)

def evaluate(dataset_path: str, limit: int = None):
    print(f"Loading dataset from {dataset_path}...")
    records = load_medbullets_test(dataset_path)
    
    if limit is not None:
        records = records[:limit]
        print(f"Limiting evaluation to {limit} records.")
        
    print(f"Initializing CDSS pipeline client...")
    client = TestClient(app)
    
    # Send a warm-up request to ensure everything is loaded
    print("Sending warm-up request to initialize lazy services...")
    client.post("/analyze", json={"case_text": "warmup"})
    
    top1_correct = 0
    top3_correct = 0
    total_time = 0.0
    total_processed = 0
    
    print("\n--- Starting Evaluation ---")
    for i, record in enumerate(records):
        case_text = format_case_text(record)
        ground_truth_answer = str(record.get("answer", "")).lower()
        
        start_time = time.time()
        response = client.post("/analyze", json={"case_text": case_text})
        elapsed = time.time() - start_time
        total_time += elapsed
        
        if response.status_code != 200:
            print(f"[{i+1}/{len(records)}] Error processing record: {response.status_code} - {response.text}")
            continue
            
        data = response.json()
        report_data = data.get("report", {})
        ranked_diagnoses = report_data.get("ranked_diagnoses", [])
        
        # Extract diagnosis strings and lowercase them
        system_diagnoses = [d.get("diagnosis", "").lower() for d in ranked_diagnoses]
        
        is_top1 = False
        is_top3 = False
        
        # Check against top 1
        if system_diagnoses and len(system_diagnoses) > 0:
            score = fuzz.partial_ratio(ground_truth_answer, system_diagnoses[0])
            if score >= 80 or ground_truth_answer in system_diagnoses[0] or system_diagnoses[0] in ground_truth_answer:
                is_top1 = True
                
        # Check against top 3
        for diag in system_diagnoses[:3]:
            score = fuzz.partial_ratio(ground_truth_answer, diag)
            if score >= 80 or ground_truth_answer in diag or diag in ground_truth_answer:
                is_top3 = True
                break
                
        if is_top1: top1_correct += 1
        if is_top3: top3_correct += 1
        total_processed += 1
        
        # Print progress
        status = "✅" if is_top1 else ("☑️" if is_top3 else "❌")
        print(f"[{i+1}/{len(records)}] {status} | Time: {elapsed:.2f}s | Truth: '{ground_truth_answer[:30]}...' | Top Pred: '{system_diagnoses[0][:30] if system_diagnoses else 'None'}...'")
        
    print("\n--- Evaluation Results ---")
    print(f"Total Processed: {total_processed}")
    print(f"Top-1 Accuracy:  {(top1_correct / total_processed) * 100:.2f}% ({top1_correct}/{total_processed})")
    print(f"Top-3 Accuracy:  {(top3_correct / total_processed) * 100:.2f}% ({top3_correct}/{total_processed})")
    print(f"Average Latency: {total_time / total_processed:.2f} seconds/query")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate CDSS Pipeline")
    parser.add_argument("--dataset", type=str, default="datasets/literature/medbulltes5op/test.json", help="Path to MedBullets test.json")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records to evaluate")
    args = parser.parse_args()
    
    # Make dataset path relative to project root if it's relative
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = args.dataset
    if not os.path.isabs(dataset_path):
        dataset_path = os.path.join(base_dir, dataset_path)
        
    evaluate(dataset_path, args.limit)
