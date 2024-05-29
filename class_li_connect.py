import json
from playwright.sync_api import sync_playwright
import os
import time

class LinkedInConnector:
    def __init__(self, profile_json_file, session_file):
        self.profile_json_file = profile_json_file
        self.session_file = session_file

    def connect_to_profiles(self):
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

            if os.path.exists(self.profile_json_file):
                with open(self.profile_json_file, 'r') as file:
                    data = json.load(file)

                    for profile in data:
                        if 'person' in profile and 'linkedin_url' in profile['person']:
                            profile_url = profile['person']['linkedin_url']
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
                                page.wait_for_selector('section.artdeco-card', timeout=10000) ### Check Section - send with note
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
            else:
                print(f"JSON file not found: {self.profile_json_file}")

            browser.close()

# Usage example
json_file = input("Enter the full path to the JSON file containing LinkedIn profiles: ")
session_file = '.li_session'
connector = LinkedInConnector(json_file, session_file)
connector.connect_to_profiles()
