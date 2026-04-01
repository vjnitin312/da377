import requests
import os

# Folder to save the downloaded file
save_folder = "raw_data"
os.makedirs(save_folder, exist_ok=True)

# IMD subdivision-wise monthly rainfall data (1901–2015)
# Source: data.gov.in (official Indian government open data portal)
url = "https://data.gov.in/resource/subdivision-wise-monthly-seasonal-and-annual-rainfall-mm-1901-2015"

print("IMD data source URL noted.")
print("Action required: Visit the URL below and download the CSV manually.")
print()
print("  https://data.gov.in/catalog/rainfall-india")
print()
print("Steps:")
print("  1. Open the above link in your browser")
print("  2. Look for 'Subdivision Wise Rainfall Normal' dataset")
print("  3. Click Download → CSV")
print("  4. Save the file as:  raw_data/imd_rainfall.csv")