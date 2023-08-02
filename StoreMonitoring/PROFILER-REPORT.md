
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

