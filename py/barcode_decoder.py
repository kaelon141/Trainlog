import datetime
import re
from datetime import timedelta

import cv2
import pytz
import requests
import zxingcpp

from py.utils import load_config


def decode(bcbp):
    result = {}

    try:
        name_bcbp = bcbp[2:22].replace(" ", "")
        fullname = name_bcbp.split("/")
        result["firstname"] = str(
            re.sub("(MRS|MR|MS|MSTR|DR)$", "", fullname[1]).replace(" ", "")
        )
        result["lastname"] = str(fullname[0].replace(" ", ""))

        result["pnr"] = str(bcbp[22:30].replace(" ", ""))
        result["origin"] = str(bcbp[30:33].replace(" ", ""))
        result["destination"] = str(bcbp[33:36].replace(" ", ""))
        result["operator"] = str(bcbp[36:38].replace(" ", ""))
        result["flight_number"] = str(bcbp[39:43].replace(" ", ""))
        result["date"] = str(datetime.strptime(bcbp[44:47], "%j").strftime("%d/%b"))
        result["cabin_class"] = str(bcbp[47].replace(" ", ""))
        result["seat_number"] = str(bcbp[49:52].replace(" ", ""))
        result["checkin_sequence"] = str(bcbp[52:56].replace(" ", ""))

        return result
    except Exception:
        return '{"error":"unable to parse string - incorrect format"}'


def boundariesFromDay(input_date):
    # Use the current year
    year = datetime.now().year

    # Parse the input date and add the current year
    date_with_year = datetime.strptime(f"{input_date}/{year}", "%d/%b/%Y")

    # Format start and end timestamps
    start_timestamp = date_with_year.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_timestamp = (date_with_year + timedelta(days=1, seconds=-1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    return start_timestamp, end_timestamp


def readBarcode(barcode):
    img = cv2.imdecode(barcode, 1)
    results = zxingcpp.read_barcodes(img)
    for result in results:
        decoded = decode(result.text)
        flight_number = decoded["operator"] + decoded["flight_number"]
        start_timestamp, end_timestamp = boundariesFromDay(decoded["date"])
        url = f"https://aeroapi.flightaware.com/aeroapi/flights/{flight_number}"
        headers = {
            "Accept": "application/json; charset=UTF-8",
            "x-apikey": load_config()["flightaware"]["fa_key"],
        }
        params = {"start": start_timestamp, "end": end_timestamp}

        # Make the GET request
        response = requests.get(url, headers=headers, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON if needed
            flight_data = response.json()["flights"][0]

            origin_tz = pytz.timezone(flight_data["origin"]["timezone"])
            destination_tz = pytz.timezone(flight_data["destination"]["timezone"])

            estimated_out_utc = datetime.strptime(
                flight_data["estimated_out"], "%Y-%m-%dT%H:%M:%SZ"
            )
            estimated_in_utc = datetime.strptime(
                flight_data["estimated_in"], "%Y-%m-%dT%H:%M:%SZ"
            )

            estimated_out_local = datetime.strftime(
                estimated_out_utc.replace(tzinfo=pytz.utc).astimezone(destination_tz)
                - timedelta(days=1),
                "%Y-%m-%dT%H:%M",
            )
            estimated_in_local = datetime.strftime(
                estimated_in_utc.replace(tzinfo=pytz.utc).astimezone(origin_tz)
                - timedelta(days=1),
                "%Y-%m-%dT%H:%M",
            )
            from pprint import pprint

            pprint(flight_data)
            result = {
                "origin": decoded["origin"],
                "destination": decoded["destination"],
                "flight_number": flight_number,
                "start_datetime": estimated_out_local,
                "end_datetime": estimated_in_local,
                "seat_number": decoded["seat_number"],
                "material": flight_data["aircraft_type"],
                "operator": flight_data["operator"],
            }
            return result

        else:
            print(
                f"Failed to retrieve flight information. Status code: {response.status_code}"
            )
