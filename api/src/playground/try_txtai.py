import csv
from txtai.embeddings import Embeddings

embeddings = Embeddings({"path": "sentence-transformers/all-MiniLM-L6-v2", "content": True, "objects": True})


def text_builder(row: dict[str: str]) -> str:

    r = f"""
Title: {row['job_title']}
Description: {row['job_description']}
"""
    return r


def generate_index():

    # Define the path to the CSV file
    csv_file = 'developer.csv'

    # Read the CSV file and create a list of tuples using list comprehension
    print(f'Reading {csv_file}...')
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        job_tuples = [(row['job_post_id'],  # ID
                       {"text": text_builder(row),
                        "job_title": row['job_title'],
                        "job_location": row['job_location'],
                        "workplace_type": row['workplace_type'],
                        "posted_timestamp": row['posted_timestamp'],
                        "contact": row['contact']
                        }, # DATA
                       None) for row in reader]

    print(f'INDEXING {len(job_tuples)} records...')
    result = embeddings.index(job_tuples)

    print(f'SAVING INDEX..')
    result = embeddings.save('./emb_developer')


def load_index():
    print('LOADING EMBEDDING INDEX...')
    my_index = embeddings.load('/Users/amit/Projects/linkedin_scraper/api/indexDB')


def search():
    while True:
        query = input("What are you looking for?\n")
        SQL = f"""
            SELECT job_title, job_location, workplace_type, score
            FROM txtai
            WHERE similar('{query}')
            AND (LOWER(job_location) LIKE '%tel aviv%' or LOWER(job_location) LIKE '%haifa%')
            """
        resuls = embeddings.search(SQL, 25)
        print(resuls)


if __name__ == '__main__':
    # generate_index()
    load_index()
    search()
