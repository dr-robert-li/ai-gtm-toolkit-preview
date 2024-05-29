import json
from playwright.sync_api import sync_playwright
import os
import time
import re
import pandas as pd
import docx
from PyPDF2 import PdfReader
import csv

class LinkedInConnector:
    def __init__(self, input_file, session_file):
        self.input_file = input_file
        self.session_file = session_file

    def extract_linkedin_urls(self):
        file_extension = os.path.splitext(self.input_file)[1].lower()
        linkedin_urls = []

        if file_extension == ".json":
            with open(self.input_file, "r") as file:
                individuals_data = json.load(file)

            for person_data in individuals_data:
                if "person" in person_data:
                    linkedin_url = None
                    for key, value in person_data["person"].items():
                        if isinstance(value, str) and value.startswith("https://www.linkedin.com/in/"):
                            linkedin_url = value
                            break

                    if linkedin_url:
                        linkedin_urls.append(linkedin_url)
                    else:
                        print(f"LinkedIn profile URL not found for person with ID: {person_data['person']['id']}")
                else:
                    print(f"Person data not found for entry: {person_data}")

        elif file_extension in [".xls", ".xlsx"]:
            df = pd.read_excel(self.input_file)
            for _, row in df.iterrows():
                for value in row.values:
                    if isinstance(value, str) and value.startswith("https://www.linkedin.com/in/"):
                        linkedin_urls.append(value)

        elif file_extension == ".csv":
            with open(self.input_file, "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    for value in row:
                        if value.startswith("https://www.linkedin.com/in/"):
                            linkedin_urls.append(value)

        elif file_extension == ".txt":
            with open(self.input_file, "r") as file:
                for line in file:
                    if line.startswith("https://www.linkedin.com/in/"):
                        linkedin_urls.append(line.strip())

        elif file_extension == ".docx":
            doc = docx.Document(self.input_file)
            for paragraph in doc.paragraphs:
                if paragraph.text.startswith("https://www.linkedin.com/in/"):
                    linkedin_urls.append(paragraph.text.strip())

        elif file_extension == ".pdf":
            with open(self.input_file, "rb") as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    urls = re.findall(r"https://www.linkedin.com/in/\S+", text)
                    linkedin_urls.extend(urls)

        else:
            print(f"Unsupported file format: {file_extension}")

        return linkedin_urls
    def connect_to_profiles(self):
        linkedin_urls = self.extract_linkedin_urls()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()

            # Load cookies from the session file
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as file:
                    cookies = json.load(file)
                context.add_cookies(cookies)
            else:
                print(f"Session file not found: {self.session_file}")
                return

            page = context.new_page()

            # Prompt the user for auto-confirmation
            auto_confirm_input = input("Do you want to auto-confirm connection requests? (y/n): ")
            self.auto_confirm = auto_confirm_input.lower() == 'y'

            for profile_url in linkedin_urls:
                # Validate the profile URL
                if not self.is_valid_linkedin_url(profile_url):
                    print(f"Invalid LinkedIn URL: {profile_url}")
                    continue

                print(f"Navigating to profile: {profile_url}")
                try:
                    page.goto(profile_url, timeout=10000)
                    print(f"Successfully navigated to profile: {profile_url}")
                except Exception as e:
                    print(f"Error navigating to profile: {profile_url}")
                    print(f"Error message: {str(e)}")
                    continue

                # Wait for the profile actions section to be loaded
                try:
                    page.wait_for_selector('section.artdeco-card', timeout=10000)
                    print("Profile actions section loaded successfully")
                except Exception as e:
                    print(f"Error waiting for profile actions section to load: {profile_url}")
                    print(f"Error message: {str(e)}")
                    continue

                time.sleep(3)
                # Find the connect button using the first selector
                connect_button = page.query_selector('button.pvs-profile-actions__action[aria-label*="Invite"][aria-label*="to connect"]')
                time.sleep(3)

                if connect_button:
                    print("Connect button found")
                    connect_button.click()
                    print("Clicked on the connect button")
                    time.sleep(3)  # Wait for 3 seconds before attempting to press the send button
                    send_without_note_button = page.query_selector('button.artdeco-button--primary[aria-label="Send without a note"]')
                    if send_without_note_button:
                        print("Send without note button found")
                        if self.auto_confirm:
                            send_without_note_button.click()
                            print(f"Connection request sent to {profile_url}")
                        else:
                            confirmation = input(f"Send connection request without a note to {profile_url}? (y/n): ")
                            if confirmation.lower() == 'y':
                                send_without_note_button.click()
                                print(f"Connection request sent to {profile_url}")
                            else:
                                print(f"Skipping connection request for {profile_url}")
                else:
                    print(f"First connect button not found for profile: {profile_url}")
                    # Try finding the second connect button
                    second_connect_button = page.query_selector('div.artdeco-dropdown__item[aria-label*="Invite"][aria-label*="to connect"]')
                    if second_connect_button:
                        print("Second connect button found")
                        time.sleep(3)
                        page.evaluate('(element) => element.click()', second_connect_button)
                        print("Clicked on the second connect button using page.evaluate()")
                        time.sleep(3)  # Wait for 3 seconds before attempting to press the send button
                        send_without_note_button = page.query_selector('button.artdeco-button--primary[aria-label="Send without a note"]')
                        if send_without_note_button:
                            print("Send without note button found")
                            if self.auto_confirm:
                                page.evaluate('(element) => element.click()', send_without_note_button)
                                print(f"Connection request sent to {profile_url}")
                            else:
                                confirmation = input(f"Send connection request without a note to {profile_url}? (y/n): ")
                                if confirmation.lower() == 'y':
                                    page.evaluate('(element) => element.click()', send_without_note_button)
                                    print(f"Connection request sent to {profile_url}")
                                else:
                                    print(f"Skipping connection request for {profile_url}")
                    else:
                        print(f"Second connect button not found for profile: {profile_url}")

                # Wait for a short delay before proceeding to the next profile
                time.sleep(2)

            browser.close()

    def is_valid_linkedin_url(self, url):
        pattern = r'^https://www\.linkedin\.com/in/[\w-]+'
        return re.match(pattern, url) is not None

# Usage example
input_file = input("Enter the full path to the file containing LinkedIn profiles (JSON, XLS, XLSX, CSV, TXT, DOCX, PDF): ")
session_file = '.li_session'
connector = LinkedInConnector(input_file, session_file)
connector.connect_to_profiles()
