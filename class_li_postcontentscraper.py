import csv
import json
from playwright.sync_api import sync_playwright

class LinkedInPostContentScraper:
    def __init__(self, cookie_file=".li_session"):
        self.cookie_file = cookie_file

    def scrape_post_content(self, post_link):
        print(f"Scraping post content from: {post_link}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Run Chromium in non-headless mode
            context = browser.new_context()

            # Load cookies from file
            print("Loading cookies from file...")
            context.add_cookies(self.load_cookies_from_file())

            page = context.new_page()
            print("Navigating to the post link...")
            page.goto(post_link)

            # Find the post content within the specified HTML blocks
            print("Extracting post content...")
            post_content = page.query_selector(".feed-shared-update-v2__description-wrapper .feed-shared-inline-show-more-text")
            if post_content:
                print("Post content found.")
                return post_content.inner_text()
            else:
                print("Post content not found.")
                return ""

            browser.close()

    def load_cookies_from_file(self):
        print(f"Loading cookies from file: {self.cookie_file}")
        with open(self.cookie_file, 'r') as file:
            return json.load(file)

    def process_csv_file(self, file_path):
        print(f"Processing CSV file: {file_path}")
        
        # Read the CSV file
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Add a new column for post content
        rows[0].append("Post Content")

        # Scrape post content for each Post Link
        for i in range(1, len(rows)):
            post_link = rows[i][0]  # Assuming Post Link is in the first column
            print(f"Scraping post content for link: {post_link}")
            post_content = self.scrape_post_content(post_link)
            rows[i].append(post_content)

        # Write the updated data back to the CSV file
        print(f"Writing updated data back to CSV file: {file_path}")
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

        print(f"Finished processing CSV file: {file_path}")

# Usage example
if __name__ == "__main__":
    scraper = LinkedInPostContentScraper()

    # Prompt the user to enter the CSV file paths
    csv_files = []
    while True:
        file_path = input("Enter the path to a CSV file (or press Enter to finish): ")
        if file_path == "":
            break
        csv_files.append(file_path)

    # Process each CSV file
    for file_path in csv_files:
        print(f"Starting to process CSV file: {file_path}")
        scraper.process_csv_file(file_path)
        print(f"Finished processing CSV file: {file_path}")
