from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.core.config import get_settings
from app.models.models import IntegrationFlow, ExecutionHistory
from app.services.deno_service import deno_service
import uuid
from datetime import datetime

settings = get_settings()

# Define scheduler with sqlalchemy jobstore for persistence
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.database_url)
}

scheduler = AsyncIOScheduler(jobstores=jobstores)

async def run_integration_flow(flow_id: str):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        flow = db.query(IntegrationFlow).filter(IntegrationFlow.id == flow_id).first()
        if not flow:
            return

        # Create history record
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        history = ExecutionHistory(
            id=execution_id,
            flow_id=flow_id,
            status="running"
        )
        db.add(history)
        db.commit()

        # Trigger execution via Deno service
        async for log in deno_service.run_flow_stream(flow.flow_nodes, flow.flow_connections, flow.flow_metadata, flow.payload):
            if log["type"] == "node_log":
                node_log = NodeExecutionLogs(
                    execution_id=execution_id,
                    node_id=log["node_id"],
                    status=log["status"],
                    input_data=log["input"],
                    output_data=log["output"],
                    duration=log["duration"]
                )
                db.add(node_log)
            elif log["type"] == "status":
                history.status = "success" if log["success"] else "error"
        
        history.end_time = datetime.utcnow()
        db.commit()

    except Exception as e:
        print(f"Error executing flow {flow_id}: {e}")
    finally:
        db.close()

def init_scheduler():
    scheduler.start()
    # Logic to load/re-add scheduled flows from DB would go here
    print("Scheduler initialized")
