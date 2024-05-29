import os
import json
import pickle
import requests
import time
import pandas as pd
from dotenv import load_dotenv

print("Loading environment variables from .env file...")
# Load environment variables from .env file
load_dotenv()

print("Getting the Apollo.io API key from the environment variable...")
# Get the Apollo.io API key from the environment variable
api_key = os.getenv("APOLLO_API_KEY")

def enrich_company_data(company_data):
    print("Enriching company data using Apollo.io...")
    enriched_data = []
    
    for _, row in company_data.iterrows():
        website = row['Website']
        
        print(f"Making a request to the Apollo.io Organization Enrichment endpoint for domain: {website}...")
        # Make a request to the Apollo.io Organization Enrichment endpoint
        url = "https://api.apollo.io/v1/organizations/enrich"
        querystring = {
            "api_key": api_key,
            "domain": website
        }
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            print(f"Successfully retrieved enriched data for domain: {website}")
            enriched_company_data = response.json()
            enriched_company_data['website'] = website  # Add the 'website' key to the enriched data
            enriched_data.append(enriched_company_data)
        else:
            print(f"Error enriching data for domain: {website}")
    
    print("Finished enriching company data.")
    return enriched_data

def find_person_by_role(domain, role):
    print(f"Finding {role} for domain: {domain}...")
    url = "https://api.apollo.io/v1/mixed_people/search"
    data = {
        "api_key": api_key,
        "q_organization_domains": domain,
        "page": 1,
        "per_page": 100,
        "person_titles": [role]
    }
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"Successfully retrieved {role} data for domain: {domain}")
        return response.json()
    else:
        print(f"Error retrieving {role} data for domain: {domain}")
        return None

def main():
    print("Loading company_data dataframe from the pickle file...")
    # Load the company_data dataframe from the pickle file
    with open("companies_data.pkl", "rb") as file:
        company_data = pickle.load(file)
    
    print("Enriching the company data using Apollo.io...")
    # Enrich the company data using Apollo.io
    enriched_data = enrich_company_data(company_data)
    
    print("Displaying the head of the enriched_data dataframe:")
    print(pd.DataFrame(enriched_data).head())
    
    print("Loading individuals_data dataframe from the pickle file...")
    # Load the individuals_data dataframe from the pickle file
    with open("individuals_data.pkl", "rb") as file:
        individuals_data = pickle.load(file)
    
    role = input("Company Data enriched, now enter the role you want to search for in the enriched companies - this will be appended to individual data (default is 'CEO'): ") or "CEO"
    print(f"Searching for {role} for each company...")
    
    for company in enriched_data:
        website = company['website']
        person_data = find_person_by_role(website, role)
        
        if person_data:
            for person in person_data['people']:
                name = person.get('name')
                email = person.get('email')
                linkedin_url = person.get('linkedin_url')
                
                if name and (email or linkedin_url):
                    print(f"Appending {role} data for domain: {website}")
                    individuals_data = individuals_data.append({
                        'name': name,
                        'email': email,
                        'linkedin_url': linkedin_url
                    }, ignore_index=True)
    
    print("Displaying the head of the updated individuals_data dataframe:")
    print(individuals_data.head())
    
    print("Saving the updated individuals_data to the existing pickle file...")
    # Save the updated individuals_data to the existing pickle file
    with open("individuals_data.pkl", "wb") as file:
        pickle.dump(individuals_data, file)
    
    print("Updated individuals_data saved to 'individuals_data.pkl'")

if __name__ == '__main__':
    print("Starting the main function...")
    main()
    print("Script execution completed.")