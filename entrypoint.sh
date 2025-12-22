#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.

echo "Starting entrypoint script..."

# 1. Check database connection
echo "Checking database connection..."
# Use python -u for unbuffered output to see logs immediately
# Execute check_db as a module (-m) for reliable imports within the package
if python -u -m app.check_db; then
    echo "Database connection verified."
else
    echo "Database connection check failed. Exiting." >&2
    exit 1
fi

# 2. Run Alembic migrations
echo "Running database migrations..."
# Run alembic from the /app directory where alembic.ini is located
# Ensure PYTHONPATH is set so alembic can find backend modules
if alembic upgrade head; then
    echo "Database migrations completed successfully."
else
    echo "Database migrations failed. Check logs for details. Exiting." >&2
    exit 1
fi

# 3. Start the application
echo "Starting Uvicorn server..."
# Use exec to replace the shell process with the Uvicorn process
# This ensures signals (like SIGTERM) are handled correctly by Uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8000