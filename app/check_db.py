import os
import sys
import time
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine.url import make_url

if "/app" not in sys.path:
    sys.path.insert(0, "/app")

MAX_RETRIES = int(os.environ.get("DB_CONN_MAX_RETRIES", 10))
RETRY_DELAY = int(os.environ.get("DB_CONN_RETRY_DELAY", 5))  # seconds


def check_db_connection():
    try:
        from app.database import engine
        from app.config import settings

        def get_database_url():
            return settings.DATABASE_URL

        # Check if engine was actually initialized in db_config
        if engine is None:
            print(
                "Error: Database engine was not initialized. Check db_config.py logs.",
                file=sys.stderr,
            )
            return False

        database_url_str = get_database_url()
        if not database_url_str:
            print("Error: DATABASE_URL not set or empty.", file=sys.stderr)
            return False

        try:
            db_url_parsed = make_url(database_url_str)
            print(
                f"Attempting to connect to: {db_url_parsed.render_as_string(hide_password=True)}"
            )
        except Exception:
            print("Attempting to connect (URL parsing failed).")

        for i in range(MAX_RETRIES):
            try:
                with engine.begin() as conn:
                    conn.execute(text("SELECT 1"))
                print("Database connection successful.")
                return True
            except OperationalError as e:
                print(f"Attempt {i + 1}/{MAX_RETRIES} failed.")
                error_str = str(e).lower()
                if "connection refused" in error_str:
                    print("   Error: Connection refused. Check database server.")
                elif "password authentication failed" in error_str:
                    print("   Error: Authentication failed. Check credentials.")
                elif "does not exist" in error_str:
                    print(f"   Error: Database '{db_url_parsed.database}' not found.")
                elif "timeout" in error_str:
                    print("   Error: Connection timed out. Check network.")
                else:
                    print(f"   Error: {str(e).splitlines()[0]}")

                if i < MAX_RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print("Max retries reached.")
                    return False
            except Exception as e:
                print(f"Attempt {i + 1}/{MAX_RETRIES} failed: {e}", file=sys.stderr)
                if i < MAX_RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print("Max retries reached.")
                    return False

    except ImportError:
        # This catch might indicate issues finding db_config OR issues *within* db_config during its import
        print(
            "Error: Could not import 'app.database' or its dependencies.",
            file=sys.stderr,
        )
        import traceback

        traceback.print_exc(file=sys.stderr)  # Add traceback for better diagnosis
        return False
    except AttributeError:
        # This might happen if db_config imported but 'engine' or 'get_database_url' is missing/None
        print(
            "Error: Could not access expected attributes (engine/get_database_url) from 'app.database'.",
            file=sys.stderr,
        )
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    result = check_db_connection()
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
