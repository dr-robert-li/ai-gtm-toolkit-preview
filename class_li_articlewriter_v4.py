import json
from playwright.sync_api import sync_playwright
import anthropic
from dotenv import load_dotenv
from openai import OpenAI
import os
import re
import requests

load_dotenv()

class LinkedInArticleWriter:
    def __init__(self, cookies_file):
        self.cookies_file = cookies_file
        self.max_retries = 3
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Client(api_key=self.api_key)
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

    def load_cookies(self):
        with open(self.cookies_file, 'r') as file:
            cookies_data = file.read()
            self.cookies = json.loads(cookies_data)

    def get_top_articles(self, region, subject):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert researcher who does content research for writers and provides URL links to source material."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Perform a Google search in {region} to provide a list of URLs and Links to the top 5 recent website articles, opinion pieces or blog posts on the subject: {subject}. URLs and links MUST being provided for each result, NO EXCEPTIONS."
                ),
            },
        ]

        client = OpenAI(api_key=self.perplexity_api_key, base_url="https://api.perplexity.ai")

        response = client.chat.completions.create(
            model="llama-3-sonar-small-32k-online",
            messages=messages,
        )
        print(response)

        return response.choices[0].message.content
    
    def get_influencers_and_posts(self, region, subject):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert social media marketer and researcher who finds top influencers on social media for a given subject and region."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Provide a list of the top 50 influencers, thought leaders and experts in {region} on LinkedIn and Twitter/X, on the subject: {subject}. Include their name, social media platform, and the latest content they have created. DO NOT provide suggestions if no direct result can be found."
                ),
            },
        ]

        client = OpenAI(api_key=self.perplexity_api_key, base_url="https://api.perplexity.ai")

        response = client.chat.completions.create(
            model="llama-3-sonar-small-32k-online",
            messages=messages,
        )
        print(response)

        return response.choices[0].message.content

    def extract_url_links(self, text):
        # Use regular expression to find URL links in the text
        url_regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        url_links = re.findall(url_regex, text)
        return url_links

    def summarize_articles(self, articles):
        summaries = []
        for article in articles:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert at efficiently summarizing content into less than 200 words while still maintaining the tone of the original author."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Please provide the author's name and a summary the following article: {article}"
                    ),
                },
            ]

            client = OpenAI(api_key=self.perplexity_api_key, base_url="https://api.perplexity.ai")

            response = client.chat.completions.create(
                model="llama-3-sonar-large-32k-online",
                messages=messages,
            )
            print(response)

            summaries.append(response.choices[0].message.content)

        return summaries

    def generate_article(self, summaries, subject, article_length, influencers_and_posts):
        print("Generating article using Anthropic Claude-3 Opus...")
        prompt = f"Please write an article of approximately {article_length} words based on the the subject: {subject}, and using the following summaries as inspiration making sure to keep the tone:\n\n{summaries}\n\n"
        prompt += f"The article should be coherent, and provide insight into a single theme that is most common in the summaries on {subject}. Use appropriate hashtags. Divide the content into subsections with subheadings. There should be an introduction and conclusion with a call to action, but do not use the subheadings Introduction, Conclusion or Call To Action. Do not create a title. The tone should be professional, succinct and authoritative.\n\n"
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
        prompt += "14. Add a table of contents (blog posts only)\n\n"
        prompt += f"Also, consider the top 50 influencers on social media related to {subject} and their latest posts:\n\n{influencers_and_posts}\n\n"
        prompt += f"Incorporate insights from these influencers and their posts related to {subject} into the article to provide additional context and relevance.\n\n"
        prompt += "The article MUST be written with Markdown formatting."

        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
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
                article_content = response.content[0].text  # Extract the text content from the ContentBlock object
                return article_content
            except Exception as e:
                retries += 1
                print(f"Error generating article: {str(e)}. Retrying... (Attempt {retries}/{max_retries})")
                if retries == max_retries:
                    print("Max retries reached. Unable to generate article.")
                    return None

    def generate_title(self, subject, article_content):
        print("Generating title using Anthropic Claude-3 Haiku...")
        prompt = f"Please generate a concise and thought provoking click-bait title for the following article:\n\n{article_content}. It is based on the subject: {subject}. Use no more than 10 words. Do not include any quotation marks."
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

        title = response.content[0].text  # Extract the text content from the ContentBlock object
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

    def generate_hero_image(self, title):
        print("Generating hero image using DALL-E 3...")
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"Create a professional header image for a LinkedIn article based on this subject - do not use any words, numbers or letters: {title}"

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        print(f"Hero image generated successfully. URL: {image_url}")

        # Download the image and save it locally
        print(f"Downloading...")
        response = requests.get(image_url)
        with open("hero_image.png", "wb") as file:
            file.write(response.content)

        print("Hero image downloaded and saved as 'hero_image.png'")

        return "hero_image.png"

    def write_article(self, article_content, title, summary):
        # Generate the hero image based on the title before opening the browser window
        hero_image_path = self.generate_hero_image(title)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Set cookies
            for cookie in self.cookies:
                page.context.add_cookies([cookie])

            page.goto('https://www.linkedin.com/article/new/')

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

                # Wait for 3 seconds
                page.wait_for_timeout(3000)

                page.keyboard.type(article_content)

                # Wait for 5 seconds to ensure article can be saved
                page.wait_for_timeout(5000)

                # Upload the hero image
                page.wait_for_selector('input[id="article-editor-cover-image__file-input"]', timeout=30000)
                page.set_input_files('input[id="article-editor-cover-image__file-input"]', hero_image_path)

                # Wait for 5 seconds to ensure image is uploaded
                page.wait_for_timeout(5000)

                # Retry clicking the "Next" button up to 10 times
                max_retries = 10
                retry_delay = 5000  # 5000ms = 5 seconds
                for attempt in range(1, max_retries + 1):
                    print(f"Attempt {attempt}: Clicking the 'Next' button...")
                    page.click('button[class="article-editor-nav__publish artdeco-button artdeco-button--icon-right artdeco-button--2 artdeco-button--primary ember-view"]')
                    page.wait_for_timeout(retry_delay)

                    # Check if the specified HTML element is present
                    if page.query_selector('h2[id="share-to-linkedin-modal__header"]'):
                        print("HTML element detected. Proceeding to the next step.")
                        break
                    else:
                        print(f"HTML element not found. Retrying in {retry_delay}ms...")

                    if attempt == max_retries:
                        print("Max retries reached. Unable to proceed to the next step.")
                        return False

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
        region = input("Enter the target region or country: ")
        subject = input("Enter the subject: ")
        article_length = int(input("Enter the desired article length (in words, 500 is the recommended): "))
        
        url_links = []
        while len(url_links) < 5:
            print("\nDoing a Perplexity.ai Search for the Top 5 articles and authors...")
            top_articles = self.get_top_articles(region, subject)
            print("\nInfluencers and Articles:")
            print(top_articles)

            # Extract URL links from the response
            url_links = self.extract_url_links(top_articles)
            print("\nExtracted URL Links:")
            print(url_links)

            if len(url_links) < 5:
                print("Less than 5 URLs found. Performing another search...")

        # Summarize the URL links using Perplexity
        summaries = self.summarize_articles(url_links)
        print("\nArticle Summaries:")
        print(summaries)

        print("\nDoing a Perplexity.ai Search for the Top influencers and their latest posts...")
        influencers_and_posts = self.get_influencers_and_posts(region, subject)
        print("\nInfluencers and Their Latest Posts:")
        print(influencers_and_posts)

        retries = 0
        while retries < self.max_retries:
            article_content = self.generate_article(summaries, subject, article_length, influencers_and_posts)
            title = self.generate_title(subject, article_content)
            summary = self.generate_summary(article_content)

            approved = self.write_article(article_content, title, summary)
            if approved:
                break
            retries += 1

        if not approved:
            print("Max retries reached. Article not published.")


# Usage example
cookies_file = '.li_session'

article_writer = LinkedInArticleWriter(cookies_file)
article_writer.run()
