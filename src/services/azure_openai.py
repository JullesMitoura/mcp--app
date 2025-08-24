from src.utils.settings import Settings
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

class AzureOpenaiService:
    def __init__(self, sets:Settings):
        self.sets = sets
        self.llm_deployment_model = sets.llm_deployment_model
        self.llm_api_version = sets.llm_api_version
        self.embedding_api_version = sets.embedding_api_version
        self.embedding_deployment_model = sets.embedding_deployment_model
        self.azure_openai_api_key = sets.azure_openai_api_key
        self.azure_openai_endpoint = sets.azure_openai_endpoint
    
    def get_llm(self, temperaturte: float = 0.1):
        llm_instance = AzureChatOpenAI(
            api_key=self.azure_openai_api_key,
            azure_endpoint=self.azure_openai_endpoint,
            azure_deployment=self.llm_deployment_model,
            api_version=self.llm_api_version,
            temperature=temperaturte
        )
        return llm_instance
    
    def get_embeddings(self):
        embeddings_instance = AzureOpenAIEmbeddings(
            api_key=self.azure_openai_api_key,
            azure_endpoint=self.azure_openai_endpoint,
            azure_deployment=self.embedding_deployment_model,
            api_version=self.embedding_api_version
        )
        return embeddings_instance