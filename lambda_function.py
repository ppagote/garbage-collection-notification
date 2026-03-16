from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime, timedelta
import os
import traceback

import smtplib
from email.message import EmailMessage

#from dotenv import load_dotenv 
# Load environment variables from .env file
# This is not needed in AWS Lambda, but useful for local testing
#load_dotenv()

url: str | None = os.getenv("URL")
username: str | None = os.getenv("GMAIL_USERNAME")
password: str | None = os.getenv("GMAIL_PASSWORD")
recipients: str | None = os.getenv("RECEPIENTS")

tomorrows_date: str = (datetime.today() + timedelta(days=1)).strftime("%d/%m/%Y")

emoji_map = {
    "RECYCLING": "\u26AB",  # Black
    "GARDEN": "\U0001F7E4",  # Brown
    "REFUSE": "\U0001F7E2",  # Green
}

def fetch_data() -> list[str]:
    if url is None:
        raise ValueError("Error: Missing URL configuration")
    
    session = requests.Session()
    
    response = session.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0'
            }
        )
    # Make a BS4 object
    soup = BeautifulSoup(response.text, features="html.parser")
    soup.prettify()
    return parse_data(soup)

def parse_data(soup: BeautifulSoup) -> list[str]:

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

def send_email(msg: str):
    if username is None or password is None or recipients is None:
        raise ValueError("Error: Missing email configuration")

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

def lambda_handler():
    try:
        bin_data = fetch_data()
        print(bin_data)

        if len(bin_data) != 0:
            msg = generate_message(bin_data)
            print(msg)

            send_email(msg)
        else:
            print("No collection data found for tomorrow.")

        return "Success"
    except Exception as e:
        print(traceback.format_exc())
        return "Error: " + str(e)


lambda_handler()
