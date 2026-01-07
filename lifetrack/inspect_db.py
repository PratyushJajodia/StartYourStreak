import os
import sys
import django

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lt.settings')
django.setup()

from django.db import connection

def inspect():
    print(f"Database Engine: {connection.settings_dict['ENGINE']}")
    print(f"Database Name: {connection.settings_dict['NAME']}")
    
    with connection.cursor() as cursor:
        table_list = connection.introspection.get_table_list(cursor)
        table_names = [t.name for t in table_list]
        
        check_table(cursor, 'lifetrack_habit')
        check_table(cursor, 'lifetrack_achievement')

def check_table(cursor, table_name):
    table_list = connection.introspection.get_table_list(cursor)
    existing_tables = [t.name for t in table_list]
    
    if table_name in existing_tables:
        print(f"Table '{table_name}' exists.")
        columns = connection.introspection.get_table_description(cursor, table_name)
        col_names = [c.name for c in columns]
        print(f"  Columns: {sorted(col_names)}")
    else:
        print(f"Table '{table_name}' DOES NOT exist.")

if __name__ == "__main__":
    inspect()
