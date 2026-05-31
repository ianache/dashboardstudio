import os
import sys
import json
import subprocess
import logging
import sklearn
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import models

logger = logging.getLogger(__name__)

STORAGE_DIR = "storage/models"
WORKER_SCRIPT = "app/runtime/ml_worker.py"

async def execute_ml_node(props: Dict[str, Any], payload: Any, db: Session) -> Dict[str, Any]:
    """
    Executes a scikit-learn model inference in an isolated subprocess.
    Includes sklearn version mismatch detection.
    """
    model_id = props.get("model_id")
    if not model_id:
        return {"success": False, "error": "No model selected"}

    # 1. Fetch model from DB
    db_model = db.query(models.MLModel).filter(models.MLModel.id == model_id).first()
    if not db_model:
        return {"success": False, "error": f"Model {model_id} not found in database"}

    file_path = os.path.join(STORAGE_DIR, db_model.filename)
    if not os.path.exists(file_path):
        return {"success": False, "error": f"Model file {db_model.filename} missing from storage"}

    # 2. Check for version mismatch
    warning = None
    current_version = sklearn.__version__
    if db_model.sklearn_version and db_model.sklearn_version != current_version:
        warning = f"Model version ({db_model.sklearn_version}) differs from server version ({current_version}). Predictions may be inconsistent."

    # 3. Spawn isolated worker for prediction
    try:
        # We use a subprocess to prevent RCE from pickle.load
        # Communicate via stdin/stdout pipes
        process = subprocess.Popen(
            ["python", WORKER_SCRIPT, "--mode", "predict", "--model-path", file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Serialize payload to JSON and send to stdin
        # Ensure payload is a list or object compatible with pandas
        stdout, stderr = process.communicate(input=json.dumps(payload), timeout=30.0)
        
        if process.returncode != 0:
            error_msg = stderr or "Unknown worker error"
            try:
                error_json = json.loads(stdout)
                error_msg = error_json.get("error", error_msg)
            except:
                pass
            return {"success": False, "error": f"ML Worker failed: {error_msg}"}

        # Parse results
        predictions = json.loads(stdout)
        
        # 4. Format output
        # Map predictions back to the payload or return as a list
        # Standard: Add 'prediction' column if input is a list of rows
        output_payload = []
        if isinstance(payload, list):
            for i, row in enumerate(payload):
                new_row = dict(row) if isinstance(row, dict) else {"input": row}
                new_row["prediction"] = predictions[i] if i < len(predictions) else None
                output_payload.append(new_row)
        else:
            output_payload = {
                "input": payload,
                "prediction": predictions[0] if isinstance(predictions, list) and len(predictions) > 0 else predictions
            }

        return {
            "success": True,
            "output": output_payload,
            "warning": warning
        }

    except subprocess.TimeoutExpired:
        process.kill()
        return {"success": False, "error": "Inference timed out after 30 seconds"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected ML Executor error: {str(e)}"}
