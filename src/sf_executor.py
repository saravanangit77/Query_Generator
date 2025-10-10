from snowflake.connector import connect as sf_connect
import time
import re
from typing import Optional, Dict, Any

class SnowflakeQueryExecutor:
    """
    A class to execute SQL queries on a Snowflake database with retry logic and error handling.
    It uses environment variables for connection parameters.
    """
    def __init__(self, connection_parameters: dict):
        self.connection_parameters = connection_parameters
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def execute_query(self, query: str) -> Optional[Any]:
        """
        Execute a SQL query with automatic retry logic for Snowflake-specific errors.
        
        Args:
            query: SQL query string to execute
            
        Returns:
            Query result (pandas DataFrame) or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                print(f"🔄 Executing query (attempt {attempt + 1}/{self.max_retries})")
                
                with sf_connect(**self.connection_parameters) as conn:
                    with conn.cursor() as cursor:
                        # Set context
                        cursor.execute(f"USE WAREHOUSE {self.connection_parameters['warehouse']}")
                        cursor.execute(f"USE DATABASE {self.connection_parameters['database']}")
                        cursor.execute(f"USE SCHEMA {self.connection_parameters['schema']}")
                        
                        # Execute the main query
                        cursor.execute(query)
                        result = cursor.fetch_pandas_all()
                        
                        print(f"✅ Query executed successfully on attempt {attempt + 1}")
                        return result
                        
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    # Check if it's a retryable error
                    if self._is_retryable_error(error_msg):
                        print(f"🔄 Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        print("❌ Non-retryable error encountered")
                        break
                else:
                    print(f"❌ All {self.max_retries} attempts failed")
                    raise e
        
        return None

    def _is_retryable_error(self, error_msg: str) -> bool:
        """
        Determine if an error is retryable based on common Snowflake error patterns.
        
        Args:
            error_msg: Error message from Snowflake
            
        Returns:
            True if the error is retryable, False otherwise
        """
        retryable_patterns = [
            r"date.*format",
            r"timestamp.*format", 
            r"epoch.*conversion",
            r"invalid.*date",
            r"invalid.*timestamp",
            r"date.*parsing",
            r"timestamp.*parsing",
            r"numeric.*overflow",
            r"division.*by.*zero",
            r"invalid.*number",
            r"column.*not.*found",
            r"table.*not.*found",
            r"syntax.*error",
            r"unexpected.*token"
        ]
        
        error_lower = error_msg.lower()
        for pattern in retryable_patterns:
            if re.search(pattern, error_lower):
                return True
        return False

    def execute_query_with_retry(self, query: str, sql_generator, user_id: str, original_question: str) -> Optional[Any]:
        """
        Execute query with automatic regeneration on Snowflake errors.
        
        Args:
            query: SQL query to execute
            sql_generator: SQLQueryGenerator instance for regeneration
            user_id: User ID for context
            original_question: Original user question
            
        Returns:
            Query result or None if all attempts failed
        """
        for attempt in range(self.max_retries):
            try:
                result = self.execute_query(query)
                if result is not None:
                    return result
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Query execution failed: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    print(f"🔄 Regenerating query based on error (attempt {attempt + 2}/{self.max_retries})")
                    
                    # Create error context for regeneration
                    error_context = f"Previous query failed with error: {error_msg}. Please fix the SQL syntax and data type issues."
                    
                    # Regenerate query with error context
                    new_query = sql_generator.generate_sql_query(
                        user_id, 
                        f"{original_question}. Error context: {error_context}",
                        collection_name="sql_knowledge_base", 
                        data_warehouse="snowflake"
                    )
                    
                    if new_query and new_query.strip().lower() != "no relevant documents found!":
                        print(f"🔄 New query generated: {new_query[:100]}...")
                        query = new_query  # Use the new query for next attempt
                    else:
                        print("❌ Failed to regenerate query")
                        break
                else:
                    print(f"❌ All {self.max_retries} regeneration attempts failed")
                    raise e
        
        return None

