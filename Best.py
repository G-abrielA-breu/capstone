###### LIBRARIES
import requests
import re
from bs4 import BeautifulSoup
import json
import time
import os

###### SCRIPTS 
import BQ_Interact as BQ

### CREDENTIALS FOR SCRAPE
email = 'gabriel.abreu@bluevoyant.com'
header = {'User-Agent': email}

#### Fetch CIK codes
def download_cik_data():
    url = 'https://www.sec.gov/files/company_tickers.json'
    response = requests.get(url, headers=header)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to download CIK data. Status code: {response.status_code}")

#### Match domains to CIK codes
def match_domain_to_cik(domain_list, cik_data):
    domain_to_cik = {}
    total_domains = len(domain_list)

    for idx, domain in enumerate(domain_list):
        pattern = re.compile(rf"{domain.split('.')[0]}", re.IGNORECASE)
        for item in cik_data.values():
            if pattern.search(item['title']):
                domain_to_cik[domain] = item['cik_str']
                break
        if (idx + 1) % 100 == 0 or (idx + 1) == total_domains:
            print(f'{idx + 1} of {total_domains}')
    return domain_to_cik

#### Extract plain text from HTML
def extract_plain_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return [tag.get_text() for tag in soup.find_all('font') if 'Item 1.05 Material Cybersecurity Incidents' in tag.get_text()]

#### Retrieve 8-K filings for CIK codes
def get_8Ks(cik_dict):
    base_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    email= 'gabriel.abreu@bluevoyant.com'
    header = {'User-Agent': f'{email}'}
    # Define the SEC EDGAR base URL for cik's 8-K filings
    i=1
    
    for c in cik_dict:
        l=[]
        first = 0
        if c == '':
            continue
        print(f'Exploring {c}, {i} of {len(cik_dict)}')
        i+=1
        # Initialize a list to store the relevant filings
        relevant_filings = {}
        # Set the CIK code for AT&T
        cik_code = cik_dict[c]
        # Define the number of filings per page (100 is the maximum)
        count = 100
        # Start with the first page of filings
        page_num = 1
        while True:
            # Construct the URL for the current page of filings
            url = f'{base_url}?action=getcompany&CIK={cik_code}&type=8-K&dateb=&owner=exclude&count={count}&start={(page_num - 1) * count}'
            # Send a request to the SEC EDGAR page
            response = requests.get(url, headers=header)
            response.raise_for_status()  # Check if the request was successful
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')
            # Find the table containing filing details
            table = soup.find('table', class_='tableFile2')
            if table == '':
                print("No 8-K filings found.")
                first = 1
                url = f'{base_url}?action=getcompany&CIK={cik_code}&type=6-K&dateb=&owner=exclude&count={count}&start={(page_num - 1) * count}'
                response = requests.get(url, headers=header)
                #response.raise_for_status()  # Check if the request was successful
                if response.status_code == 429:
                    print("Rate limit reached. Waiting for 100 seconds...")
                    time.sleep(100)
                    response = requests.get(url, headers=header)   
                # Parse the HTML content of the page
                soup = BeautifulSoup(response.content, 'html.parser')
                # Find the table containing filing details
                table = soup.find('table', class_='tableFile2')
                # If no table is found, we have reached the end of the pages
                print(table)
                if table == '':
                    print("No 6-K filings found.")
                    #first = 0
                    break
            # Loop through each row in the table, skipping the header row
            for row in table.find_all('tr')[1:]:
                # Get all the columns in the row
                cols = row.find_all('td')
                if len(cols) > 3:  # Ensure the row has enough columns
                    # The second column contains the link to the filing
                    link = cols[1].find('a')
                    if link:
                        filing_url = 'https://www.sec.gov' + link.get('href')
                       
                        filing_response = requests.get(filing_url, headers=header)
                        filing_response.raise_for_status()  # Ensure successful request
                        # Parse the content of the filing
                        filing_soup = BeautifulSoup(filing_response.content, 'html.parser')
                        text_content = filing_soup.get_text()
                        urP = re.findall(r'\b.*\.htm\b', text_content)
                        pth = filing_url.rfind("/")
                        for ur in urP:
                            try:
                                fin_url = filing_url[:pth+1] + urP[0]
                                fin_response = requests.get(fin_url, headers=header)
                                fin_response.raise_for_status()  # Ensure successful request
                                fin_soup = BeautifulSoup(fin_response.content, 'html.parser')
                                text_content = fin_soup.get_text()
                                # Search for the phrase "cybersecurity" in the filing
                                if 'cybersecurity' in text_content.lower():
                                    text_sentences = get_next_10_sentences(text_content.lower(), 'cybersecurity')
                                    combined_string = ' '.join(item.replace('\n', ' ') for item in text_sentences)
                                    print(combined_string)
                                    pattern = r'\b\S*\\\S*\b'
                                    result = re.sub(pattern, '', combined_string)
                                    combined_string = re.sub(r'\s+', ' ', result).strip()                           
                                    l.append(combined_string)
                                else:
                                   continue
                            except: 
                                print('Error', fin_url)
                                continue
            # Check if we've found fewer than 100 filings, indicating we're on the last page
            if len(table.find_all('tr')[1:]) < count:
                break
            # Move to the next page
            page_num += 1
            print(page_num)
        #print(l)
        joined_string = " ".join(l)
        print(joined_string)
        #input('Continue?')
        if joined_string != '':
            append_to_json_file('nameText.json', cik_code, joined_string)
    print(f'Finished {c}')
    return 

def get_next_10_sentences(text, phrase):
    # Define a regular expression pattern for splitting text into sentences
    sentence_endings = re.compile(r'(?<=[.!?]) +')
    # Split the text into sentences
    sentences = sentence_endings.split(text)  
    # Initialize an empty list to store the results
    result_sentences = []   
    # Loop through sentences to find the phrase
    for i, sentence in enumerate(sentences):
        if phrase in sentence:
            # If the phrase is found, get the next 10 sentences
            result_sentences = sentences[i+1:i+16]
            break
    return result_sentences

def append_to_json_file(file_path, new_key, new_value):
    try:
        # Step 1: Check if the file exists and load the data
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    if not isinstance(data, dict):
                        print("The JSON file does not contain a dictionary. Starting a new dictionary.")
                        data = {}
                except json.JSONDecodeError:
                    print("Invalid JSON format. Starting a new dictionary.")
                    data = {}
        else:
            print("The file does not exist. Starting a new dictionary.")
            data = {}

        # Step 2: Check if the key exists and handle it
        if new_key in data:
            # Combine existing and new values into a single string
            existing_value = str(data[new_key])
            new_value = str(new_value)
            combined_value = existing_value + ' ' + new_value
            data[new_key] = combined_value
        else:
            # Append the new key-value pair
            data[new_key] = new_value

        # Step 3: Save the updated dictionary back to the JSON file
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        print("Key-value pair appended successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")


def scrape():
    query = """ SELECT entity_domain, entity_name FROM `usna_capstone.Hit_Table_1` """
    try:
        cik_data = download_cik_data()
        print("Status: downloaded CIKs")
        domain_list = BQ.run_query(query)
        print("Status: downloaded domains")
        matched_data = match_domain_to_cik(domain_list, cik_data)
        print('Status: domains matched to CIKs')
        return matched_data
    except Exception as e:
        print(f"Error during scraping: {e}")

def upload_scrape(cleaned_data):
    print("Status: Uploading Scrape")
    try:
        hit_table = get_8Ks(cleaned_data)
    except Exception as e:
        print(f"Error in get_8Ks: {e}")

    with open('scrape_data.txt', 'w') as file:
        json.dump(hit_table, file)

if __name__ == "__main__":
     # STEP 1
    #matched_cik_data = scrape()
    #with open('domCik.txt', 'w') as file:
     #  json.dump(matched_cik_data, file)

    # STEP 2
    with open('first100.json', 'r') as file:
        loaded_dict = json.load(file)
    loaded_dict = dict(list(loaded_dict.items())[90:100])
    upload_scrape(loaded_dict)

