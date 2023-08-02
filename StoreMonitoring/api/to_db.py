import csv
from db import connect_to_database

# Function to store CSV data into the database
def store_csv_data_into_database():
    conn = connect_to_database()
    with conn.cursor() as cur:
        # Code to read and insert CSV data into the 'restaurants' table
        # with open('./store_business_hours_data.csv', 'r') as csvfile:
        #     reader = csv.reader(csvfile)
        #     next(reader)  # Skip the header row
        #     for row in reader:
        #         cur.execute('''
        #             INSERT INTO restaurants (store_id, day, start_time_local, end_time_local)
        #             VALUES (%s, %s, %s, %s)
        #         ''', (row[0], int(row[1]), row[2], row[3]))

        # print("1. Completed")
        # Code to read and insert CSV data into the 'status_logs' table
        # with open('./store_status_data.csv', 'r') as csvfile:
        #     reader = csv.reader(csvfile)
        #     next(reader)  # Skip the header row
        #     for row in reader:
        #         cur.execute('''
        #             INSERT INTO status_logs (store_id, status, timestamp_utc)
        #             VALUES (%s, %s, %s)
        #         ''', (row[0], row[1], row[2]))

        # print("2. Completed")

        # Code to read and insert CSV data into the 'timezones' table
        with open('./store_timezones_data.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for row in reader:
                cur.execute('''
                    INSERT INTO timezones (store_id, timezone_str)
                    VALUES (%s, %s)
                ''', (row[0], row[1]))

        print("3. Completed")

    conn.commit()
    conn.close()


store_csv_data_into_database()