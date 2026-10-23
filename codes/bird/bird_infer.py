import json
import requests

def run_bird_inference():
    # 1. Load questions from your data folder
    with open('data/mini_dev_sqlite.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if content.startswith('['):
            data = json.loads(content)
        else:
            data = [json.loads(line) for line in content.splitlines() if line.strip()]

    predictions = []
    total = len(data)
    print(f"Loaded {total} questions. Starting Ollama inference...")
    
    for idx, item in enumerate(data, 1):
        db_id = item['db_id']
        question = item['question']
        evidence = item.get('evidence', '')
        
        prompt = (
            f"Given the database {db_id}.\n"
            f"Evidence: {evidence}\n"
            f"Question: {question}\n"
            "Write a SQLite query to answer the question. Output ONLY the SQL query.\n"
            "SQL:"
        )
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_ctx": 8192
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            raw_response = response.json().get('response', '').strip()
        except Exception as e:
            print(f"[{idx}/{total}] Request failed for Q{item.get('question_id')}: {e}")
            raw_response = "SELECT 1;"

        # Clean markdown wrappers if model returned code fences
        sql = raw_response.replace("```sql", "").replace("```", "").replace("\n", " ").strip()
        
        # Format required by BIRD: <SQL> \t----- bird -----\t <db_id>
        predictions.append(f"{sql}\t----- bird -----\t{db_id}\n")
        print(f"[{idx}/{total}] Processed BIRD: {item.get('question_id', idx)}")

    with open('predict_mini_dev.txt', 'w', encoding='utf-8') as f:
        f.writelines(predictions)

    print("Inference completed! Saved to predict_mini_dev.txt")

if __name__ == "__main__":
    run_bird_inference()