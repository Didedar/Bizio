# app/api/v1/auth.py
"""
Authentication endpoints: login, register, token refresh
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db import get_db
from app import crud, schemas, models
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_user
)

router = APIRouter(tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    tenant_name: Optional[str] = None  # If creating a new tenant
    tenant_code: Optional[str] = None  # Optional unique code for tenant


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user. Optionally create a new tenant for the user.
    """
    # Check if user already exists
    existing = await crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(payload.password)
    
    # Create user
    user = await crud.create_user(
        db,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hashed_password,
        role=models.UserRole.manager
    )
    
    # Create tenant if tenant_name provided
    if payload.tenant_name:
        try:
            # Convert empty string to None for tenant_code
            tenant_code = payload.tenant_code if payload.tenant_code and payload.tenant_code.strip() else None
            tenant = await crud.create_tenant(db, name=payload.tenant_name, code=tenant_code)
            # Associate user with tenant - refresh user first to load relationship
            await db.refresh(user, ["tenants"])
            user.tenants.append(tenant)
            await db.commit()
            await db.refresh(user, ["tenants"])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    else:
        # Refresh to ensure tenants list is loaded (even if empty)
        await db.refresh(user, ["tenants"])
    
    return user


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Username field should be email.
    """
    user = await crud.get_user_by_email(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Load tenants relationship
    await db.refresh(user, ["tenants"])
    
    # Get first tenant for user (if any)
    tenant_id = None
    if user.tenants:
        tenant_id = user.tenants[0].id
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "tenant_id": tenant_id,
            "role": user.role.value
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserRead)
async def read_users_me(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Get current user info with tenant information
    """
    # Load tenants relationship
    await db.refresh(current_user, ["tenants"])
    return current_user


class SetupDemoResponse(BaseModel):
    message: str
    tenant_id: int
    user_email: str
    user_password: str


@router.post("/setup-demo", response_model=SetupDemoResponse)
async def setup_demo(db: AsyncSession = Depends(get_db)):
    """
    Initialize the database with a demo tenant and admin user.
    This endpoint is idempotent - calling it multiple times will return the existing setup.
    
    Returns credentials for the demo account.
    """
    demo_email = "admin@demo.com"
    demo_password = "demo123456"
    demo_tenant_name = "Demo Company"
    demo_tenant_code = "DEMO"
    
    # Check if demo user already exists
    existing_user = await crud.get_user_by_email(db, demo_email)
    if existing_user:
        # Load tenants
        await db.refresh(existing_user, ["tenants"])
        tenant_id = existing_user.tenants[0].id if existing_user.tenants else 1
        return SetupDemoResponse(
            message="Demo account already exists. Use these credentials to login.",
            tenant_id=tenant_id,
            user_email=demo_email,
            user_password=demo_password
        )
    
    # Create demo tenant
    try:
        tenant = await crud.create_tenant(db, name=demo_tenant_name, code=demo_tenant_code)
    except ValueError:
        # Tenant might already exist
        from sqlalchemy import select
        result = await db.execute(
            select(models.Tenant).where(models.Tenant.code == demo_tenant_code)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            # Create without code
            tenant = await crud.create_tenant(db, name=demo_tenant_name, code=None)
    
    # Create demo user
    hashed_password = get_password_hash(demo_password)
    user = await crud.create_user(
        db,
        email=demo_email,
        full_name="Demo Admin",
        hashed_password=hashed_password,
        role=models.UserRole.admin
    )
    
    # Associate user with tenant
    await db.refresh(user, ["tenants"])
    user.tenants.append(tenant)
    await db.commit()
    
    return SetupDemoResponse(
        message="Demo account created successfully! Use these credentials to login.",
        tenant_id=tenant.id,
        user_email=demo_email,
        user_password=demo_password
    )

