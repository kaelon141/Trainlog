import csv
import io
import sqlite3
import zipfile
from datetime import datetime, timedelta

import requests


def fill_missing_rates(db_path, table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Identify columns with NULL values
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]

    for col in columns:
        # Fill NULL values where a previous value exists
        update_query_with_previous = f"""
        UPDATE {table_name}
        SET {col} = (
            SELECT {col}
            FROM (
                SELECT {col}, ROWID
                FROM {table_name}
                WHERE {col} IS NOT NULL
            ) AS valid_values
            WHERE valid_values.ROWID < {table_name}.ROWID
            ORDER BY valid_values.ROWID DESC
            LIMIT 1
        )
        WHERE {col} IS NULL AND EXISTS (
            SELECT 1
            FROM {table_name} as prev
            WHERE prev.{col} IS NOT NULL AND prev.ROWID < {table_name}.ROWID
        );
        """
        cursor.execute(update_query_with_previous)

        # Fill remaining NULL values using the oldest non-null value if no previous values exist
        update_query_with_oldest = f"""
        UPDATE {table_name}
        SET {col} = (
            SELECT {col} FROM {table_name} WHERE {col} IS NOT NULL ORDER BY ROWID ASC LIMIT 1
        )
        WHERE {col} IS NULL;
        """
        cursor.execute(update_query_with_oldest)

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def get_complete_days(db_path):
    """
    Fetches a list of dates from the exchanges table where the
    number of records for each date equals 342.

    Parameters:
    - db_path (str): The path to the SQLite database file.

    Returns:
    - complete_days (list of str): A list of dates (as strings) matching the criteria.
    """
    # Connect to the SQLite database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # SQL query to select rate dates having exactly 342 records
    query = """
        SELECT DISTINCT(rate_date)
        FROM exchanges
        ORDER BY rate_date DESC
    """

    # Execute the query
    cursor.execute(query)

    # Fetch all results
    results = cursor.fetchall()

    # Close the connection to the database
    connection.close()

    # Extract dates from the results
    # Each item in results is a tuple, where the first element is the rate_date
    complete_days = [result[0] for result in results]

    return complete_days


def download_and_unzip(url):
    """
    Downloads a ZIP file from a URL and unzips it in memory.

    Parameters:
    - url (str): The URL of the ZIP file to download.

    Returns:
    - file_contents (dict): A dictionary with file names as keys and their contents as values.
    """
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Use BytesIO to create a file-like object in memory from the downloaded bytes
        zip_in_memory = io.BytesIO(response.content)

        # Use the zipfile module to read the zip file from the in-memory file-like object
        with zipfile.ZipFile(zip_in_memory, "r") as zip_ref:
            # Get the list of file names contained in the ZIP
            file_names = zip_ref.namelist()

            # Select the first file in the list (or apply any other selection criteria you prefer)
            if file_names:  # Ensure there is at least one file in the ZIP
                file_name = file_names[0]
                file_content = zip_ref.read(file_name).decode("utf-8")
                return file_content
            else:
                raise Exception("The ZIP file is empty.")
    else:
        raise Exception(
            f"Failed to download the ZIP file. HTTP Status Code: {response.status_code}"
        )


# Function to generate a complete list of dates between two dates
def generate_date_series(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def get_rates_from_bottom_in_memory(csv_content, selected_currencies):
    """
    Parses CSV content from a string and gets exchange rates for specific currencies
    from bottom to top.

    Parameters:
    - csv_content (str): The content of the CSV file as a string.
    - selected_currencies (list): A list of currency codes to retrieve rates for.

    Returns:
    - all_rates (dict): A dictionary with dates as keys and another dictionary of currencies
      and their rates as values.
    - all_rates_dates (list): A list of dates for which rates are available.
    """
    all_rates_dates = []
    all_rates = {}
    file_like_object = io.StringIO(csv_content)
    csv_reader = list(csv.DictReader(file_like_object))
    for row in reversed(csv_reader):
        rates = {}
        for currency in selected_currencies:
            rates[currency] = float(row[currency]) if row[currency] != "N/A" else None
        all_rates_dates.append(row["Date"])
        all_rates[row["Date"]] = rates
    return all_rates, all_rates_dates


def process_currency_combinations_daily(db_path, all_rates, all_rates_dates):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    time_series = generate_date_series(all_rates_dates[0], all_rates_dates[-1])
    complete_days = get_complete_days(db_path)
    filtered_time_series = [
        date
        for date in time_series
        if datetime.strftime(date, "%Y-%m-%d") not in complete_days
    ]

    for date in filtered_time_series:
        rate_date = datetime.strftime(date, "%Y-%m-%d")

        # Determine which date to use for rates based on availability
        if rate_date in all_rates:
            use_date = rate_date
        elif datetime.strftime(date + timedelta(days=-1), "%Y-%m-%d") in all_rates:
            use_date = datetime.strftime(date + timedelta(days=-1), "%Y-%m-%d")
        elif datetime.strftime(date + timedelta(days=-2), "%Y-%m-%d") in all_rates:
            use_date = datetime.strftime(date + timedelta(days=-2), "%Y-%m-%d")
        else:
            continue  # Skip this date if no rates are available

        rates = all_rates[use_date]
        columns = ", ".join(rates.keys())  # Get all currency column names from rates
        placeholders = ", ".join(["?" for _ in rates])  # Create placeholders for values
        values = [rates[currency] for currency in rates]  # Get all currency values
        query = f"INSERT OR IGNORE INTO exchanges (rate_date, {columns}) VALUES (?, {placeholders})"
        cursor.execute(query, [rate_date] + values)
        connection.commit()
    fill_missing_rates(db_path, "exchanges")

    last_registered_date = cursor.execute(
        "SELECT rate_date FROM exchanges ORDER BY rate_date DESC LIMIT 1;"
    ).fetchone()[0]
    connection.close()
    return last_registered_date


def run_currency_update():
    # Database path
    db_path = "databases/main.db"

    # List of selected currencies
    selected_currencies = [
        "AUD",
        "BGN",
        "BRL",
        "CAD",
        "CHF",
        "CNY",
        "CZK",
        "DKK",
        "GBP",
        "HKD",
        "HUF",
        "IDR",
        "ILS",
        "INR",
        "ISK",
        "JPY",
        "KRW",
        "MXN",
        "MYR",
        "NOK",
        "NZD",
        "PHP",
        "PLN",
        "RON",
        "SEK",
        "SGD",
        "THB",
        "TRY",
        "USD",
        "ZAR",
    ]

    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"
    unzipped_file = download_and_unzip(url)
    all_rates, all_rates_dates = get_rates_from_bottom_in_memory(
        unzipped_file, selected_currencies
    )
    return process_currency_combinations_daily(db_path, all_rates, all_rates_dates)
