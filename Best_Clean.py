import requests
import re
from bs4 import BeautifulSoup
import json
import time
import os
import BQ_Interact as BQ

# Credentials for requests
email = 'gabriel.abreu@bluevoyant.com'
header = {'User-Agent': email}

def download_cik_data():
    """Fetch CIK data from the SEC's JSON file."""
    url = 'https://www.sec.gov/files/company_tickers.json'
    response = requests.get(url, headers=header)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to download CIK data. Status code: {response.status_code}")

def match_domain_to_cik(domain_list, cik_data):
    """Match domains to CIK codes using regex."""
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

def extract_plain_text(html_content):
    """Extract plain text from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    return [tag.get_text() for tag in soup.find_all('font') if 'Item 1.05 Material Cybersecurity Incidents' in tag.get_text()]

def request_with_retry(url, headers, retries=3, backoff=5):
    """Send an HTTP request with retries in case of rate limiting."""
    for attempt in range(retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        elif response.status_code == 429:  # Too many requests (rate limit)
            print("Rate limit reached. Waiting for {} seconds...".format(backoff))
            time.sleep(backoff)
        else:
            response.raise_for_status()
    raise Exception(f"Failed to fetch URL after {retries} retries.")

def get_8Ks(cik_dict):
    """Retrieve 8-K filings for the given CIK dictionary."""
    base_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    filings = []
    for i, cik_code in enumerate(cik_dict.values()):
        print(f"Exploring {i + 1} of {len(cik_dict)}: {cik_code}")

        page_num = 1
        while True:
            url = f'{base_url}?action=getcompany&CIK={cik_code}&type=8-K&dateb=&owner=exclude&count=100&start={(page_num - 1) * 100}'
            response = request_with_retry(url, header)
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='tableFile2')

            if not table:
                print("No filings found for this CIK.")
                break

            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) > 3:
                    link = cols[1].find('a')
                    if link:
                        filing_url = 'https://www.sec.gov' + link.get('href')
                        filing_response = request_with_retry(filing_url, header)
                        filing_soup = BeautifulSoup(filing_response.content, 'html.parser')
                        text_content = filing_soup.get_text()

                        if 'cybersecurity' in text_content.lower():
                            sentences = get_next_10_sentences(text_content, 'cybersecurity')
                            if sentences:
                                combined_string = ' '.join(item.replace('\n', ' ') for item in sentences)
                                filings.append(combined_string)

            if len(table.find_all('tr')[1:]) < 100:
                break

            page_num += 1
            print(f"Moving to page {page_num}")

    return filings

def get_next_10_sentences(text, phrase):
    """Get the next 10 sentences after the given phrase."""
    sentence_endings = re.compile(r'(?<=[.!?]) +')
    sentences = sentence_endings.split(text)
    
    for i, sentence in enumerate(sentences):
        if phrase in sentence.lower():
            return sentences[i + 1:i + 11]
    return []

def append_to_json_file(file_path, new_key, new_value):
    """Append data to a JSON file."""
    try:
        data = {}
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    if not isinstance(data, dict):
                        data = {}
                except json.JSONDecodeError:
                    pass
        
        if new_key in data:
            data[new_key] = f"{data[new_key]} {new_value}"
        else:
            data[new_key] = new_value
        
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        print("Key-value pair appended successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

def scrape():
    """Run the scraping process."""
    query = "SELECT entity_domain, entity_name FROM `usna_capstone.Hit_Table_1`"
    try:
        cik_data = download_cik_data()
        print("CIK data downloaded successfully.")
        domain_list = BQ.run_query(query)
        print("Domain list downloaded successfully.")
        matched_data = match_domain_to_cik(domain_list, cik_data)
        print('Domains matched to CIKs.')
        return matched_data
    except Exception as e:
        print(f"Error during scraping: {e}")
        return {}

def upload_scrape(cleaned_data):
    """Upload the scraped data to a file."""
    try:
        filings = get_8Ks(cleaned_data)
        with open('scrape_data.txt', 'w') as file:
            json.dump(filings, file)
        print("Scrape data uploaded successfully.")
    except Exception as e:
        print(f"Error during scrape upload: {e}")

if __name__ == "__main__":
    with open('first100.json', 'r') as file:
        loaded_dict = json.load(file)
    
    # Process first 10 items for example
    loaded_dict = dict(list(loaded_dict.items())[0:10])
    upload_scrape(loaded_dict)
