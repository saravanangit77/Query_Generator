import json
import os
from dotenv import load_dotenv

from sf_executor import SnowflakeQueryExecutor
from SQLQueryGenerator import SQLQueryGenerator

load_dotenv()


if __name__ == "__main__":
    sql_generator = SQLQueryGenerator("chroma_db/test_db", "gemini-1.5-flash", os.environ['GOOGLE_API_KEY_PERSONAL'])
    connection_parameters = {
        "account": os.environ["snowflake_account"],
        "user": os.environ["snowflake_user"],
        "password": os.environ["snowflake_password"],
        "role": os.environ["role"],
        "database": os.environ["db_name"],
        "warehouse": os.environ["wh_name"],
        "schema": os.environ["schema_name"],
    }

    sql_executor = SnowflakeQueryExecutor(connection_parameters=connection_parameters)


    user_id = input("Enter your user ID: ")
    while True:
        print("\nWelcome to the SQL Query Generator! Mr./Ms.", user_id)
        user_query = input("Enter your SQL query or type 'exit' to quit: ")
        if user_query.lower() == 'exit':
            break
        try:
            print(user_query)
            sql_query = sql_generator.generate_sql_query(user_id,user_query, collection_name="sql_knowledge_base", data_warehouse="snowflake")
            print("Generated SQL Query: ", sql_query, "\n")
            if sql_query.strip().lower() != "No relevant documents found!":
                result = sql_executor.execute_query(sql_query)
                print("Query Result: ", result, "\n")
        except Exception as e:
            print(f"Error executing query: {e}")

    while True:
        # qstn = input("Enter your SQL query or type 'exit' to quit: ")
        sql_generator.generate_sql_query("No of users created?")