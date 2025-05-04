from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime, timedelta
#from twilio.rest import Client
import os

import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv 
# Load environment variables from .env file
# This is not needed in AWS Lambda, but useful for local testing
load_dotenv()

url: str = os.getenv("url")
'''
account_sid: str = os.getenv("account_sid")
auth_token: str = os.getenv("auth_token")
messaging_service_sid: str = os.getenv("messaging_service_sid")
contactNumbers: list = os.getenv("contactNumbers")
'''
username: str = os.getenv("gmail_username")
password: str = os.getenv("gmail_password")
recipients: str = os.getenv("recipients")

tomorrows_date = datetime.today() + timedelta(days=1)
tomorrows_date: str = datetime.strftime(tomorrows_date, "%d/%m/%Y")

emoji_map = {
    "RECYCLING": "\u26AB",  # Black
    "GARDEN": "\U0001F7E4",  # Brown
    "REFUSE": "\U0001F7E2",  # Green
}


def parse_data() -> list[str]:

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

'''
def connectTwilio(msg: str):

    client = Client(account_sid, auth_token)

    for to_contact in contactNumbers:

        message = client.messages.create(
            messaging_service_sid=messaging_service_sid,
            body=msg,
            to=to_contact,
        )

        print(message.sid)
'''

def send_email(msg: str):

    # Create the email content
    message = EmailMessage()
    message["Subject"] = "\u2757[URGENT] " + msg
    message["From"] = username
    message["To"] = recipients

    # Send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(username, password)
        server.send_message(message)
    print("Email sent successfully!")


def generate_message(bin_data: list[str]) -> str:
    return (
        "Collection for "
        + ", ".join(bin_data)
        + " is tomorrow ("
        + tomorrows_date
        + ")"
    )


def lambda_handler(event, context):
    try:
        bin_data = parse_data()
        print(bin_data)

        if len(bin_data) != 0:
            msg = generate_message(bin_data)
            print(msg)

            #connectTwilio(msg)
            send_email(msg)

        return "Success"
    except Exception as e:
        print(e)
        return "Error"


#lambda_handler(None, None)
