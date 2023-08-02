### Documentation for Store Uptime and Downtime Report Generation

#### Architecture Overview

The Store Uptime and Downtime Report Generation system is designed as a FastAPI web application that utilizes a cache to store generated reports with a Time-To-Live (TTL) of 1 hour. It follows a trigger and poll architecture to generate reports asynchronously and provides an API endpoint to fetch the generated reports.
### Endpoints

1. **Home**

   - URL: `/`
   - Method: GET
   - Description: This endpoint returns a simple "Hello World" message, indicating that the API is running.

2. **Trigger Report**

   - URL: `/trigger_report`
   - Method: POST
   - Description: This endpoint triggers the generation of a new report. It runs the report generation process in the background and returns a unique report_id that can be used to retrieve the report later.

   - Request Body: None
   - Response:
     - Status 200 OK

       ```
       {
           "report_id": "unique_report_id"
       }
       ```

3. **Get Report**

   - URL: `/get_report`
   - Method: GET
   - Description: This endpoint allows users to retrieve the status and data of a generated report using the report_id obtained from the trigger_report endpoint.

   - Request Parameters:
     - `report_id` (str): The unique report_id obtained from the trigger_report endpoint.

   - Response:
     - Status 200 OK (Report still being generated)

       ```
       {
           "status": "Running"
       }
       ```

     - Status 200 OK (Report generation complete)

       ```
       {
           "status": "Complete",
           "data": [
               {
                   "store_id": 1,
                   "uptime_last_hour": 50,
                   "uptime_last_day": 1200,
                   "uptime_last_week": 5000,
                   "downtime_last_hour": 10,
                   "downtime_last_day": 240,
                   "downtime_last_week": 1000
               },
               // More store data...
           ]
       }
       ```

### Database Data Extraction

The API uses the following functions to extract data from the database:

1. **get_all_store_ids**

   - Description: This function retrieves all unique store_ids from the "status_logs" table in the database.

2. **get_status_logs**

   - Description: This function retrieves the "timestamp_utc" and "status" data for a specific store_id from the "status_logs" table, ordered by "timestamp_utc" in ascending order.

3. **get_business_hours**

   - Description: This function retrieves the "day", "start_time_local", and "end_time_local" data for a specific store_id from the "restaurants" table in the database.

4. **get_store_timezone**

   - Description: This function retrieves the timezone information for a specific store_id from the "timezones" table in the database. If no timezone information is found, it assumes the timezone as "America/Chicago."

### Uptime and Downtime Calculation

The `calculate_uptime_downtime` function calculates the uptime and downtime for a specific store using interpolation techniques. The function performs the following steps:

1. Retrieves the status logs and business hours data for the store using the previously mentioned database extraction functions.

2. Converts the retrieved data into pandas DataFrames for efficient processing.

3. Determines the store's timezone and converts the timestamp data to the local timezone.

4. Merges the status logs with the nearest business hours based on the day of the week and time of the day using pandas' `merge_asof` function.

5. Interpolates missing status values within specific time intervals (last hour, last day, last week) to account for any gaps in the data.

6. Calculates the uptime and downtime in minutes/hours based on the interpolated status logs.

### CSV Output

The API saves the generated report data to a CSV file named "report-reportID.csv" with the following columns:

- store_id: The unique identifier for each store.
- uptime_last_hour: The total uptime in minutes for the last hour.
- uptime_last_day: The total uptime in hours for the last day.
- uptime_last_week: The total uptime in hours for the last week.
- downtime_last_hour: The total downtime in minutes for the last hour.
- downtime_last_day: The total downtime in hours for the last day.
- downtime_last_week: The total downtime in hours for the last week.

The CSV file is generated upon completion of the report generation and will include data for all store_ids processed during the report generation. Each row in the CSV file represents the report data for a specific store.

#### Components

1. **FastAPI Web Application:** The core of the system is built using the FastAPI web framework. It provides API endpoints for triggering report generation and retrieving the generated reports.

2. **TTLCache:** The application uses the `cachetools` library to implement a TTLCache with a maximum size of 100 and a time-to-live (TTL) of 1 hour (3600 seconds). This cache is used to store the generated reports temporarily.

3. **Database Connection:** The system connects to a postgresql database to fetch data required for report generation. It includes functions to retrieve status logs, business hours, and timezones for specific store_ids.

4. **Background Tasks:** The `BackgroundTasks` class provided by FastAPI is used to run the report generation process asynchronously in the background. When the report generation is triggered, the system starts calculating the uptime and downtime for each store_id, and the results are stored in the cache.

5. **Datetime and Timezone Handling:** The `datetime` module is used to handle timestamps and time intervals. The `pytz` library is utilized for timezone handling.

6. **Pandas DataFrame:** The `pandas` library is used to store and manipulate the data in DataFrames, making it easier to perform calculations and output the final results in CSV format.

#### Trigger and Poll Architecture

1. When a client sends a POST request to the "/trigger_report" API endpoint, the server generates a unique report_id (UUID) and starts the report generation process asynchronously in the background using `BackgroundTasks`.

2. The server immediately responds with the report_id, indicating that the report generation has been triggered.

3. The background task (`generate_report`) iterates over all store_ids retrieved from the database and calculates the uptime and downtime for each store using interpolation methods. The results are stored in the `report_cache` with the report_id as the key.

4. Clients can request the status of the report or the CSV by sending a GET request to the "/get_report" API endpoint with the report_id. If the report is still being generated, the server responds with "Running." Once the report is complete and available in the cache, the server responds with "Complete" along with the report data.

#### Report Generation Logic

1. For each store_id, the system retrieves status logs and business hours from the database.

2. The status logs and business hours are converted into pandas DataFrames for easy manipulation and merging.

3. The system then merges the status logs and business hours on the nearest day of the week and time of the day to calculate uptime and downtime. This is achieved using `pd.merge_asof`.

4. The system calculates uptime and downtime for the last hour, last day, and last week based on the current timestamp.

5. For each time interval (hour, day, and week), the system creates a DataFrame with all the timestamps within that interval and interpolates the status logs to get the status (active/inactive) for each minute/hour within the interval.

6. Finally, the system converts the uptime and downtime from minutes to hours and stores the results in a dictionary with the store_id as the key.

### Profiler Data Table

Below is the profiler data table generated for the `generate_report` function during execution. It shows the number of hits, total time taken, time per hit, and the percentage of total time spent in each line of the function.

```
Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   261                                           @profile
   262                                           def generate_report(report_id: str):
   263                                               # Get all store_ids from the database
   264         1    4136870.0 4136870.0      1.0      store_ids = get_all_store_ids()
   265                                               # print(len(store_ids))
   266         1      61265.0  61265.0      0.0      current_timestamp=datetime.strptime('2023-01-25 14:04:00.152582 UTC','%Y-%m-%d %H:%M:%S.%f %Z')
   267                                               # Create a dictionary to store individual reports for each store_id
   268         1         12.0     12.0      0.0      cnt=0
   269         1          4.0      4.0      0.0      report_data = []
   270         1        562.0    562.0      0.0      report_cache[report_id] = report_data
   271                                               # Iterate over each store_id and calculate the report
   272       200       5187.0     25.9      0.0      for store_id in store_ids[:200]:
   273                                                   # Calculate uptime and downtime for the store
   274       200  412129136.0 2060645.7     98.8          uptime_downtime = calculate_uptime_downtime(store_id, current_timestamp)
   275                                                   # print(uptime_downtime)
   276                                                   # Store the report data for the store_id in the dictionary
   277       200       2341.0     11.7      0.0          report_data.append(uptime_downtime)
   278       200       1449.0      7.2      0.0          cnt+=1
   279       200     967250.0   4836.2      0.2          print(cnt)
   280
   281                                               print_stats()
   282                                               # Store the entire dictionary of reports in the cache with the report_id as the key
   283                                               report_cache[report_id] = report_data
```

#### Interpretation

- Line 264: Fetching store_ids from the database took approximately 4.1 seconds (total time). This operation was executed only once.
- Line 266: Initializing the `current_timestamp` variable took approximately 61.3 milliseconds (total time). This operation was executed only once.
- Line 270: Creating an empty list `report_data` and storing it in the `report_cache` took approximately 562 microseconds (total time). This operation was executed only once.
- Line 272-283: The loop to calculate uptime and downtime for each store_id and store the results in `report_data` took the most time. It spent approximately 412 seconds (98.8% of the total time) inside the `calculate_uptime_downtime` function for each store_id. Additionally, printing the progress (`cnt`) during the loop took approximately 967 milliseconds (0.2% of the total time) for each store_id.

### Conclusion

The Store Uptime and Downtime Report Generation system efficiently calculates and stores the uptime and downtime for multiple store_ids using interpolation methods and pandas DataFrames. The use of background tasks and a cache with TTL ensures a smooth and asynchronous report generation process. The output is provided to the user in a clean and organized CSV format for further analysis and insights.
