from snowflake.connector import connect as sf_connect

class SnowflakeQueryExecutor:
    """
    A class to execute SQL queries on a Snowflake database.
    It uses environment variables for connection parameters.
    """
    def __init__(self, connection_parameters: dict ):
        self.connection_parameters = connection_parameters

    def execute_query(self,query: str):
        with sf_connect(**self.connection_parameters) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"USE WAREHOUSE {self.connection_parameters['warehouse']}")
                cursor.execute(f"USE DATABASE {self.connection_parameters['database']}")
                cursor.execute(f"USE SCHEMA {self.connection_parameters['schema']}")
                cursor.execute(query)
                return cursor.fetch_pandas_all()

