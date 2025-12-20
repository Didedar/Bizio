# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db import get_db
from app import crud, schemas, models
from app.core.security import get_password_hash

router = APIRouter(tags=["users"])

@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Hash password if provided
    hashed_password = None
    if payload.password:
        hashed_password = get_password_hash(payload.password)
    
    # Convert role string to enum if provided
    role = models.UserRole.manager
    if payload.role:
        try:
            role = models.UserRole(payload.role)
        except ValueError:
            role = models.UserRole.manager
    
    u = await crud.create_user(db, email=payload.email, full_name=payload.full_name, hashed_password=hashed_password, role=role)
    
    # Eagerly load tenants relationship to avoid lazy loading issues
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    stmt = (
        select(models.User)
        .where(models.User.id == u.id)
        .options(selectinload(models.User.tenants))
    )
    result = await db.execute(stmt)
    return result.scalar_one()

@router.get("/", response_model=List[schemas.UserRead])
async def list_users(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    # Simple implementation - list all users
    # In production, you might want to filter by tenant or add authentication
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models
    stmt = (
        select(models.User)
        .where(models.User.is_active == True)
        .options(selectinload(models.User.tenants))
        .offset(skip)
        .limit(limit)
    )
    q = await db.execute(stmt)
    return q.scalars().all()

@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models
    
    stmt = (
        select(models.User)
        .where(models.User.id == user_id)
        .options(selectinload(models.User.tenants))
    )
    q = await db.execute(stmt)
    u = q.scalar_one_or_none()
    
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u
