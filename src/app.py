import json
import os
from dotenv import load_dotenv

from sf_executor import SnowflakeQueryExecutor
from sql_query_generator import SQLQueryGenerator

load_dotenv()


if __name__ == "__main__":
    # Choose your model provider: "google" or "azure"
    model_provider = os.environ.get("MODEL_PROVIDER", "google").lower()
    
    if model_provider == "azure":
        # Azure OpenAI configuration - using your .env variable names
        sql_generator = SQLQueryGenerator(
            chroma_path="chroma_db/test_db",
            model="gpt-4",  # Not used for Azure, but required parameter
            api_key=os.environ['AZURE_PASSWORD'],  # Your .env uses AZURE_PASSWORD
            model_provider="azure",
            azure_endpoint=os.environ['AZURE_USERNAME'],  # Your .env uses AZURE_USERNAME for endpoint
            azure_deployment=os.environ.get('AZURE_DEPLOYMENT', 'gpt-4'),  # Default deployment name
            api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        )
    else:
        # Google Gemini configuration (default)
        sql_generator = SQLQueryGenerator(
            chroma_path="chroma_db/test_db",
            model="gemini-1.5-flash",
            api_key=os.environ['GOOGLE_API_KEY_PERSONAL'],
            model_provider="google"
        )
    
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
    print("\nWelcome to the SQL Query Generator! Mr./Ms.", user_id)
    while True:
        user_query = input("Enter your SQL query or type 'exit' to quit: ")
        if user_query.lower() == 'exit':
            break
        try:
            print(user_query)
            sql_query = sql_generator.generate_sql_query(user_id,user_query, collection_name="sql_knowledge_base", data_warehouse="snowflake")
            print("Generated SQL Query: ", sql_query, "\n")
            if sql_query.strip().lower() != "no relevant documents found!":
                result = sql_executor.execute_query(sql_query)
                # Print DataFrame in a more structured format
                print("\n" + "="*80)
                print(" "*30 + "📊 QUERY RESULTS 📊")
                print("="*80 + "\n")

                if hasattr(result, 'to_dict'):  # Check if result is a pandas DataFrame
                    # Set display options for better formatting
                    import pandas as pd
                    from tabulate import tabulate

                    pd.set_option('display.max_columns', None)
                    pd.set_option('display.expand_frame_repr', False)
                    pd.set_option('display.max_colwidth', 100)

                    # Get column widths for better formatting
                    col_names = result.columns.tolist()

                    # Create a decorated table
                    table = tabulate(result, headers=col_names, tablefmt="fancy_grid", showindex=False)
                    print(table)

                    # Print summary info
                    print("\n" + "-"*80)
                    print(f"📈 Total rows: {len(result)} | Total columns: {len(result.columns)}")
                    print("-"*80)
                else:
                    print("🔍 Result:", result)
                print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"Error executing query: {e}")

    while True:
        # qstn = input("Enter your SQL query or type 'exit' to quit: ")
        sql_generator.generate_sql_query("No of users created?")