# Railway Deployment Guide for Bizio

This guide walks you through deploying the full stack (Frontend + Backend + Database) to Railway.

## Prerequisites
- A [Railway](https://railway.app/) account.
- The project code pushed to a GitHub repository.

## Step 1: Create a New Project
1. Go to your Railway Dashboard.
2. Click **New Project** > **Provision PostgreSQL**.
3. This creates a new project with a database.

## Step 2: Add Redis (Optional but Recommended)
1. Click **New** > **Database** > **Redis**.
2. This is needed for Celery background tasks.

## Step 3: Deploy Backend
1. Click **New** > **GitHub Repo**.
2. Select your repository.
3. Click on the new service card to configure it.
4. Go to **Settings** > **Root Directory** and set it to `/backend`.
5. Go to **Variables** and add these:
    - `DATABASE_URL`: Use the value from the PostgreSQL service (tab "Connect" -> "Variables"). **Important**: Replace `postgresql://` with `postgresql+asyncpg://` if your code requires async driver, OR rely on your code's URL fixer.
    - `REDIS_URL`: Use the value from Redis service.
    - `SECRET_KEY`: Generate a random string.
    - `CORS_ORIGINS`: `*` (or your frontend domain later).
    - `PORT`: Railway sets this automatically. Our `Dockerfile` is updated to respect it.
6. The service should build and deploy. 

## Step 4: Deploy Frontend
1. Click **New** > **GitHub Repo** (select the same repo again).
2. Click on the new service card.
3. Go to **Settings**:
    - **Root Directory**: Set to `/frontend`.
    - **Build Command**: `npm run build`
    - **Start Command**: `npm start` (This runs `npx serve -s dist -l $PORT`)
4. Go to **Variables**:
    - `VITE_API_BASE_URL`: The URL of your **Backend Service** (e.g., `https://backend-production.up.railway.app/api/v1`). 
      *Note: You get this URL from the Backend service's "Settings" > "Domains".*
5. The service will build. Once deployed, open the public URL to see your app.

## Step 5: Verify Connection
1. Open the Frontend URL.
2. Try to log in or see the dashboard.
3. If it fails, check the browser console (Network tab) to see if requests are going to the correct Backend URL.
4. Check Backend logs in Railway for any errors.

## Troubleshooting
- **Build Failures**: Check the "Build Logs" tab.
- **"Could not open requirements file" / "Pip install failed"**: 
    - This means Railway is trying to build from the **Root** directory instead of `/backend`.
    - Go to **Settings** > **Root Directory** and ensure it is set to `/backend`.
    - If it is already set, try removing the service and adding it again, making sure to set the Root Directory *before* the first deployment completes if possible, or trigger a Redeploy.
- **"App check failed"**: Ensure `PORT` is being listened to. (We configured `uvicorn` to listen on `$PORT`).
- **CORS Errors**: Ensure Backend `CORS_ORIGINS` includes your Frontend URL or `*`.
