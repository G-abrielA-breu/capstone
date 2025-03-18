
from google.cloud import bigquery

#### interacts with BQ database 
def run_query(query):
    ret = []
    client = bigquery.Client(project='tf-scoring-dev-ac2c')
    query_job = client.query(query)
    results = query_job.result()
    for row in results:
        ret.append(row.entity_domain)
    return ret

def wipe():
    lst_all = ["`tf-scoring-dev-ac2c.usna_capstone.Hit_Table_1`","`tf-scoring-dev-ac2c.usna_capstone.Entity_Quality_1`"]
    ret = []
    for i in lst_all: 
      query = (f'''delete from {i} where TRUE''')
      #print(query)
      try:
        client = bigquery.Client(project='tf-scoring-dev-ac2c')
        query_job = client.query(query)
        results = query_job.result()
        for row in results:
            ret.append(row.entity_domain)
      except Exception as e:
         print(e)

    for i in lst_all: 
      query = (f'''drop table {i}''')
      #print(query)
      try:
        client = bigquery.Client(project='tf-scoring-dev-ac2c')
        query_job = client.query(query)
        results = query_job.result()
        for row in results:
            ret.append(row.entity_domain)
        return ret
      except Exception as e:
         print(e)


if __name__ == "__main__":
    print("ran as main")
