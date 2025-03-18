import requests
from bs4 import BeautifulSoup
import time

# Function to get the URL for the latest 8-K filings for a given CIK
def get_filings_url(cik, filing_type='8-K'):
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        'action': 'getcompany',
        'CIK': cik,
        'type': filing_type,
        'output': 'xml',  # We can get XML data for easy parsing
        'count': 100,  # The number of results per request
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve data for CIK {cik}")
        return None

# Function to extract document links from the SEC XML response
def extract_document_links(xml_data):
    soup = BeautifulSoup(xml_data, 'lxml')
    filings = soup.find_all('entry')
    document_links = []
    
    for filing in filings:
        doc_url = filing.find('link')['href']
        document_links.append(doc_url)
    
    return document_links

# Function to scrape the actual 8-K filing document
def scrape_8k_document(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract all text content (e.g., the full text of the filing)
        text_content = soup.get_text()
        return text_content.strip()
    else:
        print(f"Failed to retrieve 8-K document at {url}")
        return None

# Main function to get and scrape all 8-K filings for a given CIK
def scrape_8k_filings(cik):
    print(f"Scraping 8-K filings for CIK: {cik}")
    
    # Step 1: Get filings XML data
    filings_xml = get_filings_url(cik)
    if filings_xml is None:
        return
    
    # Step 2: Extract all document URLs (links to the 8-K filings)
    document_links = extract_document_links(filings_xml)
    if not document_links:
        print("No 8-K filings found for the given CIK.")
        return
    
    # Step 3: Scrape and print each 8-K document
    for link in document_links:
        print(f"Scraping 8-K document: {link}")
        filing_text = scrape_8k_document(link)
        
        if filing_text:
            print(f"Document Content: \n{filing_text[:1000]}...")  # Print the first 1000 chars of the filing
        time.sleep(1)  # Delay between requests to avoid hitting the server too frequently

if __name__ == "__main__":
    cik_code = input("Enter the CIK code: ")
    scrape_8k_filings(cik_code)