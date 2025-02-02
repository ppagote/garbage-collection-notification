from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime, timedelta
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("url")
account_sid: str = os.getenv("account_sid")
auth_token: str = os.getenv("auth_token")
messaging_service_sid: str = os.getenv("messaging_service_sid")
contactNumbers: list = os.getenv("contactNumbers")

tomorrows_date = datetime.today() + timedelta(days=1)
tomorrows_date: str = datetime.strftime(tomorrows_date, "%d/%m/%Y")

emoji_map = {
    "RECYCLING": "\u26AB",  # Black
    "GARDEN": "\U0001F7E4",  # Brown
    "REFUSE": "\U0001F7E2",  # Green
}


def parse_data() -> dict:

    response = requests.get(url)
    # Make a BS4 object
    soup = BeautifulSoup(response.text, features="html.parser")
    soup.prettify()

    # Extract data
    bin_data: list[str] = []

    # Find the table containing the bin collection data
    table = soup.find("table", {"class": "eb-EVDNdR1G-tableContent"})

    if table:
        rows = table.find_all("tr", class_="eb-EVDNdR1G-tableRow")

        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 4:
                collection_type = columns[1].get_text(strip=True)
                collection_date = columns[3].get_text(strip=True)

                # Validate collection_date format
                if (
                    re.match(r"\d{2}/\d{2}/\d{4}", collection_date)
                    and collection_date == tomorrows_date
                ):
                    bin_type: str = collection_type + " " + emoji_map[collection_type]
                    bin_data.append(bin_type)

    return bin_data


def connectTwilio(bin_data: list[str]):

    if len(bin_data) != 0:
        msg = (
            "Collection for "
            + ", ".join(bin_data)
            + " is tomorrow ("
            + tomorrows_date
            + ")"
        )
        print(msg)

        client = Client(account_sid, auth_token)

        for to_contact in contactNumbers:

            message = client.messages.create(
                messaging_service_sid=messaging_service_sid,
                body=msg,
                to=to_contact,
            )

            print(message.sid)


def lambda_handler(event, context):
    try:
        bin_data = parse_data()
        print(bin_data)

        connectTwilio(bin_data)

        return "Success"
    except Exception as e:
        print(e)
        return "Error"


lambda_handler(None, None)
