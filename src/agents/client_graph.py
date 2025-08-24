# to async development
import asyncio

# typing 
from typing import List, Annotated
from typing_extensions import TypedDict

# mcp from langchain
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langchain_mcp_adapters.client import MultiServerMCPClient

# langgraph
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver

# langchain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# local imports 
from src.utils.settings import Settings
from src.services.azure_openai import AzureOpenaiService

sets = Settings()
print(sets)
azure_service = AzureOpenaiService(sets)


# --------------------------------------------------------------------
clients_mcp = MultiServerMCPClient(
    {
        "clients": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http"
        }
    }
)

async def graph_build(clients_session):
    # define llm
    llm = azure_service.get_llm()

    # load mcp tools
    mcp_tools = await load_mcp_tools(clients_session)

    # link mcp tools with llm
    llm_tools = llm.bind_tools(mcp_tools)

    # system prompt
    system_prompt = await load_mcp_prompt(clients_session, "system_prompt")

    # define a prompt template
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt[0].content),
            MessagesPlaceholder("messages")
        ]
    )

    # define the chain
    chat_llm = prompt_template | llm_tools

    # define a state graph
    class State(TypedDict):
        messages: Annotated[List[AnyMessage], add_messages]

    # function to represents a node in graph
    def chat_node(state: State) -> State:
        state["messages"] = chat_llm.invoke({"messages": state["messages"]})
        return state

    # start the graph build
    graph_builder = StateGraph(State)

    # add node to graph
    graph_builder.add_node("chat_node", chat_node)

    # add node to call mcp servers
    graph_builder.add_node("tool_node", ToolNode(tools = mcp_tools))

    # connect the initial node to chat node
    graph_builder.add_edge(START, "chat_node")

    # define conditional edges between: if tools were used, go to tool_node, else go to end
    graph_builder.add_conditional_edges("chat_node", 
                                        tools_condition, 
                                        {"tools": "tool_node", "__end__": END})

    # connect tool_node back to chat_node
    graph_builder.add_edge("tool_node", "chat_node")

    # compile the graph
    graph = graph_builder.compile(checkpointer=MemorySaver())

    return graph

async def main():
    cfgs = {"configurable": {"thread_id":1234}}

    async with clients_mcp.session("clients") as clients_session:
        agent = await graph_build(clients_session)

        while True:
            message = input("User: ")
            response = await agent.ainvoke({"messages": message}, config=cfgs)
            print("Agent:", response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())