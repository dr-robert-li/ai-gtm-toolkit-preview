import os
import csv
import json
import anthropic
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

class LinkedInCommentBot:
    def __init__(self, csv_files, auto_approve=False):
        self.csv_files = csv_files
        self.auto_approve = auto_approve
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.li_session_file = ".li_session"
        self.client = anthropic.Client(api_key=self.anthropic_api_key)

    def generate_response(self, post_content):
        print("Generating response using Anthropic API...")
        prompt = f"\n\nPlease write a response to the following LinkedIn post content in less than 50 words and end with a profound question, while not referencing any specific names:\n\n{post_content}"
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0.7,
            system="You are an expert content marketer and business development executive that generates responses to LinkedIn posts.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("Response generated successfully.")

        response_output = response.content[0].text  # Extract the text content from the ContentBlock object
        # print(response_output)
        return response_output

    def process_csv(self, csv_file):
        print(f"Processing CSV file: {csv_file}")
        with open(csv_file, "r") as file:
            reader = csv.reader(file)
            rows = list(reader)

        fieldnames = rows[0]
        if "Response" not in fieldnames:
            fieldnames.append("Response")
            print("Added 'Response' column to the CSV file.")
        if "Comment Posted" not in fieldnames:
            fieldnames.append("Comment Posted")
            print("Added 'Comment Posted' column to the CSV file.")

        for i in range(1, len(rows)):
            row = dict(zip(fieldnames, rows[i]))
            if "Response" not in row or "Comment Posted" not in row:
                post_content = row["Post Content"]
                retry_count = 0
                while retry_count < 3:
                    response = self.generate_response(post_content)
                    print(f"\nPost Content:\n{post_content}\n")
                    print(f"Generated Response:\n{response}\n")
                    if self.auto_approve:
                        approve = "y"
                        print("Auto-approving response.")
                    else:
                        approve = input("Do you approve this response? (y/n): ")
                    if approve.lower() == "y":
                        row["Response"] = response
                        post_link = row["Post Link"]
                        comment_posted = self.post_comment(post_link, response)
                        row["Comment Posted"] = "Yes" if comment_posted else "No"
                        print("Response approved and posted as a comment.")
                        break
                    else:
                        retry_count += 1
                        if retry_count < 3:
                            print("Retrying response generation...")
                        else:
                            print("Skipping this post.")
                            row["Response"] = ""
                            row["Comment Posted"] = "No"

            rows[i] = [row.get(field, "") for field in fieldnames]

        print("Saving updated data to the CSV file...")
        with open(csv_file, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(fieldnames)
            writer.writerows(rows[1:])
        print("CSV file updated successfully.")


    def post_comment(self, post_link, response):
        print(f"Posting comment on LinkedIn post: {post_link}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Load cookies from the .li_session file
            print("Loading LinkedIn session cookies...")
            with open(self.li_session_file, "r") as file:
                cookies = json.load(file)
                for cookie in cookies:
                    page.context.add_cookies([cookie])
            print("LinkedIn session cookies loaded successfully.")

            print("Navigating to the LinkedIn post...")
            page.goto(post_link)

            # Like the post
            print("Liking the LinkedIn post...")
            like_button = page.query_selector('button[aria-label*="React Like"]')
            if like_button:
                like_button.click()
                print("Post liked successfully.")
            else:
                print("Like button not found. Skipping liking the post.")

            # Enter the comment in the text box
            print("Entering the comment in the text box...")
            comment_box = page.query_selector(".comments-comment-box__form .ql-editor")
            if comment_box:
                comment_box.type(response)
                print("Comment entered successfully.")
                page.wait_for_timeout(3000)
                
                # Submit the comment
                print("Submitting the comment...")
                submit_button = page.query_selector(".comments-comment-box__submit-button")
                if submit_button:
                    submit_button.click()
                    page.wait_for_timeout(2000)
                    print("Comment submitted successfully.")
                    return True
                else:
                    print("Submit button not found. Comment not submitted.")
            else:
                print("Comment box not found. Comment not posted.")

            browser.close()
        return False

    def process_csv_files(self):
        print("Processing CSV files...")
        for csv_file in self.csv_files:
            self.process_csv(csv_file)
        print("All CSV files processed successfully.")

if __name__ == "__main__":
    csv_files = []
    while True:
        csv_file = input("Enter the path to a *_li_posts.csv file (or press Enter to finish): ")
        if csv_file == "":
            break
        csv_files.append(csv_file)

    auto_approve = input("Do you want to automatically approve responses? (y/n): ").lower() == "y"

    bot = LinkedInCommentBot(csv_files, auto_approve)
    bot.process_csv_files()
    print("LinkedIn commenting bot execution completed.")
