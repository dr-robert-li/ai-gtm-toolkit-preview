import streamlit as st
import pandas as pd
import os
import docx
import pickle
from PyPDF2 import PdfReader  # Updated import statement
from anthropic import Client
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Get the Anthropic API key from the environment variable
api_key = os.getenv("ANTHROPIC_API_KEY")

# Create an instance of the Anthropic client
client = Client(api_key=api_key)

def read_file(file):
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension == '.csv':
        data = pd.read_csv(file)
    elif file_extension == '.xlsx':
        data = pd.read_excel(file)
    elif file_extension in ['.txt', '.docx', '.pdf']:
        if file_extension == '.txt':
            with open(file.name, 'r') as f:
                text = f.read()
        elif file_extension == '.docx':
            doc = docx.Document(file)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_extension == '.pdf':
            pdf_reader = PdfReader(file)  # Updated class name
            text = '\n'.join([pdf_reader.pages[i].extract_text() for i in range(len(pdf_reader.pages))])  # Updated method name
        
        # Use Claude 3 to extract structured data from the text
        prompt = f"\n\nPlease extract individuals and companies data from the following text:\n\n{text}\n\nIndividuals data should include Name, Email, and LinkedIn. Companies data should include Company and Website."
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0,
            system="You are a helpful AI that extracts structured data from text.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response = message.content[0].text  # Extract the text content from the ContentBlock object
        print(response)

        individuals_data = pd.DataFrame(columns=['Name', 'Email', 'LinkedIn'])
        companies_data = pd.DataFrame(columns=['Company', 'Website'])

        lines = response.split('\n')  # Split the response into lines
        for line in lines:
            if 'Name:' in line:
                name = line.split('Name:')[1].strip()
                email = ''
                linkedin = ''
                for subline in lines[lines.index(line)+1:]:
                    if 'Email:' in subline:
                        email = subline.split('Email:')[1].strip()
                    if 'LinkedIn:' in subline:
                        linkedin = subline.split('LinkedIn:')[1].strip()
                    if 'Name:' in subline or 'Company:' in subline:
                        break
                individuals_data = pd.concat([individuals_data, pd.DataFrame({'Name': [name], 'Email': [email], 'LinkedIn': [linkedin]})], ignore_index=True)
            elif 'Company:' in line:
                company = line.split('Company:')[1].strip()
                website = ''
                for subline in lines[lines.index(line)+1:]:
                    if 'Website:' in subline:
                        website = subline.split('Website:')[1].strip()
                    if 'Name:' in subline or 'Company:' in subline:
                        break
                companies_data = pd.concat([companies_data, pd.DataFrame({'Company': [company], 'Website': [website]})], ignore_index=True)

        data = pd.concat([individuals_data, companies_data], ignore_index=True)

    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    return data

def split_data(data):
    individuals_columns = ['Name', 'Email', 'LinkedIn']
    companies_columns = ['Company', 'Website']
    
    # Strip whitespace from column names
    data.columns = [col.strip() for col in data.columns]
    
    # Use Claude 3 to match the found column headers to the expected columns
    prompt = f"\n\nGiven the following column headers from the data:\n\n{', '.join(data.columns)}\n\nYou must match each of them to one of the expected individuals columns verbatim: {', '.join(individuals_columns)}\nAnd to one of the expected companies columns verbatim: {', '.join(companies_columns)}\n\nProvide the mapping in the format 'Found Column: Expected Column' for each match.\n\nThe expected LinkedIn column must be matched to data which contains the string: linkedin or LinkedIn\n\nIf a match is not found then provide no data."
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        temperature=0,
        system="You are a helpful AI that matches column headers.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response = message.content[0].text  # Extract the text content from the ContentBlock object
    print(response)

    column_mapping = {}
    lines = response.split('\n')  # Split the response into lines
    for line in lines:
        if ':' in line:
            found_column, expected_column = line.split(':')
            column_mapping[found_column.strip()] = expected_column.strip()

    individuals_data = pd.DataFrame(columns=individuals_columns)
    companies_data = pd.DataFrame(columns=companies_columns)

    for found_column, expected_column in column_mapping.items():
        if expected_column in individuals_columns:
            individuals_data[expected_column] = data[found_column].apply(lambda x: x.strip() if isinstance(x, str) else x).fillna('')
        elif expected_column in companies_columns:
            companies_data[expected_column] = data[found_column].apply(lambda x: x.strip() if isinstance(x, str) else x).fillna('')

    individuals_data = individuals_data.dropna(subset=['Name'])
    companies_data = companies_data.dropna(subset=['Company'])

    return individuals_data, companies_data


def main():
    st.title("Lead Data Ingestion")
    
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'txt', 'docx', 'pdf'])
    
    if uploaded_file is not None:
        try:
            data = read_file(uploaded_file)
            individuals_data, companies_data = split_data(data)
            
            if not individuals_data.empty:
                st.subheader("Individuals Data")
                st.dataframe(individuals_data.head())
                individuals_data.to_pickle("individuals_data.pkl")
                st.success("Individuals data saved to 'individuals_data.pkl' (overwritten if already exists)")
            
            if not companies_data.empty:
                st.subheader("Companies Data")
                st.dataframe(companies_data.head())
                companies_data.to_pickle("companies_data.pkl")
                st.success("Companies data saved to 'companies_data.pkl' (overwritten if already exists)")
            
            if individuals_data.empty and companies_data.empty:
                st.warning("No valid data found for individuals or companies.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == '__main__':
    main()