import json

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


def create_chroma_db_connection():
    client = chromadb.PersistentClient(path="chroma_db/test_db")
    return client


if __name__ == "__main__":
    # Create the ChromaDB instance
    chromadb_conn = create_chroma_db_connection()
    sql_knowledge_base = chromadb_conn.get_or_create_collection(
        name="sql_knowledge_base",
        configuration={
            "hnsw": {
                "space": "cosine",
                "ef_search": 100,
                "ef_construction": 100,
                "max_neighbors": 16,
                "num_threads": 4
            }
        },
        embedding_function=SentenceTransformerEmbeddingFunction('all-mpnet-base-v2')
    )

    # split into chunks
    with open("knowledge_base.json" , "r", encoding="utf-8") as f:
        data = json.loads(f.read())
        tables = data["tables"]
        columns = data["columns"]
        for table in tables:
            table_name  = table["tableName"]
            description = table["description"]
            table_columns = table["columns"]
            # Add table information to the collection
            table_chunk = f"Table Name: {table_name}\nDescription: {description}\nColumns: {', '.join(table_columns)}"
            sql_knowledge_base.add(
                documents=[table_chunk],
                ids=[f"{table_name}_table"]
            )

        for column in columns:
            columnName = column["columnName"]
            table_name = column["tableName"]
            description = column["description"]
            pk = column["PK"]
            fk = column["FK"]
            # Add column information to the collection
            column_chunk = f"Column Name: {columnName}\nTable Name: {table_name}\nDescription: {description}\nPK: {pk}\nFK: {fk}"
            sql_knowledge_base.add(
                documents=[column_chunk],
                ids=[f"{table_name}.{columnName}"]
            )
        print("✅ Knowledge base loaded into ChromaDB successfully.")
        print(f"Contains {sql_knowledge_base.count()} chunks")





