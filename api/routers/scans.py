import os
import json
import logging
import xmltodict
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import schemas
from ..db import models
from ..db.session import get_db
from ..services import tasks as scan_tasks
from ..security import auth

router = APIRouter(prefix="/v1/scans", tags=["Scans"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.ScanResponse, status_code=202)
def create_scan(
    scan_req: schemas.ScanCreateRequest,
    db: Session = Depends(get_db),
    token: models.Token = Depends(auth.require_scope("scan:write"))
):
    db_scan = models.Scan(
        profile=scan_req.profile.value,
        targets=scan_req.targets,
        ports=scan_req.ports,
        notes=scan_req.notes,
        callback_url=str(scan_req.callback_url) if scan_req.callback_url else None,
        tags=scan_req.tags,
        token_id=token.id
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)

    scan_tasks.create_scan_task(
        scan_id=str(db_scan.id),
        targets=db_scan.targets,
        profile=db_scan.profile,
        ports=db_scan.ports,
        timing_template=scan_req.timing_template.value,
        callback_url=db_scan.callback_url
    )
    
    logger.info(f"Scan {db_scan.id} enfileirado por token {token.id}")
    return db_scan

@router.get("/", response_model=List[schemas.ScanResponse])
def list_scans(
    db: Session = Depends(get_db),
    token: models.Token = Depends(auth.require_scope("scan:read")),
    skip: int = 0,
    limit: int = 100
):
    scans = db.query(models.Scan).order_by(models.Scan.created_at.desc()).offset(skip).limit(limit).all()
    return scans

@router.get("/{id}", response_model=schemas.ScanResultResponse)
def get_scan_details(
    id: UUID,
    db: Session = Depends(get_db),
    token: models.Token = Depends(auth.require_scope("scan:read"))
):
    db_scan = db.query(models.Scan).filter(models.Scan.id == id).first()
    if not db_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return db_scan

@router.get("/{id}/result.{format}")
def get_scan_result(
    id: UUID,
    format: str,
    db: Session = Depends(get_db),
    token: models.Token = Depends(auth.require_scope("scan:read"))
):
    if format not in ["json", "xml"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'xml'.")

    db_scan = db.query(models.Scan).filter(models.Scan.id == id).first()
    if not db_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if db_scan.status != 'succeeded':
        raise HTTPException(status_code=409, detail=f"Scan result not available. Status is '{db_scan.status}'.")

    if not db_scan.result_xml:
        raise HTTPException(status_code=404, detail="Scan result data not found in database.")

    if format == "xml":
        return Response(content=db_scan.result_xml, media_type="application/xml")
    
    if format == "json":
        data_dict = xmltodict.parse(db_scan.result_xml)
        return Response(content=json.dumps(data_dict), media_type="application/json")
