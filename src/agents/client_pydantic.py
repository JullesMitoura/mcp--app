import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI

from src.utils.settings import Settings
sets = Settings()

clients_mcp = MCPServerHTTP(url = "http://localhost:8000/sse",
                            tool_prefix="client")

client_openai = AsyncAzureOpenAI(
    api_key=sets.azure_openai_api_key,
    azure_endpoint=sets.azure_openai_endpoint,
    api_version=sets.llm_api_version
)

agent = Agent(
    mcp_servers=[clients_mcp],
    model=OpenAIModel(
        model_name=sets.llm_deployment_model,
        provider = OpenAIProvider(openai_client = client_openai)
    )
)

# main
async def main():
    async with agent.run_mcp_servers():
        while True:
            question = input("User: ")
            response = await agent.run(question)
            print(response.output)

if __name__ == "__main__":
    asyncio.run(main())