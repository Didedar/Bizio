# app/api/v1/clients.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app import crud, schemas

router = APIRouter(tags=["clients"])

# ============================================================================
# Client CRUD
# ============================================================================

@router.post("/", response_model=schemas.ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    client: schemas.ClientCreate,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new client for the specified tenant.
    
    Required fields:
    - name: str (client name)
    
    Optional fields:
    - email: Optional[EmailStr]
    - phone: Optional[str]
    - address: Optional[str]
    - metadata: Optional[dict]
    - extra_data: Optional[dict]
    """
    created = await crud.create_client(db, tenant_id, client)
    return created

@router.get("/", response_model=List[schemas.ClientRead])
async def list_clients(
    tenant_id: int = Query(..., description="Tenant ID"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    clients = await crud.list_clients(db, tenant_id, skip, limit)
    return clients

@router.get("/{client_id}", response_model=schemas.ClientRead)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    client = await crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.patch("/{client_id}", response_model=schemas.ClientRead)
async def update_client(
    client_id: int,
    client_update: schemas.ClientUpdate,
    db: AsyncSession = Depends(get_db)
):
    existing = await crud.get_client(db, client_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = client_update.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    updated = await crud.update_client(db, client_id, update_data)
    return updated

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    existing = await crud.get_client(db, client_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Client not found")

    await crud.delete_client(db, client_id)

