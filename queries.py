############ Premade QUERIES 

total_reset= '''drop table `tf-scoring-dev-ac2c.usna_capstone.Hit_Table_1`,Entity_Quality_1,source_counts_1'''



#Table of ransomes scraped from each source
create_source_counts= '''
create table `tf-scoring-dev-ac2c.usna_capstone.source_counts_1` as 
select distinct ransomware_source, count(*) as freq,
min(observed_ts) as min_observed_ts,
max(observed_ts) as max_observed_ts
from `tf-scoring-dev-ac2c.usna_capstone.ransomware_scraped_data`
group by ransomware_source'''



join_entity_ransome = '''
SELECT bv_entity_domain,entity_domain FROM `tf-scoring-dev-ac2c.usna_capstone.entity_master_20250117` LEFT JOIN `tf-scoring-dev-ac2c.usna_capstone.ransomware_scraped_data` ON bv_entity_domain = entity_domain
'''

### scrap
#-- count of rows in ransomeware with same domain
#--select entity_domain, count(entity_domain) as hits from `tf-scoring-dev-ac2c.usna_capstone.ransomware_scraped_data` group by entity_domain order by hits desc


### HIT TABLE is a table of companies that are found in the ransome table based on domain
### intent is to embed these rows and cluster

create_Hit= '''
create table `tf-scoring-dev-ac2c.usna_capstone.Hit_Table_1` (
  bv_id string, 
  entity_domain string, 
  entity_name string,
  num_hits int64,
  num_employees string, 
  revenue string,
  naics_code string,
  industry_code string,
  city string, -- make city into unque nums, 0 OCONUS
  state string, -- make state into unique nums, 0 OCONUS
  country string, -- 0 or 1
  total_ips integer,
  total_domains integer,
  net_ranges integer,
  ransome_source string,
  ransome_upload_ts timestamp,
  ransome_scraped_ts timestamp,
  is_alerted integer
)
'''


### INSERT into Hit_Table1
### this is the main table where we store all relvant entity data. Intent is to clean it (only nums: categories or ranges) before clustering

insert_Hit = '''
insert into `tf-scoring-dev-ac2c.usna_capstone.Hit_Table_1` 
(
  bv_id, 
  entity_domain, 
  entity_name,
  num_hits,
  num_employees, 
  revenue,
  naics_code,
  industry_code,
  city, 
  state,
  country,
  total_ips,
  total_domains,
  net_ranges,
  ransome_source,
  ransome_upload_ts,
  ransome_scraped_ts,
  is_alerted
) 
select 
  max(bv_id),
  lower(bv_entity_domain),
  lower(ent.bv_entity_name),
  count(entity_domain),
  max(employee),
  max(revenue),
  max(naics_code),
  max(industry_code),
  max(lower(city)),
  max(lower(state)),
  max(lower(country)),
  max(total_ips),
  max(total_domain_count),
  max(total_netranges),
  max(ransomware_source),
  max(observed_ts),
  max(listing_ts),
  max(is_alerted)

from `tf-scoring-dev-ac2c.usna_capstone.entity_master_20250117` as ent
join `tf-scoring-dev-ac2c.usna_capstone.footprint_size_latest` as foot on bv_id = entity
join `tf-scoring-dev-ac2c.usna_capstone.ransomware_scraped_data` as ran on bv_entity_domain = entity_domain
group by bv_entity_domain,ent.bv_entity_name

'''
 
### CREATE Entity_Quality Table
### intent is that each entity (row) can be assesed before clustering, you can set a minimum 'quality'(% of non "" or null values) to your training entities

    # maybe make this a trigger? 

create_quality='''
create table `tf-scoring-dev-ac2c.usna_capstone.Entity_Quality_1` as
SELECT 
  bv_id,
  (1-round((
    -- Calculate the number of NULLs or blank strings in each row
    (IF(bv_id IS NULL OR bv_id = '', 1, 0) + 
     IF(entity_domain IS NULL OR entity_domain = '', 1, 0) + 
     IF(entity_name IS NULL OR entity_name = '', 1, 0) +
     IF(num_hits IS NULL, 1, 0) +
     IF(num_employees IS NULL OR num_employees = '', 1, 0) +
     IF(revenue IS NULL OR revenue = '', 1, 0) +
     IF(naics_code IS NULL OR naics_code = '', 1, 0) +
     IF(industry_code IS NULL OR industry_code = '', 1, 0) +
     IF(city IS NULL OR city = '', 1, 0) +
     IF(state IS NULL OR state = '', 1, 0) +
     IF(country IS NULL OR country = '', 1, 0) +
     IF(total_ips IS NULL, 1, 0) +
     IF(total_domains IS NULL, 1, 0) +
     IF(net_ranges IS NULL, 1, 0) +
     IF(ransome_source IS NULL OR ransome_source = '', 1, 0) +
     IF(ransome_upload_ts IS NULL, 1, 0) +
     IF(ransome_scraped_ts IS NULL, 1, 0) +
     IF(is_alerted IS NULL, 1, 0)
    ) / CAST(18 AS FLOAT64) -- Divide by the total number of columns (18)
  ),3)) AS quality
FROM 
  `tf-scoring-dev-ac2c.usna_capstone.Hit_Table_1`
'''

select_domains = '''
select entity_domain from `tf-scoring-dev-ac2c.usna_capstone.Hit_Table_1`
'''
