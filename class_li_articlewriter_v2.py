import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from openai import OpenAI
import anthropic
import json

load_dotenv()

class PerplexityArticleWriter:
    def __init__(self, cookies_file):
        self.cookies_file = cookies_file
        self.max_retries = 3
        self.api_key = os.getenv("PERPLEXITY_API_KEY")

    def load_cookies(self):
        with open(self.cookies_file, 'r') as file:
            cookies_data = file.read()
            self.cookies = json.loads(cookies_data)

    def prompt_user(self):
        print("Please provide the following information for generating the article:")
        article_length = int(input("Enter the desired length of the article in words: "))
        article_tone = input("Enter the desired tone of the article: ")
        article_purpose = input("Enter the purpose and subject of the article: ")
        target_region = input("Enter the target region or country for this article: ")

        keyword_density = None
        keywords = None
        example_article_link = None
        example_social_media_link = None

        keyword_option = input("Do you want to specify keywords and target keyword density? (yes/no): ").lower() == 'yes'
        if keyword_option:
            keywords = input("Enter the necessary keywords (comma-separated): ").split(',')
            keyword_density = float(input("Enter the target keyword density (e.g., 0.02 for 2%): "))

        article_option = input("Do you want to provide a link to an example article? (yes/no): ").lower() == 'yes'
        if article_option:
            example_article_link = input("Enter the link to the example article: ")

        social_media_option = input("Do you want to provide a link to an example social media profile? (yes/no): ").lower() == 'yes'
        if social_media_option:
            example_social_media_link = input("Enter the link to the example social media profile: ")

        return article_length, article_tone, article_purpose, target_region, keyword_density, keywords, example_article_link, example_social_media_link

    def scrape_content(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3")
            page.goto(url)
            content = page.content()
            browser.close()
        return content

    def generate_article(self, prompt):
        print("Generating article using Anthropic Claude-3 Opus...")
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0.7,
            system="You are an expert content marketer and business development executive that generates thought provoking and SEO optimized articles for LinkedIn based on the requirements.",
            messages=[
                    {"role": "user", "content": prompt}
                ]
        )
        print("Article generated successfully.")

        article_content = response.content[0].text # Extract the text content from the ContentBlock object
        return article_content
    
    def write_article(self, article_length, article_tone, article_purpose, target_region, keywords=None, keyword_density=None, example_article_link=None, example_social_media_link=None):
        print("Generating article using Perplexity.ai...")

        prompt = f"Please write an SEO-optimized article of approximately {article_length} words with the following requirements:\n\n"
        prompt += f"Purpose and subject: {article_purpose}\n"
        prompt += f"Tone: {article_tone}\n"
        prompt += f"Target region or country: {target_region}\n"

        if keyword_density:
            prompt += f"Use the following keywords with a target keyword density of {keyword_density}: {','.join(keywords)}\n"

        if example_article_link:
            example_article_content = self.scrape_content(example_article_link)
            prompt += f"Use the following example article as a reference for style and structure:\n{example_article_content}\n"

        if example_social_media_link:
            example_social_media_content = self.scrape_content(example_social_media_link)
            prompt += f"Mirror the tone and style of the following social media profile:\n{example_social_media_content}\n"

        prompt += "To optimize the article for SEO, follow these rules:\n"
        prompt += "1. Find a primary keyword to target\n"
        prompt += "2. Assess search intent\n"
        prompt += "3. Assess your chances of ranking in Google\n"
        prompt += "4. Research what people want to know\n"
        prompt += "5. Optimize headings and subheadings\n"
        prompt += "6. Hook readers with your intro (blog posts only)\n"
        prompt += "7. Edit your copy for simplicity\n"
        prompt += "8. Link to relevant resources\n"
        prompt += "9. Make it easier to consume with images\n"
        prompt += "10. Optimize your images\n"
        prompt += "11. Set a compelling title tag and meta description\n"
        prompt += "12. Set an SEO-friendly URL slug\n"
        prompt += "13. Add schema markup for rich snippets\n"
        prompt += "14. Add a table of contents (blog posts only)\n"

        article_content = self.generate_article(prompt)
        print("Article generated successfully.")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Set cookies
            for cookie in self.cookies:
                page.context.add_cookies([cookie])

            page.goto('https://www.linkedin.com/article/new/')

            # Preview the article
            print("\nPreview of the article:")
            print("Content:", article_content)

            # Prompt for approval
            approved = input("Do you approve the article? You will be given one more opportunity later to approve or disapprove (yes/no): ").lower() == 'yes'

            if approved:
                # Wait for the article content paragraph to be visible
                page.wait_for_selector('div.prosemirror > p.article-editor-content__paragraph.is-empty.article-editor-content--is-empty', timeout=30000)
                page.fill('p.article-editor-content__paragraph.is-empty.article-editor-content--is-empty.article-editor-content__has-focus', article_content)

                # Wait for 2 seconds
                page.wait_for_timeout(2000)

                # Click the Next button
                page.click('button[class="article-editor-nav__publish artdeco-button artdeco-button--icon-right artdeco-button--2 artdeco-button--primary ember-view"]')

                # Wait for 5 seconds
                page.wait_for_timeout(5000)

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
        article_length, article_tone, article_purpose, target_region, keyword_density, keywords, example_article_link, example_social_media_link = self.prompt_user()

        retries = 0
        while retries < self.max_retries:
            approved = self.write_article(article_length, article_tone, article_purpose, target_region, keyword_density, keywords, example_article_link, example_social_media_link)
            if approved:
                break
            retries += 1

        if not approved:
            print("Max retries reached. Article not published.")

# Usage example
cookies_file = '.li_session'

article_writer = PerplexityArticleWriter(cookies_file)
article_writer.run()
