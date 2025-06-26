import os

from snowflake.connector import SnowflakeConnection
from dotenv import load_dotenv
load_dotenv()

CONNECTION_PARAMETERS = {
    "account": os.environ["snowflake_account"],
    "user": os.environ["snowflake_user"],
    "password": os.environ["snowflake_password"],
    "role": os.environ["role"],
    "database": os.environ["db_name"],
    "warehouse": os.environ["wh_name"],
    "schema": os.environ["schema_name"],
}

conn = SnowflakeConnection(**CONNECTION_PARAMETERS)
def execute_query(query: str):
    """
    Executes a SQL query on the Snowflake database.

    :param query: The SQL query to execute.
    :return: The result of the query execution.
    """
    with conn.cursor() as cursor:
        cursor.execute(f"USE WAREHOUSE {CONNECTION_PARAMETERS['warehouse']}")
        cursor.execute(f"USE DATABASE {CONNECTION_PARAMETERS['database']}")
        cursor.execute(f"USE SCHEMA {CONNECTION_PARAMETERS['schema']}")
        cursor.execute(query)
        return cursor.fetch_pandas_batches()

likes = execute_query("SELECT * FROM likes")
print(likes)