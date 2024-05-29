import os
from playwright.sync_api import sync_playwright
import json
import csv
import re
from dotenv import load_dotenv

class LinkedInPostScraper:
    def __init__(self, cookies):
        self.cookies = cookies

    def scrape_posts(self, linkedin_url, person_id):
        # Ensure the LinkedIn URL ends with a trailing slash
        if not linkedin_url.endswith("/"):
            linkedin_url += "/"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            
            try:
                context = browser.new_context()
            except Exception as e:
                print(f"Error creating a new context: {str(e)}")
                browser.close()
                return
            
            if context is None:
                print(f"Failed to create a new context for person with ID: {person_id}. Skipping.")
                browser.close()
                return
            
            context.add_cookies(self.cookies)
            page = context.new_page()
            
            try:
                # Navigate to the LinkedIn profile page with timeout
                page.goto(linkedin_url, timeout=60000)  # Increase the timeout to 60 seconds
                page.wait_for_selector('.profile-creator-shared-feed-update__mini-container', timeout=30000)  # Wait for a specific element to load
                print(f"Navigated to: {page.url}")  # Log the current URL

                # Wait for 5 seconds before extracting post links
                page.wait_for_timeout(5000)
                
            except Exception as e:
                print(f"Error navigating to LinkedIn profile page for person with ID: {person_id}")
                print(f"Error message: {str(e)}")
                browser.close()
                return
            
            # Extract the links to posts
            post_links = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('.profile-creator-shared-feed-update__mini-container a[data-test-app-aware-link][href^="https://www.linkedin.com/feed/update/"]'));
                    return links.map(link => link.href);
                }
            """)
            
            # Remove duplicate post links
            unique_post_links = set(post_links)
            
            print(f"Found {len(unique_post_links)} unique post links")  # Log the number of unique post links found
            
            # Save the unique post links to a CSV file
            csv_filename = f"{person_id}_li_posts.csv"
            with open(csv_filename, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Post Link"])
                for link in unique_post_links:
                    writer.writerow([link])
            
            print(f"Unique post links saved to {csv_filename}")
            
            # Close the browser
            browser.close()
            
def load_cookies_from_file(file_path):
    with open(file_path, "r") as file:
        cookie_data = json.load(file)
    return cookie_data

def agent_scrape_linkedin_posts(individuals_data_file):
    # Load the .env file
    load_dotenv()
    
    # Load all the cookies from the .li_session file
    cookies_file = ".li_session"
    cookies = load_cookies_from_file(cookies_file)
    
    # Load the individuals_data_enriched JSON file
    with open(individuals_data_file, "r") as file:
        individuals_data = json.load(file)
    
    scraper = LinkedInPostScraper(cookies)
    
    for person_data in individuals_data:
        if "person" in person_data and "linkedin_url" in person_data["person"]:linkedin_url = person_data["person"]["linkedin_url"]
        person_id = person_data["person"]["id"]
        scraper.scrape_posts(linkedin_url, person_id)
    else:
        print(f"LinkedIn URL not found for person with ID: {person_data['person']['id']}")

# Example usage
individuals_data_file = input("Enter the path to the individuals_data_enriched JSON file: ")
agent_scrape_linkedin_posts(individuals_data_file)
