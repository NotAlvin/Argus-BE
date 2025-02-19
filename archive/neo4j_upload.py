from neo4j import GraphDatabase
import pandas as pd
from tqdm import tqdm
import os
from multiprocessing import Pool, cpu_count

# Load your data
insider_company_df = pd.read_csv('insider_company_relationships.csv').head(30000)

# Connect to Neo4j
uri = "neo4j+s://79f59118.databases.neo4j.io:7687"  # Update with your Neo4j URI
username = "neo4j"  # Update with your Neo4j username
password = os.getenv("NEO4J_KEY")  # Update with your Neo4j password

driver = GraphDatabase.driver(uri, auth=(username, password))

def reset_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")
    print('Graph Refreshed')

def create_nodes_and_relationships(rows):
    with driver.session() as session:
        for i, row in tqdm(rows.iterrows(), total=rows.shape[0], desc="Creating nodes and relationships"):
            session.execute_write(lambda tx: tx.run("""
                MERGE (i:Insider {link: $insider_link})
                SET i.name = $insider_name
                MERGE (c:Company {link: $company_link})
                SET c.name = $company_name
                MERGE (i)-[:INSIDER_AT]-(c)
            """, insider_link=row['insider_link'], insider_name=row['insider_name'],
                 company_link=row['company_link'], company_name=row['company_name']))

def process_rows(start_index, end_index):
    rows = insider_company_df.iloc[start_index:end_index]
    create_nodes_and_relationships(rows)

if __name__ == '__main__':
    with driver.session() as session:
        # Reset the graph
        session.execute_write(reset_graph)

    # Define the checkpoint interval
    checkpoint_interval = 3000

    # Use multiprocessing to parallelize the creation of nodes and relationships
    with Pool(processes=cpu_count()) as pool:
        for start_index in range(0, len(insider_company_df), checkpoint_interval):
            end_index = min(start_index + checkpoint_interval, len(insider_company_df))
            pool.apply_async(process_rows, (start_index, end_index))
            print(f'Processing index {start_index}')

        pool.close()
        pool.join()

    driver.close()