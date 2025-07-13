import chromadb
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from textwrap import dedent

from cache_service import CacheService


def extract_sql_from_code_block(result: str) -> str:
    # Remove the backticks and language label
    inner = result.strip().strip("`").split("\n")
    if inner[0].strip().lower() == "sql":
        return "\n".join(inner[1:])
    return result.strip()


class SQLQueryGenerator:
    def __init__(self, chroma_path: str , model: str, api_key: str):
        self.chroma_client = self._connect_chroma(chroma_path)
        self.llm = GoogleGenerativeAI(
            model=model,
            temperature=0.9,
            api_key=api_key
        )
        self.context_cache = CacheService(host='localhost', port=6379, db=0)
        self.prompt_template = PromptTemplate.from_template(
            "{system_msg} \nPrev-Conversation: {conversation}\nContext: {context}\nQuestion: {question}\nTask: {task}")

    def _connect_chroma(self, path: str):
        try:
            client = chromadb.PersistentClient(path=path)
            collections_list = client.list_collections()  # Ensures DB is not corrupted
            print(collections_list)
            if not collections_list:
                raise RuntimeError("❌ No collections found in ChromaDB. Please run data_ingest.py to create them.")
            print("✅ Connected to ChromaDB successfully.")
            return client
        except Exception as e:
            raise RuntimeError(f"❌ Error connecting to ChromaDB: {e}")

    def _get_collection(self, name: str):
        try:
            return self.chroma_client.get_or_create_collection(name)
        except ValueError:
            raise Exception(f"❌ Collection '{name}' not found. Please run data_ingest.py to create it.")

    def create_prompt_template(self, context: str, question: str, task: str, conversation: str) -> str:
        system_msg = dedent("""
            You are a helpful assistant. Only respond with the SQL query_prompt.
            If relevant documents are not found, respond with "No relevant documents found!".
            Do not include code blocks or formatting.
        """)
        return self.prompt_template.format(system_msg=system_msg, context=context, question=question, task=task, conversation = conversation)

    def generate_sql_query(self, key, search_query: str, collection_name: str = "sql_knowledge_base",
                           data_warehouse: str = "snowflake") -> str:
        collection = self._get_collection(collection_name)
        result = collection.query(query_texts=[search_query], n_results=10)
        documents = result.get("documents", [])

        if not documents or not documents[0]:
            return "No relevant documents found."

        context = "\n".join(doc for doc_list in documents for doc in doc_list)
        # get from cache_service.py
        conversation_list = self.context_cache.get_user_queries(key)
        conversation = "\n".join(
            f"User: {entry['user']} | LLM: {entry['llm_response']}" for entry in conversation_list
        )
        if not conversation:
            conversation = "No previous conversation found."
        print(conversation)
        prompt = self.create_prompt_template(context=context, question=search_query,
                                             task=f"Generate a SQL query_prompt to execute in {data_warehouse}", conversation=conversation)
        try:
            print("Prompt sent to LLM: \n", prompt,'\n\n')
            response = self.llm.invoke(prompt)
            if not response:
                return "No SQL query generated."
        except Exception as e:
            return f"❌ LLM error: {e}"

        sql_query = response.strip()
        self.context_cache.add_user_query(key, search_query, sql_query)  # Store the query in cache
        return sql_query