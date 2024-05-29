# LinkedIn GTM Toolkit (Preview)

This repository contains a collection of Python scripts that automate various tasks related to LinkedIn GTM (Go-to-Market) activities. These scripts leverage the Anthropic API, OpenAI API, Perplexity.ai API, and Playwright library to perform tasks such as data ingestion, enrichment, content scraping, article writing, and engagement.

This repository is a preview version of this project. It is not actively maintained, and no warranties nor support is provided.

## How to Start

To get started with the LinkedIn GTM Automation Scripts, follow these steps:

1. Make sure you have Git installed on your system. If you don't have Git installed, you can download it from the official website: [https://git-scm.com/downloads](https://git-scm.com/downloads)

2. Clone the repository to your local machine using the following command:


```
git clone https://github.com/dr-robert-li/ai-gtm-toolkit.git
```

3. Navigate to the cloned repository directory:


```
cd ai-gtm-toolkit
```

4. Open a terminal or command prompt to run the scripts. Here are some options for different operating systems:
- Windows:
  - Command Prompt: Press `Win + R`, type `cmd`, and press `Enter`.
  - PowerShell: Press `Win + X`, select "Windows PowerShell" or "Windows Terminal".
  - Git Bash: If you installed Git, you can use Git Bash as a terminal. Right-click inside the repository folder and select "Git Bash Here".
  - Windows Terminal (recommended): Download and install [Windows Terminal](https://www.microsoft.com/en-us/p/windows-terminal/9n0dx20hk701) from the Microsoft Store for an enhanced terminal experience on Windows.
  - Cmder: Download and install [Cmder](https://cmder.net/), a popular terminal emulator for Windows.
- macOS:
  - Terminal: Press `Cmd + Space`, type "Terminal", and press `Enter`.
  - iTerm2 (recommended): Download and install [iTerm2](https://iterm2.com/) for an enhanced terminal experience on macOS.

5. Proceed with the setup and usage instructions below.

## Requirements

- Python 3.7 or higher
- `pip` package manager
- You will need to provide your own API keys for Anthropic, OpenAI, Perplexity.ai, and Apollo.io

## Setup

1. Create a virtual environment:


```
python -m venv venv
```

2. Activate the virtual environment:
- For Windows:
  ```
  venv\Scripts\activate
  ```
- For macOS and Linux:
  ```
  source venv/bin/activate
  ```

3. Install the required dependencies:


```
pip install -r requirements.txt
```

4. You will then need to initialize Playwright so that it can install the required browser clients:

```
playwright install
```

5. Create a `.env` file in the project root directory and provide the necessary API keys and credentials. Here's an example `.env` file:


```
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
APOLLO_API_KEY=your_apollo_api_key
```

# Usage

***Steps 1 to 4 must be done first and in order. Also note, that the `social_media_agent.py` is not ready to use yet.***

---
## Steps 1-3 - Ingesting and Enriching

### 1. `ingest.py`

This script allows you to ingest data from various file formats (CSV, XLSX, TXT, DOCX, PDF) and extract structured data using the Anthropic API. It separates the data into individuals and companies dataframes and saves them as `pkl` files. ***NOTE: it is much easier to handle files with filenames which don't contain spaces, are all lowercase, and don't contact special characters outside of the symbols: `.-_`***

Before ingesting you will need to organize your data into one of two structures:

For contacts all data needs to fall under three headers: ***Name, LinkedIn, Email***

For companies all data needs to fall under two headers: ***Company, Website***

To run the script:


```
streamlit run ingest.py
```

Questions:


```
Choose a file to upload for data ingestion.
```

### 2. `enrich_companies_data.py`

This script enriches the company data using the Apollo.io API. It retrieves additional information about the companies and saves the enriched data as a JSON file.

To run the script:


```
streamlit run enrich_companies_data.py
```

Questions:


```
Enter the role you want to search for in the enriched companies (default is 'CEO').
```

### 3. `enrich_individuals_data.py`

This script enriches the individual data using the Apollo.io API. It retrieves additional information about the individuals and saves the enriched data as a JSON file.

To run the script:


```
streamlit run enrich_individuals_data.py
```

Questions:


```
Enter the path to the individuals_data_enriched JSON file.
```

---

## Steps 4 Onwards - LinkedIn Workflow

***Note that some steps have a,b and c methods. These are to be used alternatively, not sequentially, nor concurrently.***

### 4. `class_li_login.py`

This script contains the `LinkedInLoginTool` class, which automates the process of logging into LinkedIn using the provided email and password. It saves the session cookies to a file named `.li_session`.

**Warning: The `.li_session` file generated by this script contains sensitive information. Make sure to keep this file and the folder containing it in protected storage and do not share it with anyone.**

To run the script:


```
python class_li_login.py
```

Questions:


```
Enter your LinkedIn email.
Enter your LinkedIn password.
```

### 5. `class_li_postscraper_v2.py`

This script contains the `LinkedInPostScraper` class, which scrapes LinkedIn posts from a given LinkedIn profile URL. It extracts the post links and saves them to a CSV file inside a subfolder: `./li_post_links_csv/`.

To run the script:


```
python class_li_postscraper_v2.py
```

Questions:


```
Enter the path to the file with LinkedIn Profile URLs.
```

### 6. `class_li_postcontentscraper_v2.py`

This script contains the `LinkedInPostContentScraper` class, which scrapes the content of LinkedIn posts from the CSV files generated by `class_li_postscraper_v2.py`. It adds the post content to the CSV files.


To run the script:


```
python class_li_postcontentscraper_v2.py
```

Questions:


```
Enter the folder path for li_post_links_csv containing *_li_posts.csv files.
Do you want to process all the CSV files? (y/n)
If not, enter the numbers of the CSV files you want to process (comma-separated).
```

### 7. `class_li_engagement_v2.py`

This script contains the `LinkedInCommentBot` class, which automates the process of engaging with LinkedIn posts. It reads post data from CSV files, generates comments using the Anthropic API, and posts the comments on the respective LinkedIn posts.

To run the script:


```
python class_li_engagement.py
```

Questions:


```
Enter the folder path for the li_post_links_csv folder containing *_li_posts.csv files.
Do you want to process all the CSV files? (y/n)
If not, enter the numbers of the CSV files you want to process (comma-separated).
Do you want to automatically approve responses? (y/n)
```

### 8a. `class_li_articlewriter.py`

This script contains the `LinkedInArticleWriter` class, which generates LinkedIn articles based on the keywords extracted from the enriched individual data. It uses the Anthropic API to generate the article content, title, and summary, and then publishes the article on LinkedIn.

To run the script:


```
python class_li_articlewriter.py
```

Questions:


```
Enter the path to the JSON file containing LinkedIn profiles.
Select a person to use their keywords as the article seed.
Do you approve the article? You will be given one more opportunity later to approve or disapprove (yes/no).
Do you want to publish the article? This is your final chance to approve or disapprove (yes/no).
```

### 8b. `class_li_articlewriter_v3.py`

This script is an alternative version of `class_li_articlewriter.py`. It uses the Perplexity.ai API to search for top articles and influencers related to a given subject and region. It then generates an SEO-optimized LinkedIn article using the Anthropic API and publishes it on LinkedIn.

To run the script:


```
python class_li_articlewriter_v3.py
```

Questions:


```
Enter the target region or country.
Enter the subject.
Enter the desired article length (in words, 500 is the recommended).
Do you approve the article? You will be given one more opportunity later to approve or disapprove (yes/no).
Do you want to publish the article? This is your final chance to approve or disapprove (yes/no).
```

### 8c. `class_li_articlewriter_v4.py`

This script is an alternative version of `class_li_articlewriter_V3.py`. It does the same thing except it now also uses DALL-E 3 to create a hero image and download/upload it for you.

To run the script:


```
python class_li_articlewriter_v4.py
```

Questions:


```
Enter the target region or country.
Enter the subject.
Enter the desired article length (in words, 500 is the recommended).
Do you approve the article? You will be given one more opportunity later to approve or disapprove (yes/no).
Do you want to publish the article? This is your final chance to approve or disapprove (yes/no).
```

### 9a. `class_li_connect.py`

This script contains the `LinkedInConnector` class, which automates the process of sending connection requests to individuals based on the data in the enriched JSON file.

To run the script:


```
python class_li_connect.py
```

Questions:


```
Enter the full path to the JSON file containing LinkedIn profiles.
Send connection request without a note to [profile_url]? (y/n)
```

### 9b. `class_li_connect_v2.py`

This script is an alternative version of `class_li_connect.py`. It contains the `LinkedInConnector` class, which automates the process of sending connection requests to individuals based on the data from a greater number of file formats and generic data structures as long as they contain LinkedIn profile URLs.


To run the script:


```
python class_li_connect_v2.py
```

Questions:


```
Enter the full path to the file containing LinkedIn profiles (JSON, XLS, XLSX, CSV, TXT, DOCX, PDF).
Do you want to auto-confirm connection requests? (y/n)
If not auto-confirming, send connection request without a note to [profile_url]? (y/n)
```

### 9c. `class_li_connect_v3.py`

This script contains the `LinkedInConnector` class, which automates the process of sending connection requests to individuals in the same way that `class_li_connect_v2.py` does. However, it also includes an option to generate a personalized note using the Anthropic API.

To run the script:


```
python class_li_connect_v3.py
```

Questions:


```
Enter the full path to the file containing LinkedIn profiles (JSON, XLS, XLSX, CSV, TXT, DOCX, PDF).
Do you want to auto-confirm connection requests? This will skip adding a note (y/n).
If not auto-confirming, do you want to add a note to the connection request? (y/n)
```

---

Note: Make sure to comply with LinkedIn's terms of service and respect the privacy of individuals while using these scripts.





