import redis
import json
from typing import List, Dict

class CacheService:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.r = redis.Redis(host=host, port=port, db=db)
            print(f"Connected to Redis server (version: {redis.__version__})")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self.r = None

    def add_user_query(self, user_id: str, user_qstn: str, sql_query: str):
        """
        Add a new query to the user's history, keeping only the latest 5 entries.

        Args:
            user_id: The unique identifier for the user
            user_qstn: The question asked by the user
            sql_query: The SQL query generated in response
        """
        if not self.r:
            print("Redis connection not available")
            return

        key = user_id
        entry = {'user': user_qstn, 'llm_response': sql_query}

        # Get existing list or start new
        try:
            data = self.r.get(key)
            if data:
                qlist = json.loads(data.decode('utf-8'))
            else:
                qlist = []

            # Add new entry
            qlist.append(entry)

            # Keep only the latest 5 entries
            if len(qlist) > 5:
                qlist = qlist[-5:]

            # Store back in Redis
            self.r.set(key, json.dumps(qlist))
            print(f"Successfully updated cache for user {user_id}")

        except Exception as e:
            print(f"Error updating cache: {e}")

    def get_user_queries(self, user_id: str) -> List[Dict]:
        """
        Retrieve the user's query history.

        Args:
            user_id: The unique identifier for the user

        Returns:
            A list of dictionaries containing user queries and responses
        """
        if not self.r:
            print("Redis connection not available")
            return []

        try:
            data = self.r.get(user_id)
            if data:
                return json.loads(data.decode('utf-8'))
            return []
        except Exception as e:
            print(f"Error retrieving from cache: {e}")
            return []

    def clear_user_cache(self, user_id: str) -> bool:
        """
        Clear all cached queries for a specific user.

        Args:
            user_id: The unique identifier for the user

        Returns:
            True if successful, False otherwise
        """
        if not self.r:
            return False

        try:
            return bool(self.r.delete(user_id))
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False

if __name__ == "__main__":
    cache_service = CacheService()
    # Example usage
    cache_service.add_user_query("user123", "What is the sales data for Q1?", "SELECT * FROM sales WHERE quarter = 'Q1';")
    queries = cache_service.get_user_queries("user123")
    print(queries)  # Should print the list of queries for user123