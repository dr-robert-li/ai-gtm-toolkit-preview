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

def enrich_individual_data(individual_data):
    print("Enriching individual data using Apollo.io...")
    enriched_data = []
    
    for _, row in individual_data.iterrows():
        first_name = row['Name'].split()[0] if pd.notna(row['Name']) else None
        last_name = ' '.join(row['Name'].split()[1:]) if pd.notna(row['Name']) else None
        email = row['Email'] if pd.notna(row['Email']) else None
        linkedin_url = row['LinkedIn'] if pd.notna(row['LinkedIn']) else None
        
        print(f"Making a request to the Apollo.io People Enrichment endpoint for: {first_name} {last_name}")
        # Make a request to the Apollo.io People Enrichment endpoint
        url = "https://api.apollo.io/v1/people/match"
        data = {
            "api_key": api_key,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "linkedin_url": linkedin_url,
            "reveal_personal_emails": True
        }
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"Successfully retrieved enriched data for: {first_name} {last_name}")
            enriched_individual_data = response.json()
            enriched_data.append(enriched_individual_data)
        else:
            print(f"Error enriching data for: {first_name} {last_name}")
    
    print("Finished enriching individual data.")
    return enriched_data

def main():
    print("Loading individuals_data dataframe from the pickle file...")
    # Load the individuals_data dataframe from the pickle file
    with open("individuals_data.pkl", "rb") as file:
        individuals_data = pickle.load(file)
    
    print("Enriching the individual data using Apollo.io...")
    # Enrich the individual data using Apollo.io
    enriched_data = enrich_individual_data(individuals_data)
    
    print("Displaying the head of the enriched_data:")
    print(pd.DataFrame(enriched_data).head())
    
    # Get the current epoch time
    epoch_time = int(time.time())
    
    # Create the file name with the epoch time
    file_name = f"individuals_data_enriched_{epoch_time}.json"
    
    print(f"Saving the enriched_data to {file_name}...")
    # Save the enriched_data to a JSON file with the epoch time in the name
    with open(file_name, "w") as file:
        json.dump(enriched_data, file, indent=2)
    
    print(f"Enriched individuals_data saved to '{file_name}'")


if __name__ == '__main__':
    print("Starting the main function...")
    main()
    print("Script execution completed.")
