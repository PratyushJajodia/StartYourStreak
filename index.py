
import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lt.settings')

# Attempt to migrate on every boot (safe for small apps, ensures DB is ready)
try:
    print("Attempting to run migrations...")
    call_command('migrate')
    print("Migrations completed successfully.")
except Exception as e:
    print(f"Error running migrations: {e}")

application = get_wsgi_application()

app = application
