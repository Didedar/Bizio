#!/usr/bin/env bash
# run_local.sh
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"
uvicorn app.main:app --reload --port 8000
