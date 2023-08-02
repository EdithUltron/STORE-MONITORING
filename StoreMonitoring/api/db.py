
import psycopg2
from dotenv.main import load_dotenv

# Database connection details
DB_HOST = "192.168.56.1"
DB_NAME = "loop"
DB_USER = "postgres"
DB_PASSWORD = "a"

# Connect to the database
def connect_to_database():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Function to create tables in the database
def create_tables():
    conn = connect_to_database()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS restaurants (
                store_id BIGINT,
                day INT,
                start_time_local TIME,
                end_time_local TIME
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS status_logs (
                store_id BIGINT,
                status TEXT,
                timestamp_utc TIMESTAMP
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS timezones (
                store_id BIGINT,
                timezone_str TEXT
            )
        ''')
    conn.commit()
    conn.close()


create_tables()