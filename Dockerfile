# Stage 1: Build frontend assets
FROM node:20-alpine AS build-frontend
WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install --frozen-lockfile

# Copy the rest of the frontend code
COPY frontend/ ./
ENV VITE_BACKEND_URL=
# Build the frontend
RUN npm run build

# Stage 2: Setup backend and serve frontend
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONPATH=/app

# Install backend dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code, alembic config, and helper scripts
COPY . /app/
COPY alembic.ini /app/
COPY alembic /app/alembic
COPY entrypoint.sh /app/

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Copy built frontend assets from the build stage
COPY --from=build-frontend /app/frontend/dist /app/static_root

# Expose the port the app runs on
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]