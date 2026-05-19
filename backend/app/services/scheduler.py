from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from app.core.config import get_settings
from app.models.models import IntegrationFlow, ExecutionHistory, NodeExecutionLogs
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

        flow_data = {
            "nodes": flow.flow_nodes,
            "connections": flow.flow_connections,
            "metadata": flow.flow_metadata
        }
        
        from app.services.source_executor import pre_execute_flow_nodes
        pre_exec_ok, flow_data = await pre_execute_flow_nodes(flow_data, db)
        
        # Trigger execution via Deno service
        async for log in deno_service.run_flow_stream(flow_data, {}):
            if log["type"] == "node_log":
                start_dt = None
                if log.get("start_time"):
                    try:
                        iso_str = log.get("start_time").replace("Z", "+00:00")
                        start_dt = datetime.fromisoformat(iso_str)
                    except Exception:
                        pass
                
                end_dt = None
                if log.get("end_time"):
                    try:
                        iso_str = log.get("end_time").replace("Z", "+00:00")
                        end_dt = datetime.fromisoformat(iso_str)
                    except Exception:
                        pass

                node_log = NodeExecutionLogs(
                    execution_id=execution_id,
                    node_id=log["node_id"],
                    status=log["status"],
                    input_data=log["input"],
                    output_data=log["output"],
                    duration=log["duration"],
                    start_time=start_dt or datetime.utcnow(),
                    end_time=end_dt
                )
                db.add(node_log)
            elif log["type"] == "status":
                history.status = "success" if log["success"] else "error"
        
        history.end_time = datetime.utcnow()
        flow.last_run = history.end_time
        flow.last_run_success = (history.status == "success")
        
        # Update next_run_at for the next occurrence if it's a scheduled flow
        if flow.cron_expression and flow.status in ("active", "scheduled"):
            try:
                from apscheduler.triggers.cron import CronTrigger
                trigger = CronTrigger.from_crontab(flow.cron_expression)
                flow.next_run_at = trigger.get_next_fire_time(None, datetime.utcnow())
            except Exception as cron_err:
                print(f"Error calculating next run for flow {flow_id}: {cron_err}")
                
        db.commit()

    except Exception as e:
        print(f"Error executing flow {flow_id}: {e}")
    finally:
        db.close()

def schedule_flow(flow):
    from app.core.database import SessionLocal
    job_id = f"flow-{flow.id}"
    if not flow.cron_expression or flow.status not in ("active", "scheduled"):
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            print(f"Unscheduled flow {flow.id}")
        return

    try:
        trigger = CronTrigger.from_crontab(flow.cron_expression)
        next_run = trigger.get_next_fire_time(None, datetime.utcnow())
        
        scheduler.add_job(
            run_integration_flow,
            trigger,
            args=[flow.id],
            id=job_id,
            replace_existing=True
        )
        
        # Update next_run_at in DB
        db = SessionLocal()
        try:
            flow_db = db.query(IntegrationFlow).filter(IntegrationFlow.id == flow.id).first()
            if flow_db:
                flow_db.next_run_at = next_run
                db.commit()
        finally:
            db.close()
            
        print(f"Scheduled flow {flow.id} ({flow.name}) with cron: {flow.cron_expression}. Next run: {next_run}")
    except Exception as e:
        print(f"Error scheduling flow {flow.id}: {e}")

def unschedule_flow(flow_id: str):
    job_id = f"flow-{flow_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        print(f"Unscheduled flow {flow_id}")

def init_scheduler():
    scheduler.start()
    
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        scheduled_flows = db.query(IntegrationFlow).filter(IntegrationFlow.cron_expression.isnot(None)).all()
        for flow in scheduled_flows:
            schedule_flow(flow)
    finally:
        db.close()
    print("Scheduler initialized")
