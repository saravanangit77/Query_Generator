import os
import chromadb
from langchain_google_genai import ChatGoogleGenerativeAI


class SQLQueryGenerator:
    def __init__(self, chroma_path: str = "chroma_db/test_db", model: str = "gemini-1.5-flash"):
        self.chroma_client = self._connect_chroma(chroma_path)
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0.9,
            api_key=os.getenv("GEMINI_API_KEY_PERSONAL")
        )

    def _connect_chroma(self, path: str):
        return chromadb.PersistentClient(path=path)

    def _get_collection(self, name: str):
        try:
            return self.chroma_client.get_collection(name)
        except ValueError:
            raise Exception(f"❌ Collection '{name}' not found. Please run data_ingest.py to create it.")

    @staticmethod
    def _format_prompt(context: str, question: str, task: str) -> str:
        return f"""
        You are a helpful assistant. Only respond with the SQL query. If relevant documents are not found, respond with "No relevant documents found.".
        Context: {context}
        Question: {question}
        Task: {task}
        """

    def generate_sql_query(self, search_query: str, collection_name: str = "sql_knowledge_base",
                           data_warehouse: str = "snowflake") -> str:
        collection = self._get_collection(collection_name)
        result = collection.query(query_texts=search_query, n_results=10)
        documents = result.get("documents", [])

        if not documents or not documents[0]:
            return "No relevant documents found."

        context = "\n".join(documents[0])
        prompt = self._format_prompt(context=context, question=search_query,
                                     task=f"Generate a SQL query to execute in {data_warehouse}")
        response = self.llm.invoke(prompt)

        if not response.content:
            return "No relevant documents found."

        try:
            # Extract SQL from code block
            sql_code_block = response.content.split("```")[1]
            return sql_code_block.lstrip("sql").strip()
        except IndexError:
            return response.content.strip()


if __name__ == "__main__":
    generator = SQLQueryGenerator()
    llm_search_query = "Who got more likes?"
    sql_query = generator.generate_sql_query(llm_search_query)
    print(f"Generated SQL Query:\n{sql_query}")
