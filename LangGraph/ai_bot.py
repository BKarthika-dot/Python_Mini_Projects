# SIMPLE BOT

# Main Goal: Integrating LLMs into Graphs

# 1. Define state structure with a list of HumanMessageObjects
# 2. Initialise an LLM model using LangChain libraries
# 3. Sending & handling messages

from typing import TypedDict,List
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph,START,END

llm=ChatOllama(model="llama3.2")


class AgentState(TypedDict):
    messages:List[HumanMessage]

def process(state:AgentState)->AgentState:
    response=llm.invoke(state['messages'])
    print(f"\nAI:{response.content}")
    return state

graph=StateGraph(AgentState)
graph.add_node("Process",process)
graph.add_edge(START,"Process")
graph.add_edge("Process",END)
agent=graph.compile()


user_input=input("Enter: ")
while user_input!="exit":
    agent.invoke({"messages":[HumanMessage(content=user_input)]})
    user_input=input("Enter: ")
