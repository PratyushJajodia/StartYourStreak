
import os
import sys
import threading
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.db import connection, close_old_connections
from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lt.settings')

# Get WSGI application to initialize Django
django_app = get_wsgi_application()

# Thread-safe flag to ensure migrations only run once
_migrations_run = False
_migrations_lock = threading.Lock()

def ensure_migrations():
    """Run database migrations if they haven't been run yet."""
    global _migrations_run
    
    # Fast path: if already run, skip
    if _migrations_run:
        return
    
    # Use lock to prevent race conditions in serverless environment
    with _migrations_lock:
        # Double-check after acquiring lock
        if _migrations_run:
            return
        
        try:
            print("Attempting to run migrations...")
            sys.stderr.write("MIGRATION: Starting database migrations...\n")
            
            # Close any stale connections
            close_old_connections()
            
            # Check if database is configured
            db_config = connection.settings_dict
            db_engine = db_config.get('ENGINE', '')
            db_name = db_config.get('NAME', '')
            
            print(f"Database engine: {db_engine}")
            print(f"Database name: {db_name}")
            
            if not db_name and 'sqlite' not in db_engine:
                raise ImproperlyConfigured(
                    "Database not properly configured. Check DATABASE_URL environment variable."
                )
            
            # Ensure database connection is established
            connection.ensure_connection()
            print(f"Database connection established: {db_engine}")
            sys.stderr.write(f"MIGRATION: Database connection established\n")
            
            # Run migrations for all apps, including Django's built-in apps
            # This will create django_session and other required tables
            call_command('migrate', verbosity=2, interactive=False, run_syncdb=False)
            print("Migrations completed successfully.")
            sys.stderr.write("MIGRATION: Completed successfully\n")
            
            _migrations_run = True
        except ImproperlyConfigured as e:
            # Database configuration error - this is critical
            error_msg = f"Database configuration error: {e}"
            print(error_msg)
            sys.stderr.write(f"CRITICAL: {error_msg}\n")
            raise
        except Exception as e:
            import traceback
            error_msg = f"Error running migrations: {e}"
            traceback_str = traceback.format_exc()
            print(error_msg)
            print(traceback_str)
            # Write to stderr so it appears in Vercel logs
            sys.stderr.write(f"MIGRATION ERROR: {error_msg}\n")
            sys.stderr.write(traceback_str)
            # Don't re-raise - allow the request to proceed so we can see other errors
            # But mark as failed so we don't keep trying
            _migrations_run = True  # Prevent infinite retry loop

class MigrationMiddleware:
    """WSGI middleware to ensure migrations run before handling requests."""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Run migrations on first request (lazy initialization)
        # This works better in serverless environments like Vercel
        try:
            ensure_migrations()
        except Exception as e:
            # If migrations fail, still try to handle the request
            # The error will show up in logs
            sys.stderr.write(f"MIGRATION MIDDLEWARE ERROR: {e}\n")
        
        return self.app(environ, start_response)

# Wrap the application with migration middleware
application = MigrationMiddleware(django_app)
app = application
