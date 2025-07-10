from collections import defaultdict
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

from py.currency import get_exchange_rate
from py.utils import load_config

bmc_api_key = load_config()["bmc"]["key"]


def calculate_monthly_revenue(subscription, revenue_per_month):
    start_date = datetime.strptime(
        subscription["subscription_created_on"], "%Y-%m-%d %H:%M:%S"
    )
    end_date = datetime.strptime(
        subscription["subscription_current_period_end"], "%Y-%m-%d %H:%M:%S"
    )
    monthly_price = (
        float(subscription["subscription_coffee_price"]) / 12
        if subscription["subscription_duration_type"] == "year"
        else float(subscription["subscription_coffee_price"])
    )

    current_date = start_date
    while current_date <= end_date:
        revenue_per_month[current_date.strftime("%Y-%m")] += monthly_price
        current_date += relativedelta(months=1)


def process_supporters(supporters, revenue_per_month):
    for supporter in supporters:
        price = float(supporter["support_coffees"]) * float(
            supporter["support_coffee_price"]
        )
        day = supporter["support_created_on"]
        month = datetime.strptime(day, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m")
        if month not in revenue_per_month:
            revenue_per_month[month] = price
        else:
            revenue_per_month[month] += price


# Function to fetch all pages of data from the API
def fetch_all_pages(url, headers):
    all_data = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data["data"])
            url = data.get("next_page_url", None)  # Update the URL for the next request
        else:
            print(f"Failed to retrieve data from {url}: {response.status_code}")
            print(response.text)
            break  # Exit loop in case of failure
    return all_data


def get_revenue_per_month():
    # Define the headers with the authorization token
    headers = {"Authorization": f"Bearer {bmc_api_key}"}

    # Initialize revenue_per_month
    revenue_per_month = defaultdict(float)

    # URLs for subscriptions and supporters
    sub_url = "https://developers.buymeacoffee.com/api/v1/subscriptions"
    sup_url = "https://developers.buymeacoffee.com/api/v1/supporters"

    # Fetch and process subscription data
    sub_data = fetch_all_pages(sub_url, headers)
    for subscription in sub_data:
        calculate_monthly_revenue(subscription, revenue_per_month)

    # Fetch and process supporter data
    sup_data = fetch_all_pages(sup_url, headers)
    process_supporters(sup_data, revenue_per_month)

    # Get the current month in the same format as your keys ('%Y-%m')
    current_month = datetime.now().strftime("%Y-%m")

    # Filter the dictionary to include only past months
    past_revenue_per_month = {
        month: revenue
        for month, revenue in revenue_per_month.items()
        if month <= current_month
    }

    # Optionally, convert defaultdict to a regular dictionary and sort by month
    ordered_revenue = dict(sorted(past_revenue_per_month.items()))
    return ordered_revenue


def get_spending_per_month():
    hosting_expenses_table = [
        {
            "type": "Routing Server",
            "from_date": datetime(2023, 1, 1),
            "to_date": datetime(2024, 3, 30),
            "amount": 11.04,
            "currency": "EUR",
        },
        {
            "type": "OVH main",
            "from_date": datetime(2023, 1, 1),
            "to_date": datetime(2024, 4, 30),
            "amount": 6,
            "currency": "EUR",
        },
        {
            "type": "Infomaniak 1",
            "from_date": datetime(2024, 3, 1),
            "to_date": datetime(2025, 3, 31),
            "amount": 29,
            "currency": "EUR",
        },
        {
            "type": "Infomaniak 2",
            "from_date": datetime(2025, 4, 1),
            "to_date": None,
            "amount": 79,
            "currency": "EUR",
        },
    ]

    translation_expenses_table = [
        {"amount": 25.00, "date": "2025-04-14 9:52:00", "currency": "USD"},
        {"amount": 25.00, "date": "2024-08-29 9:01:00", "currency": "USD"},
        {"amount": 62.50, "date": "2024-06-28 10:01:00", "currency": "USD"},
        {"amount": 43.75, "date": "2024-05-31 21:24:00", "currency": "USD"},
        {"amount": 31.25, "date": "2024-03-09 13:21:00", "currency": "USD"},
        {"amount": 31.25, "date": "2024-03-02 14:51:00", "currency": "USD"},
        {"amount": 37.50, "date": "2023-10-19 20:16:00", "currency": "USD"},
        {"amount": 25.00, "date": "2023-10-15 17:49:00", "currency": "USD"},
        {"amount": 12.50, "date": "2023-10-09 00:01:00", "currency": "USD"},
        {"amount": 12.50, "date": "2023-10-08 23:59:00", "currency": "USD"},
        {"amount": 62.50, "date": "2023-09-30 13:04:00", "currency": "USD"},
        {"amount": 12.50, "date": "2023-08-25 15:50:00", "currency": "USD"},
    ]

    # NEW: API subscription expenses
    api_subscription_expenses = [
        {
            "type": "Monthly API Subscription",
            "from_date": datetime(2025, 6, 25),  # Starting from June 25th
            "to_date": None,  # Ongoing
            "amount": 9.00,
            "currency": "USD",
        },
    ]

    # NEW: API topup expenses (one-time purchases)
    api_topup_expenses = [
        # Add your topup expenses here as they occur
        # Example:
        # {"amount": 50.00, "date": "2024-07-15 10:00:00", "currency": "USD"},
    ]

    # Initialize spending per month
    spending_per_month = defaultdict(
        lambda: {"hosting": 0, "translation": 0, "api_subscription": 0, "api_topup": 0}
    )

    # Process hosting expenses
    for expense in hosting_expenses_table:
        from_date = expense["from_date"]
        to_date = expense["to_date"] if expense["to_date"] else datetime.now()
        amount = expense["amount"]

        current_date = from_date
        while current_date <= to_date:
            month_key = current_date.strftime("%Y-%m")
            spending_per_month[month_key]["hosting"] -= amount
            current_date += relativedelta(months=1)

    # Process translation expenses
    for expense in translation_expenses_table:
        date = datetime.strptime(expense["date"], "%Y-%m-%d %H:%M:%S")
        month_key = date.strftime("%Y-%m")
        amount_in_euros = get_exchange_rate(
            expense["amount"], expense["currency"], "EUR", date
        )
        spending_per_month[month_key]["translation"] -= amount_in_euros

    # NEW: Process API subscription expenses
    for expense in api_subscription_expenses:
        from_date = expense["from_date"]
        to_date = expense["to_date"] if expense["to_date"] else datetime.now()

        current_date = from_date
        while current_date <= to_date:
            month_key = current_date.strftime("%Y-%m")
            # Convert USD to EUR for consistency
            amount_in_euros = get_exchange_rate(
                expense["amount"], expense["currency"], "EUR", current_date
            )
            spending_per_month[month_key]["api_subscription"] -= amount_in_euros
            current_date += relativedelta(months=1)

    # NEW: Process API topup expenses
    for expense in api_topup_expenses:
        date = datetime.strptime(expense["date"], "%Y-%m-%d %H:%M:%S")
        month_key = date.strftime("%Y-%m")
        amount_in_euros = get_exchange_rate(
            expense["amount"], expense["currency"], "EUR", date
        )
        spending_per_month[month_key]["api_topup"] -= amount_in_euros

    return spending_per_month


def get_finances():
    revenue_data = get_revenue_per_month()
    spending_data = get_spending_per_month()

    # Step 1: Combine and normalize dates
    all_dates = sorted(set(revenue_data.keys()) | set(spending_data.keys()))

    # Step 2: Initialize data points
    combined_data = {
        date: {
            "revenue": 0,
            "hosting_spending": 0,
            "translation_spending": 0,
            "api_subscription_spending": 0,
            "api_topup_spending": 0,
            "total_spending": 0,
            "profit": 0,
        }
        for date in all_dates
    }

    # Step 3: Fill data points
    for date in revenue_data:
        combined_data[date]["revenue"] = revenue_data[date]
    for date in spending_data:
        combined_data[date]["hosting_spending"] = spending_data[date]["hosting"]
        combined_data[date]["translation_spending"] = spending_data[date]["translation"]
        combined_data[date]["api_subscription_spending"] = spending_data[date][
            "api_subscription"
        ]
        combined_data[date]["api_topup_spending"] = spending_data[date]["api_topup"]
        combined_data[date]["total_spending"] = (
            spending_data[date]["hosting"]
            + spending_data[date]["translation"]
            + spending_data[date]["api_subscription"]
            + spending_data[date]["api_topup"]
        )

    # Calculate profit for each date
    for date in combined_data:
        combined_data[date]["profit"] = (
            combined_data[date]["revenue"] + combined_data[date]["total_spending"]
        )

    # Prepare data for the chart
    labels = list(combined_data.keys())
    revenue_data_points = [combined_data[date]["revenue"] for date in labels]
    hosting_spending_data_points = [
        combined_data[date]["hosting_spending"] for date in labels
    ]
    translation_spending_data_points = [
        combined_data[date]["translation_spending"] for date in labels
    ]
    api_subscription_spending_data_points = [
        combined_data[date]["api_subscription_spending"] for date in labels
    ]
    api_topup_spending_data_points = [
        combined_data[date]["api_topup_spending"] for date in labels
    ]
    total_spending_data_points = [
        combined_data[date]["total_spending"] for date in labels
    ]
    profit_data_points = [combined_data[date]["profit"] for date in labels]

    totals = {
        "revenue": round(
            sum([combined_data[date]["revenue"] for date in combined_data])
        ),
        "hosting_spending": round(
            sum([combined_data[date]["hosting_spending"] for date in combined_data])
        ),
        "translation_spending": round(
            sum([combined_data[date]["translation_spending"] for date in combined_data])
        ),
        "api_subscription_spending": round(
            sum(
                [
                    combined_data[date]["api_subscription_spending"]
                    for date in combined_data
                ]
            )
        ),
        "api_topup_spending": round(
            sum([combined_data[date]["api_topup_spending"] for date in combined_data])
        ),
        "total_spending": round(
            sum([combined_data[date]["total_spending"] for date in combined_data])
        ),
        "profit": round(sum([combined_data[date]["profit"] for date in combined_data])),
    }

    return (
        labels,
        revenue_data_points,
        hosting_spending_data_points,
        translation_spending_data_points,
        api_subscription_spending_data_points,
        api_topup_spending_data_points,
        total_spending_data_points,
        profit_data_points,
        totals,
    )
