import BQ_Interact as BQ
import json
import re
from difflib import get_close_matches
import time

def normalize_name(name):
    # Lowercase and remove special characters for better matching
    return re.sub(r'\W+', '', name.lower())

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def match_companies(companies_urls, companies_cik):
    matched_companies = {}
    i = 0
    for company_url in companies_urls:
        i +=1
        company_name = company_url['bv_entity_name']
        normalized_name = normalize_name(company_name)
        print(f'{normalized_name}, {i} of {len(companies_urls)}')
        # Find closest match in the CIK list
    
        possible_matches = get_close_matches(normalized_name, [normalize_name(c['title']) for c in companies_cik], n=1, cutoff=0.9)
       # if len(possible_matches) > 1:
       #     print(possible_matches)
       #     h1= input('Continue?')
        if possible_matches:
            match_name = possible_matches[0]
            # Find the CIK code associated with the matched name
            cik_entry = next((c for c in companies_cik if normalize_name(c['title']) == match_name), None)
            if cik_entry:
                matched_companies[company_name] = cik_entry['cik_str']

    return matched_companies

def main():
    #query = """ 
    #select t.bv_entity_domain,bv_entity_name from `tf-scoring-dev-ac2c.usna_capstone.count_entity_ransom_hits_1T` as t join `tf-scoring-dev-ac2c.usna_capstone.entity_master_20250117` as b on t.bv_entity_domain = b.bv_entity_domain where t.hits >= 1 and hits != 1456 order by hits desc
    #"""
    #top100 = BQ.run_query(query)

    # Load JSON files
    companies_urls = load_json('topEnt.json') # Replace with actual file path
    companies_cik = load_json('cik.json') # Replace with actual file path
    print('read jsons')
    # Match companies
    matched_companies = match_companies(companies_urls, companies_cik)

    # Get the first 100 companies
    #first_100_companies = dict(list(matched_companies.items())[:100])

    # Save the first 100 companies
    with open('first100.json', 'w') as file:
        json.dump(matched_companies, file)

if __name__ == '__main__':
    main()
