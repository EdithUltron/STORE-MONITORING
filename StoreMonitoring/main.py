from cachetools import TTLCache
from fastapi import FastAPI, BackgroundTasks, HTTPException
from datetime import datetime, timedelta
from api.db import connect_to_database
import pytz
import uuid
import pandas as pd
import uvicorn
from line_profiler import LineProfiler
from fastapi.middleware.cors import CORSMiddleware  # Import the CORSMiddleware

app = FastAPI()

profiler = LineProfiler()

SLICE_NUM=500


origins = [
    "http://localhost:3000",
]

# Add the CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import FileResponse

@app.get("/download_report", tags=["report"])
async def download_report(report_id: str):
    file_path = f"report-{report_id}.csv"  # Assuming the report is saved with the report_id as the file name
    return FileResponse(file_path, filename="report.csv")


def profile(func):
    def inner(*args, **kwargs):
        profiler.add_function(func)
        profiler.enable_by_count()
        return func(*args, **kwargs)
    return inner

# Initialize a cache to store the reports with a TTL of 1 hour (3600 seconds)
report_cache = TTLCache(maxsize=100, ttl=3600)

def print_stats():
    profiler.print_stats()

@app.get("/")
def home():
    # print(store_status_data)
    return ({'Hello World'})

# Function to get all store_ids from the database
def get_all_store_ids():
    conn = connect_to_database()
    with conn.cursor() as cur:
        cur.execute('''
            SELECT DISTINCT store_id
            FROM status_logs
        ''')
        store_ids = cur.fetchall()
    conn.close()

    return [store_id for (store_id,) in store_ids]


# Function to get status logs for a specific store from the database
def get_status_logs(store_id: int):
    conn = connect_to_database()
    with conn.cursor() as cur:
        cur.execute('''
            SELECT timestamp_utc, status
            FROM status_logs
            WHERE store_id = %s
            ORDER BY timestamp_utc ASC
        ''', (store_id,))
        status_logs = cur.fetchall()
    conn.close()

    return [{"timestamp_utc": ts, "status": status} for ts, status in status_logs]

# Function to get business hours for a specific store from the database
def get_business_hours(store_id: int):
    conn = connect_to_database()
    with conn.cursor() as cur:
        cur.execute('''
            SELECT day, start_time_local, end_time_local
            FROM restaurants
            WHERE store_id = %s
        ''', (store_id,))
        business_hours = cur.fetchall()
    conn.close()

    return business_hours

# Function to get timezone for a specific store from the database
def get_store_timezone(store_id: int):
    conn = connect_to_database()
    with conn.cursor() as cur:
        cur.execute('''
            SELECT timezone_str
            FROM timezones
            WHERE store_id = %s
        ''', (store_id,))
        timezone_info = cur.fetchone()
    conn.close()

    return timezone_info[0] if timezone_info else "America/Chicago"  # Assume America/Chicago if timezone missing



# Function to calculate uptime and downtime for a store using interpolation method
@profile
def calculate_uptime_downtime(store_id: int, current_timestamp: datetime):
    # Get status logs and business hours for the store
    status_logs = get_status_logs(store_id)
    business_hours = get_business_hours(store_id)

    # Get the store's timezone
    store_timezone = get_store_timezone(store_id)
    local_timezone = pytz.timezone(store_timezone)


    # Convert status logs and business hours to pandas DataFrames
    status_df = pd.DataFrame(status_logs)
    status_df["timestamp_utc"] = pd.to_datetime(status_df["timestamp_utc"])

    status_df["timestamp_local"] = status_df["timestamp_utc"].dt.tz_localize(pytz.UTC).dt.tz_convert(local_timezone)

    business_hours_df = pd.DataFrame(business_hours, columns=["day", "start_time_local", "end_time_local"])
    business_hours_df["day"] = business_hours_df["day"].astype('int64')  
    
    if business_hours_df.empty:
            # If no business hours data, assume the store is open 24/7
        business_hours_df = pd.DataFrame({"day": range(7), "start_time_local": current_timestamp.replace(hour=0, minute=0, second=0, microsecond=0),
                                            "end_time_local": current_timestamp.replace(hour=23, minute=59, second=59, microsecond=999999)})
    else:
        # Convert 'datetime.time' to full datetime objects with the date from the current timestamp
        business_hours_df["start_time_local"] = business_hours_df.apply(
            lambda row: datetime.combine(current_timestamp.date(), row["start_time_local"]),
            axis=1
        )
        business_hours_df["end_time_local"] = business_hours_df.apply(
            lambda row: datetime.combine(current_timestamp.date(), row["end_time_local"]),
            axis=1
        )
    
    business_hours_df["start_time_local"] = pd.to_datetime(business_hours_df["start_time_local"]).dt.tz_localize(local_timezone)
    business_hours_df["end_time_local"] = pd.to_datetime(business_hours_df["end_time_local"]).dt.tz_localize(local_timezone)


    # Add a new column for the day of the week in status_df
    status_df["day"] = status_df["timestamp_local"].dt.dayofweek.astype('int64')

    # Merge status_df and business_hours_df on the nearest day of the week and time of the day
    merged_df = pd.merge_asof(status_df.sort_values("timestamp_local"),
                              business_hours_df.sort_values("start_time_local"),
                              left_on="timestamp_local",
                              right_on="start_time_local",
                              by="day",
                              direction="nearest")

    # Drop unnecessary columns from the merged DataFrame
    merged_df = merged_df.drop(columns=["day", "start_time_local", "end_time_local"])

    # Sort the merged DataFrame by timestamp_local
    merged_df = merged_df.sort_values("timestamp_local")

    current_timestamp=current_timestamp.replace(tzinfo=local_timezone)

    # Calculate the timestamp for one hour before the current timestamp
    one_hour_ago = current_timestamp - timedelta(minutes=59)

    # Calculate the timestamp for one day before the current timestamp
    one_day_ago = current_timestamp - timedelta(hours=23)

    # Calculate the timestamp for one week before the current timestamp
    one_week_ago = current_timestamp - timedelta(hours=167)

     # Create a DataFrame with all the timestamps within the last hour
    all_timestamps_last_hour = pd.date_range(start=one_hour_ago, end=current_timestamp, freq="1min")

    # Interpolate and sum up uptime and downtime for each minute within the last hour
    interpolated_status_logs_last_hour = merged_df.loc[
        (merged_df["timestamp_local"] >= one_hour_ago) & (merged_df["timestamp_local"] <= current_timestamp)
    ]


    # Merge the all_timestamps_last_hour with interpolated_status_logs_last_hour on timestamp_local
    interpolated_status_logs_last_hour = pd.merge_asof(
        pd.DataFrame({"timestamp_local": all_timestamps_last_hour}),
        interpolated_status_logs_last_hour,
        on="timestamp_local",
        direction="nearest"
    )

    # Interpolate missing values in the status column
    interpolated_status_logs_last_hour["status"].interpolate(method="pad", inplace=True)
    interpolated_status_logs_last_hour["status"].fillna("inactive", inplace=True)


    all_timestamps_last_day = pd.date_range(start=one_day_ago, end=current_timestamp, freq="H")
    
    # Interpolate and sum up uptime and downtime for each hour within the last day
    interpolated_status_logs_last_day = merged_df.loc[
        (merged_df["timestamp_local"] >= one_day_ago) & (merged_df["timestamp_local"] <= current_timestamp)
    ]


    # Merge the all_timestamps_last_hour with interpolated_status_logs_last_hour on timestamp_local
    interpolated_status_logs_last_day = pd.merge_asof(
        pd.DataFrame({"timestamp_local": all_timestamps_last_day}),
        interpolated_status_logs_last_day,
        on="timestamp_local",
        direction="nearest"
    )

    # Interpolate missing values in the status column
    interpolated_status_logs_last_day["status"].interpolate(method="pad", inplace=True)
    interpolated_status_logs_last_day["status"].fillna("inactive", inplace=True)


    all_timestamps_last_week= pd.date_range(start=one_week_ago, end=current_timestamp, freq="H")

    # Interpolate and sum up uptime and downtime for each day within the last week
    interpolated_status_logs_last_week = merged_df.loc[
        (merged_df["timestamp_local"] >= one_week_ago) & (merged_df["timestamp_local"] <= current_timestamp)
    ]

    
    # Merge the all_timestamps_last_hour with interpolated_status_logs_last_hour on timestamp_local
    interpolated_status_logs_last_week = pd.merge_asof(
        pd.DataFrame({"timestamp_local": all_timestamps_last_week}),
        interpolated_status_logs_last_week,
        on="timestamp_local",
        direction="nearest"
    )

    # Interpolate missing values in the status column
    interpolated_status_logs_last_week["status"].interpolate(method="pad", inplace=True)
    interpolated_status_logs_last_week["status"].fillna("inactive", inplace=True)

    # Convert uptime and downtime from minutes to hours
    uptime_last_hour =   len([i for i in interpolated_status_logs_last_hour["status"]=="active" if i==True])
    downtime_last_hour = len([i for i in interpolated_status_logs_last_hour["status"]=="inactive" if i==True])
    uptime_last_day = len([i for i in interpolated_status_logs_last_day["status"]=="active" if i==True])
    uptime_last_week = len([i for i in interpolated_status_logs_last_week["status"]=="active" if i==True])
    downtime_last_day = len([i for i in interpolated_status_logs_last_day["status"]=="inactive" if i==True])
    downtime_last_week = len([i for i in interpolated_status_logs_last_week["status"]=="inactive" if i==True])

    return {
        "store_id": store_id,
        "uptime_last_hour": uptime_last_hour,
        "uptime_last_day": uptime_last_day,
        "uptime_last_week": uptime_last_week,
        "downtime_last_hour": downtime_last_hour,
        "downtime_last_day": downtime_last_day,
        "downtime_last_week": downtime_last_week
    }

# API endpoint to trigger report generation
@app.post("/trigger_report", tags=["report"])
async def trigger_report(background_tasks: BackgroundTasks):

    if len(list(report_cache.keys()))> 0:
        # print(list(report_cache.keys()))
        return {"report_id":list(report_cache.keys())[0]}
    
    # Generate a random report_id (for simplicity, we use a timestamp here)
    report_id = str(uuid.uuid4())

    # Run the report generation process in the background
    background_tasks.add_task(generate_report, report_id,background_tasks)


    # Return the report_id
    return {"report_id": report_id}





@profile
def calculate_uptime_downtime_task(store_id:int, current_timestamp:datetime,report_id:int):
    # ... (rest of the code for calculating uptime and downtime remains unchanged)

    # Calculate uptime and downtime for the store
    uptime_downtime = calculate_uptime_downtime(store_id, current_timestamp)

    # Store the report data in the PostgreSQL database
    # store_report_data(uptime_downtime)

    report_cache[report_id].append(uptime_downtime)






# Background function to generate the report for all store_ids
@profile
def generate_report(report_id: str,background_tasks: BackgroundTasks):
    # Get all store_ids from the database
    store_ids = get_all_store_ids()
    # print(len(store_ids))
    current_timestamp=datetime.strptime('2023-01-25 14:04:00.152582 UTC','%Y-%m-%d %H:%M:%S.%f %Z')
    # Create a dictionary to store individual reports for each store_id
    cnt=0
    report_data = []
    report_cache[report_id] = report_data
    # Iterate over each store_id and calculate the report
    for store_id in store_ids[:SLICE_NUM]:
        # Calculate uptime and downtime for the store
        background_tasks.add_task(calculate_uptime_downtime_task,store_id, current_timestamp,report_id)

    print_stats()
    # Store the entire dictionary of reports in the cache with the report_id as the key
    report_cache[report_id] = report_data



# API endpoint to get the status of the report or the CSV
@app.get("/get_report", tags=["report"])
async def get_report(report_id: str):
    # store_ids = get_all_store_ids()
    # Check if the report_id exists in the cache
    if report_id in report_cache:
        # If the report is still being generated, return "Running"
        # print(report_cache[report_id])
        if len(report_cache[report_id]) < SLICE_NUM:
            return {"status": "Running"}

        # If the report is complete, return "Complete" along with the entire dictionary of reports
        report_data = report_cache[report_id]
        report_cache.clear()
        # Convert the report_data list of dictionaries to a pandas DataFrame
        report_df = pd.DataFrame(report_data)

        # Define the order of columns in the CSV file
        csv_columns = ["store_id", "uptime_last_hour", "uptime_last_day", "uptime_last_week",
                    "downtime_last_hour", "downtime_last_day", "downtime_last_week"]

        # Save the DataFrame as a CSV file with the specified column order
        file_path = f"report-{report_id}.csv"
        report_df.to_csv(file_path, columns=csv_columns, index=False)
        
        return {"status": "Complete", "data": report_data}

    # If the report_id is not found in the cache, return "Invalid report_id"
    raise HTTPException(status_code=404, detail="Invalid report_id")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
