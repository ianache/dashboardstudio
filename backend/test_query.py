import sys
import os

sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models import models
from app.schemas import schemas

db = SessionLocal()
flows = db.query(models.IntegrationFlow).all()

for flow in flows:
    latest_exec = db.query(models.ExecutionHistory).filter(models.ExecutionHistory.flow_id == flow.id).order_by(models.ExecutionHistory.start_time.desc()).first()
    if latest_exec:
        if latest_exec.status == "running":
            nodes_done = db.query(models.NodeExecutionLogs).filter(models.NodeExecutionLogs.execution_id == latest_exec.id).count()
            total = len(flow.flow_nodes) if flow.flow_nodes else 1
            prog = int((nodes_done / total) * 100)
            flow.progress = min(prog, 99)
        elif latest_exec.status == "success":
            flow.progress = 100
            flow.last_run_success = True
        else:
            flow.progress = 100
            flow.last_run_success = False
    else:
        flow.progress = 0
        
    print(f"Flow: {flow.name}, Progress: {flow.progress}, Last Run Success: {flow.last_run_success}")
    
    # Check serialization
    dto = schemas.IntegrationFlowResponse.model_validate(flow)
    print(f"Serialized Progress: {dto.progress}")
