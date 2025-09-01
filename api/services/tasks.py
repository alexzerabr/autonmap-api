import os
import json
import logging
import xmltodict
import asyncio
from datetime import datetime, timezone
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from ..config import settings
from .nmap_runner import run_nmap_scan
from ..db.session import SessionLocal
from ..db.models import Scan
from .webhooks import send_webhook

logger = logging.getLogger(__name__)

redis_conn = Redis.from_url(settings.REDIS_URL)
q = Queue('scans', connection=redis_conn)

def execute_scan_task(scan_id: str, targets: list[str], profile: str, ports: str | None, timing_template: str, callback_url: str | None):
    """Função que o worker RQ executa. Agora inclui timing_template."""
    db: Session = SessionLocal()
    scan = None
    xml_path, out_path, err_path = (None, None, None)
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} não encontrado no DB para processamento.")
            return

        scan.status = 'running'
        scan.started_at = datetime.now(timezone.utc)
        db.commit()

        xml_path, out_path, err_path = run_nmap_scan(str(scan.id), targets, profile, ports, timing_template)

        if not xml_path or not os.path.exists(xml_path):
            raise RuntimeError("Execução do Nmap falhou em produzir um arquivo de saída XML.")

        with open(xml_path, 'r') as f:
            xml_content = f.read()

        scan.result_xml = xml_content
        scan.status = 'succeeded'
        scan.finished_at = datetime.now(timezone.utc)
        logger.info(f"Scan {scan.id} bem-sucedido. Resultado salvo no banco de dados.")

        if callback_url:
            result_json = xmltodict.parse(xml_content)
            payload = {
                "id": str(scan.id),
                "status": "succeeded",
                "targets": scan.targets,
                "profile": scan.profile,
                "finished_at": scan.finished_at.isoformat(),
                "result": result_json
            }
            asyncio.run(send_webhook(callback_url, payload))

    except Exception as e:
        logger.exception(f"Um erro inesperado ocorreu no scan {scan_id}: {e}")
        if scan:
            scan.status = 'failed'
            scan.finished_at = datetime.now(timezone.utc)
    finally:
        if scan:
            db.commit()
        for p in [xml_path, out_path, err_path]:
            if p and os.path.exists(p):
                os.remove(p)
        db.close()

def create_scan_task(scan_id: str, targets: list[str], profile: str, ports: str | None, timing_template: str, callback_url: str | None):
    """Enfileira a tarefa de scan, agora incluindo o timing_template."""
    q.enqueue(
        execute_scan_task,
        scan_id=scan_id,
        targets=targets,
        profile=profile,
        ports=ports,
        timing_template=timing_template,
        callback_url=callback_url,
        job_timeout='3h'
    )
