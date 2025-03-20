###### LIBRARIES
import requests
import re
from bs4 import BeautifulSoup
import json
import time

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
    # Define the SEC EDGAR base URL for AT&T's 8-K filings
    for c in cik_dict:
        if c == '':
            continue
        print(f'Exploring {c} ')
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
            
            # If no table is found, we have reached the end of the pages
            if not table:
                print("No more filings found.")
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
                        #print(filing_url)
                        # Check the filing details for the phrase "1.05 material"
                        filing_response = requests.get(filing_url, headers=header)
                        filing_response.raise_for_status()  # Ensure successful request

                        # Parse the content of the filing
                        filing_soup = BeautifulSoup(filing_response.content, 'html.parser')
                        text_content = filing_soup.get_text()
                        #print(text_content)
                        urP = re.findall(r'\b.*\.htm\b', text_content)
                        pth = filing_url.rfind("/")
                        #print(pth)
                        #print(filing_url[:pth+1])
                        #print(urP)
                        for ur in urP:
                            try:
                                fin_url = filing_url[:pth+1] + urP[0]
                                fin_response = requests.get(fin_url, headers=header)
                                fin_response.raise_for_status()  # Ensure successful request
                                fin_soup = BeautifulSoup(fin_response.content, 'html.parser')
                                text_content = fin_soup.get_text()
                                #print(fin_url)
                                #time.sleep(1000)
                                # Search for the phrase "1.05 material" in the filing
                                if '1.05 material' in text_content.lower():
                                    #print(text_content)
                                    #print(fin_url)
                                    relevant_filings[cik_code]=(text_content,fin_url)
                            except: 
                                print('Error', fin_url)
                                continue
            
            # Check if we've found fewer than 100 filings, indicating we're on the last page
            if len(table.find_all('tr')[1:]) < count:
                break
            
            # Move to the next page
            page_num += 1
            print(page_num)
            # Sleep for a bit to avoid overwhelming the server (rate limiting)
        # time.sleep(1)

        # If relevant filings are found, save them to a CSV file
        if relevant_filings:
            with open('scrape_data.txt', 'a') as file:
                json.dump(relevant_filings, file)
            print(f"Found {len(relevant_filings)} relevant 8-K filings containing '1.05 material'. Saved to 'att_8k_filings_1_05_material_all.csv'.")
        else:
            print("No 8-K filings containing '1.05 material' found for AT&T.")
    print(f'Finished {c}')
    return 

def scrape():
    query = """
    SELECT entity_domain, entity_name FROM `usna_capstone.Hit_Table_1`
    """
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
    with open('domCik.txt', 'w') as file:
        json.dump(cleaned_data, file)

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
    with open('domCik.txt', 'r') as file:
        loaded_dict = json.load(file)
        #print(loaded_dict)
    upload_scrape(loaded_dict)

