### Documentation for Store Uptime and Downtime Report Generation

#### Architecture Overview

The Store Uptime and Downtime Report Generation system is designed as a FastAPI web application that utilizes a cache to store generated reports with a Time-To-Live (TTL) of 1 hour. It follows a trigger and poll architecture to generate reports asynchronously and provides an API endpoint to fetch the generated reports.

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

#### CSV Output

The generated report data is saved as a CSV file named "report_output.csv" in the current working directory. The CSV file includes the following columns:

- store_id
- uptime_last_hour (in minutes)
- uptime_last_day (in hours)
- uptime_last_week (in hours)
- downtime_last_hour (in minutes)
- downtime_last_day (in hours)
- downtime_last_week (in hours)


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

### Database Reads

The application performs several database reads to gather the necessary data for generating the reports. These database reads are essential for the report generation process and are performed using the following functions:

1. **`get_all_store_ids`:** This function retrieves all unique `store_id` values from the `status_logs` table. The query selects distinct `store_id` values from the database, and the result is fetched and returned as a list of integers representing each store's unique identifier.

2. **`get_status_logs`:** Given a specific `store_id`, this function retrieves the `timestamp_utc` and `status` values from the `status_logs` table for that store. The records are ordered by `timestamp_utc` in ascending order, representing the chronological status logs for the store. The function returns the data as a list of dictionaries, where each dictionary contains the `timestamp_utc` and `status` for each log entry.

3. **`get_business_hours`:** For a particular `store_id`, this function fetches the `day`, `start_time_local`, and `end_time_local` values from the `restaurants` table. These values represent the business hours for the store on each day of the week. The function returns the data as a list of tuples, where each tuple contains the `day`, `start_time_local`, and `end_time_local` values for a specific day.

4. **`get_store_timezone`:** This function retrieves the timezone information for a specific `store_id` from the `timezones` table. If the timezone information is available, it returns the `timezone_str`. Otherwise, it assumes the timezone as "America/Chicago." The timezone information is essential for converting timestamps between UTC and the store's local timezone.

### CSV Output

The application generates the final report data as a dictionary containing uptime and downtime information for each store. However, as CSV format is commonly used for data storage and sharing, there is a need to save the report data in a CSV file for further analysis or distribution. To achieve this, the application can use the `pandas` library, which provides an easy-to-use interface for working with tabular data, including CSV files.

To save the report data as a CSV file, the following steps can be taken:

1. Convert the list of dictionaries (report data) into a pandas DataFrame.
2. Use the pandas `to_csv` function to save the DataFrame as a CSV file.

Example code to save the report data as a CSV file:

```python
import pandas as pd

# Assuming report_data contains the generated report data as a list of dictionaries
report_data = [
    {
        "store_id": 1,
        "uptime_last_hour": 50,
        "uptime_last_day": 1200,
        "downtime_last_hour": 10,
        "downtime_last_day": 240,
    },
    # More store data...
]

# Convert the report_data list of dictionaries to a pandas DataFrame
report_df = pd.DataFrame(report_data)

# Save the DataFrame as a CSV file
report_df.to_csv("report.csv", index=False)
```

In this example, the `report_data` list of dictionaries is converted to a DataFrame using `pd.DataFrame(report_data)`. The `to_csv` function is then used to save the DataFrame as a CSV file named "report.csv." The `index=False` parameter is used to exclude the row numbers (index) from the CSV file.

By following these steps, the application can generate the report data and save it in a CSV file for further use or analysis. The CSV file will contain a row for each store, with columns representing store_id, uptime in the last hour, uptime in the last day, downtime in the last hour, and downtime in the last day.

#### Conclusion

The Store Uptime and Downtime Report Generation system efficiently calculates and stores the uptime and downtime for multiple store_ids using interpolation methods and pandas DataFrames. The use of background tasks and a cache with TTL ensures a smooth and asynchronous report generation process. The output is provided to the user in a clean and organized CSV format for further analysis and insights.
