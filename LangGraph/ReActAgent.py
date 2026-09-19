from typing import Annotated,Sequence,TypedDict

#BaseMessage - foundational class for all message types in langgraph
#ToolMessage - passes data back to LLM after it calls a tool
#SystemMessage - provides instructions to the llm

from langchain_core.messages import BaseMessage,ToolMessage,SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph,START,END

#add_messages is a reducer function - a rule that controls how updates from nodes are combined to the existing state

from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]

@tool
def addition(a:int,b:int):
    """Function takes two integers and returns their sum"""
    return a+b

tools = [addition] #list of tools we can use

model=ChatOllama(model="llama3.2").bind_tools(tools)  #bind the tools to the model

def model_call(state:AgentState)->AgentState:
    system_prompt=SystemMessage(content=
        "You are an AI Assistant. Answer user queries to the best of your ability."
    ) 
    response=model.invoke([system_prompt]+state["messages"])

    return {"messages":[response]}

def should_continue(state:AgentState)->str:
    messages=state['messages']
    last_message=messages[-1]

    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"

    
graph=StateGraph(AgentState)
graph.add_node("our_agent",model_call)
graph.add_edge(START,"our_agent")

tool_node=ToolNode(tools=tools)
graph.add_node("tools",tool_node)

graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {
        "end":END,
        "continue":"tools"
    }
)

graph.add_edge("tools","our_agent")

app=graph.compile()

def print_stream(stream):
    for s in stream:
        message=s['messages'][-1]
        if isinstance(message,tuple):
            print(message)
        else:
            message.pretty_print()


user_input={"messages":[("user","Add 3+4")]}
print_stream(app.stream(user_input,stream_mode="values"))

