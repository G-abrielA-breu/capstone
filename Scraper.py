###### LIBRARIES
import requests
import csv
import re
import yfinance as yf
from bs4 import BeautifulSoup
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import sys
from tqdm import tqdm
import time

###### SCRIPTS 
import BQ_Interact as BQ
import Scraper as SC


### CREDENTIALS FOR SCRAPE
email= 'gabriel.abreu@bluevoyant.com'
header = {'User-Agent': f'{email}'}


#### get cik codes: in-(), out-(list of cik codes)
def download_cik_data():
    url = 'https://www.sec.gov/files/company_tickers.json'
    response = requests.get(url,headers=header)
    #print(response) ## need user header 
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to download CIK data")

#### matches domains to cik codes: in-(domain list, cik codes list), out-dictionary of domains to cik codes) 
def match_domain_to_cik(domain_list, cik_data):
    domain_to_cik = {}
    for domain in domain_list:
        pattern = re.compile(rf"{domain.split('.')[0]}", re.IGNORECASE)
        for item in cik_data.values():
            company_name = item['title']
            if pattern.search(company_name):
                domain_to_cik[domain] = item['cik_str']
                break
            else: 
                domain_to_cik[domain] = "Not Found"
    return domain_to_cik

#### get plane text from a scrape 

def extract_plain_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator='\n', strip=True)


#### get 8ks for a given list of cik codes 
def get_8Ks(cik):
    
    for code in cik:
        base_url= f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=exclude&start=0&count=100'
    
        # Fetch the list of filings for the CIK
        response = requests.get(base_url, headers=header)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all document links
        tot =len(soup.find_all('a', href=True))
        i = 0
        for link in soup.find_all('a', href=True):
            i+=1
            print(f'Exploring {i} of {tot}')
    
            if '/Archives/edgar/data/' in link['href']:
                filing_url = 'https://www.sec.gov' + link['href']
                filing_response = requests.get(filing_url, headers=header)
                filing_soup = BeautifulSoup(filing_response.content, 'html.parser')
            
                # Find text files or relevant sections
                for filing_link in filing_soup.find_all('a', href=True):
                    if filing_link['href'].endswith('.txt'):
                        doc_url = 'https://www.sec.gov' + filing_link['href']
                    
                        doc_response = requests.get(doc_url, headers=header)
                        text_content = extract_plain_text(doc_response.content)
                    
                        if 'Item 1.05 Material Cybersecurity Incidents' in text_content:
                            print(f"Found '1.05' in: {doc_url}")
                            #sys.exit()
                            #print(text_content)  # Print or process the plain text as needed
                            sys.exit()


def scrape():
    l_cik=[]
    query = """
    select entity_domain,entity_name from `usna_capstone.Hit_Table_1`
    """
    try:
        cik_data = download_cik_data()
        print("Status: downloaded CIKs")
        l_domains = BQ.run_query(query)  #BQ.run_query()
        print("Status: downloaded domains")
        matched_data = match_domain_to_cik(l_domains, cik_data)
        for domain, cik in matched_data.items():
            #print(f"Domain: {domain}, CIK: {cik}")
            l_cik.append(cik)
        print(f'Status: domains matched to CIKs')
        return l_cik
    except Exception as e:
        print(e)

def clean(l_cik):
    cleaned_data=[]
    try:
        print('here1')
        return cleaned_data
    except:
        print('here 2')

def upload_scrape(cleaned_data):
    Hit_Table=[]
    try: 
        for cik in cleaned_data:
            Hit_Table.append(get_8Ks(cik))
            print(Hit_Table[0])
    except Exception as e:
        print(e)

def run():
    l_cik = scrape()
    cleaned_data = clean(l_cik)
    upload_scrape(cleaned_data)
    
