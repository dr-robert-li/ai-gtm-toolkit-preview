import json
from playwright.sync_api import sync_playwright
import os
import time
import re
import pandas as pd
import docx
from PyPDF2 import PdfReader
import csv
import anthropic
from dotenv import load_dotenv

load_dotenv()

class LinkedInConnector:
    def __init__(self, input_file, session_file):
        self.input_file = input_file
        self.session_file = session_file
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Client(api_key=self.anthropic_api_key)

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
    
    def generate_response(self, post_content):
        print("Generating response using Anthropic Claude 3 Haiku...")
        prompt = f"\n\nPlease write an inviting note to connect on LinkedIn referencing something interesting in the profile here:\n\n{post_content}\n\nIt MUST be less than 15 words.\n\nFocus on the posts, experience, skills and interests.\n\nDo NOT reference any names EXCEPT their FIRST NAME, which can be found in this h1 class: text-heading-xlarge.\n\nDo NOT reference that they are using a Premium LinkedIn account.\n\nNever state: Here is a 15-word invitation to connect on LinkedIn. Never provide a heading or subject line. Never state what is being done in any way, shape or form."
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0.7,
            system="You are an expert business development executive loves to network with like-minded business people",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("Response generated successfully.")

        response_output = response.content[0].text  # Extract the text content from the ContentBlock object
        return response_output
    
    def auto_add_note(self, page, profile_url):
        time.sleep(1.5)  # Wait for 1500ms for elements to load
        add_note_button = page.query_selector('button[aria-label="Add a note"]')
        if add_note_button:
            print("Add a note button found")
            add_note_button.click()
            print("Clicked on the add a note button")
            time.sleep(1.5)  # Wait for 1500ms before filling the text box

            # Scrape the entire profile element
            profile_element = page.query_selector('main.scaffold-layout__main')
            if profile_element:
                profile_content = profile_element.inner_text()
                print("Generating note content...")
                note_content = self.generate_response(profile_content)
                # Remove the quotation marks at the start and end of the note
                note_content = note_content.strip('"')
                print(f"Generated note content: {note_content}")

                # Fill the text box with the generated note
                text_box = page.query_selector('textarea[name="message"]')
                if text_box:
                    text_box.fill(note_content)
                    print("Filled the text box with the generated note")

                    # Ask the user if they wish to send the invite with the note
                    for attempt in range(3):
                        confirmation = input(f"Send connection request with the above note to {profile_url}? (y/n): ")
                        if confirmation.lower() == 'y':
                            send_button = page.query_selector('button[aria-label="Send invitation"]')
                            if send_button:
                                send_button.click()
                                print(f"Connection request with note sent to {profile_url}")
                            break
                        else:
                            if attempt < 2:
                                print("Generating a new note...")
                                note_content = self.generate_response(profile_content)
                                print(f"Generated new note content: {note_content}")
                                # Delete the existing text in the text box
                                text_box.press("Control+A")
                                text_box.press("Delete")
                                # Fill the text box with the new note
                                text_box.fill(note_content)
                            else:
                                print(f"Skipping connection request for {profile_url}")
                else:
                    print("Text box not found")
            else:
                print("Profile element not found")
        else:
            print("Add a note button not found")

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
            auto_confirm_input = input("Do you want to auto-confirm connection requests? This will skip adding a note (y/n): ")
            self.auto_confirm = auto_confirm_input.lower() == 'y'

            if self.auto_confirm:
                print("Confirm: Auto-confirming connection requests, skipping adding a note.")
            else:
                auto_add_note_input = input("Do you want to add a note to the connection request? (y/n): ")
                self.auto_add_note_enabled = auto_add_note_input.lower() == 'y'

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

                    if self.auto_confirm:
                        send_without_note_button = page.query_selector('button.artdeco-button--primary[aria-label="Send without a note"]')
                        if send_without_note_button:
                            print("Send without note button found")
                            send_without_note_button.click()
                            print(f"Connection request sent to {profile_url}")
                    else:
                        if self.auto_add_note_enabled:
                            self.auto_add_note(page, profile_url)
                        else:
                            confirmation = input(f"Send connection request without a note to {profile_url}? (y/n): ")
                            if confirmation.lower() == 'y':
                                send_without_note_button = page.query_selector('button.artdeco-button--primary[aria-label="Send without a note"]')
                                if send_without_note_button:
                                    print("Send without note button found")
                                    send_without_note_button.click()
                                    print(f"Connection request sent to {profile_url}")
                            else:
                                self.auto_add_note(page, profile_url)
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

                        if self.auto_confirm:
                            send_without_note_button = page.query_selector('button.artdeco-button--primary[aria-label="Send without a note"]')
                            if send_without_note_button:
                                print("Send without note button found")
                                page.evaluate('(element) => element.click()', send_without_note_button)
                                print(f"Connection request sent to {profile_url}")
                        else:
                            if self.auto_add_note_enabled:
                                self.auto_add_note(page, profile_url)
                            else:
                                confirmation = input(f"Send connection request without a note to {profile_url}? (y/n): ")
                                if confirmation.lower() == 'y':
                                    send_without_note_button = page.query_selector('button.artdeco-button--primary[aria-label="Send without a note"]')
                                    if send_without_note_button:
                                        print("Send without note button found")
                                        page.evaluate('(element) => element.click()', send_without_note_button)
                                        print(f"Connection request sent to {profile_url}")
                                else:
                                    self.auto_add_note(page, profile_url)
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



