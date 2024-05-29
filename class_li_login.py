import os
import json
from playwright.sync_api import sync_playwright

class LinkedInLoginTool:
    def __init__(self, email, password):
        self.email = email
        self.password = password
    
    def login(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # Navigate to LinkedIn login page
            page.goto("https://www.linkedin.com/login")
            
            # Fill in the email and password fields
            page.fill("#username", self.email)
            page.fill("#password", self.password)
            
            # Click the login button
            page.click('button[type="submit"]')
            
            # Wait for the home page to load
            page.wait_for_selector(".feed-identity-module__actor-meta")
            
            print("Logged in successfully!")
            
            # Get all cookies
            cookies = page.context.cookies()
            
            # Save all cookies to a ".li_session" file, overwriting any existing file
            with open(".li_session", "w") as session_file:
                json.dump(cookies, session_file)
            
            print("All cookies saved to .li_session file.")
            
            # Close the browser
            browser.close()

def agent_login_to_linkedin(email, password):
    login_tool = LinkedInLoginTool(email, password)
    login_tool.login()

# Example usage
email = input("Enter your LinkedIn email: ")
password = input("Enter your LinkedIn password: ")

agent_login_to_linkedin(email, password)
