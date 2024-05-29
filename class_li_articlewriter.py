import json
from playwright.sync_api import sync_playwright
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

class LinkedInArticleWriter:
    def __init__(self, cookies_file, json_file):
        self.cookies_file = cookies_file
        self.json_file = json_file
        self.max_retries = 3
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Client(api_key=self.api_key)

    def load_cookies(self):
        with open(self.cookies_file, 'r') as file:
            cookies_data = file.read()
            self.cookies = json.loads(cookies_data)

    def load_json_data(self):
        with open(self.json_file, 'r') as file:
            self.json_data = json.load(file)

    def get_person_keywords(self):
        persons = []
        for item in self.json_data:
            person = item.get('person', {})
            name = person.get('name', '')
            organization = person.get('organization', {})
            keywords = organization.get('keywords', [])
            persons.append((name, keywords))
        return persons

    def prompt_user(self, persons):
        print("Select a person to use their keywords as the article seed:")
        for i, (name, keywords) in enumerate(persons, start=1):
            print(f"{i}. Name: {name}")
            print("   Keywords:", ', '.join(keywords))
            print()

        choice = int(input("Enter your choice (1-{}): ".format(len(persons))))
        return persons[choice - 1]

    def generate_article(self, keywords):
        print("Generating article using Anthropic Claude-3 Opus...")
        prompt = f"Please write an article of no more than 500 words based on the following keywords: {', '.join(keywords)}. The article should provide insights and explore the relationships between the keywords. Use appropriate hashtags. Divide the content into subsections with subheadings. There should be an introduction and conclusion with a call to action, but do not use the subheadings Introduction, Conclusion or Call To Action. Do not create a title. The tone should be professional, succint and authoritative."
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0.7,
            system="You are an expert content marketer and business development executive that generates thought provoking articles for LinkedIn.",
            messages=[
                    {"role": "user", "content": prompt}
                ]
        )
        print("Article generated successfully.")

        article_content = response.content[0].text # Extract the text content from the ContentBlock object
        return article_content
    
    def generate_title(self, article_content):
        print("Generating title using Anthropic Claude-3 Haiku...")
        prompt = f"Please generate a concise and thought provoking click-bait title for the following article:\n\n{article_content}. Use no more than 10 words. Do not include any quotation marks."
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0.7,
            system="You are an expert content marketer and business development executive that generates thought eye catching, clickable titles for LinkedIn articles.",
            messages=[
                    {"role": "user", "content": prompt}
                ]
        )
        print("Title generated successfully.")

        title = response.content[0].text # Extract the text content from the ContentBlock object
        return title
    
    def generate_summary(self, article_content):
        print("Generating summary using Anthropic Claude-3 Haiku...")
        prompt = f"Please generate a professional but catchy summary of no more than 25 words of the following article with appropriate hashtags:\n\n{article_content}"
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0.7,
            system="You are an expert content marketer and business development executive that generates thought-provoking and engaging summaries for LinkedIn articles.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("Summary generated successfully.")

        summary = response.content[0].text  # Extract the text content from the ContentBlock object
        return summary

    def write_article(self, keywords):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Set cookies
            for cookie in self.cookies:
                page.context.add_cookies([cookie])

            page.goto('https://www.linkedin.com/article/new/')

            # Generate the article using Anthropic API
            article_content = self.generate_article(keywords)

            # Generate the title using Anthropic API
            title = self.generate_title(article_content)

            # Generate the summary using Anthropic API
            summary = self.generate_summary(article_content)

            # Preview the article
            print("\nPreview of the article:")
            print("Title:", title)
            print("Content:", article_content)

            # Prompt for approval
            approved = input("Do you approve the article? You will be given one more opportunity later to approve or disapprove (yes/no): ").lower() == 'yes'

            if approved:
                # Wait for the title textarea to be visible
                page.wait_for_selector('textarea[id="article-editor-headline__textarea"]', timeout=30000)
                page.fill('textarea[id="article-editor-headline__textarea"]', title)

                # Wait for 2 seconds
                page.wait_for_timeout(3000)

                # Press the Tab key to move focus to the article content area
                # page.press('textarea[id="article-editor-headline__textarea"]', 'Tab')

                # Wait for the article content paragraph to be visible
                # page.wait_for_selector('div.prosemirror > p.article-editor-content__paragraph.is-empty.article-editor-content--is-empty', timeout=30000)
                # page.fill('p.article-editor-content__paragraph.is-empty.article-editor-content--is-empty.article-editor-content__has-focus', article_content)
                page.keyboard.type(article_content)

                # Wait for 2 seconds
                page.wait_for_timeout(2000)

                # Click the Next button
                page.click('button[class="article-editor-nav__publish artdeco-button artdeco-button--icon-right artdeco-button--2 artdeco-button--primary ember-view"]')

                # Wait for 5 seconds
                page.wait_for_timeout(5000)

                # Wait for the summary div to be visible
                page.wait_for_selector('div[class="ql-editor ql-blank"]', timeout=30000)
                page.fill('div[class="ql-editor ql-blank"]', summary)

                # Prompt for approval one more time
                print("\nInjecting article into LinkedIn and pushing to publish...\n")
                final_approval = input("Do you want to publish the article? This is your final chance to approve or disapprove (yes/no): ").lower() == 'yes'

                if final_approval:
                    # Click the Publish button
                    page.click('button[class="share-actions__primary-action artdeco-button artdeco-button--2 artdeco-button--primary ember-view"]')
                    print("Article published successfully!")
                else:
                    print("Article not approved. Discarding...")
            else:
                print("Article not approved. Discarding...")

            browser.close()

        return approved



    def run(self):
        self.load_cookies()
        self.load_json_data()
        persons = self.get_person_keywords()
        selected_person, selected_keywords = self.prompt_user(persons)

        retries = 0
        while retries < self.max_retries:
            approved = self.write_article(selected_keywords)
            if approved:
                break
            retries += 1

        if not approved:
            print("Max retries reached. Article not published.")

# Usage example
cookies_file = '.li_session'
json_file = input("Enter the path to the JSON file: ")

article_writer = LinkedInArticleWriter(cookies_file, json_file)
article_writer.run()