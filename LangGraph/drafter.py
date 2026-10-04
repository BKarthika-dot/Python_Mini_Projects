from typing import Annotated,Sequence,TypedDict

#BaseMessage - foundational class for all message types in langgraph
#ToolMessage - passes data back to LLM after it calls a tool
#SystemMessage - provides instructions to the llm

from langchain_core.messages import BaseMessage,HumanMessage,ToolMessage,SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph,START,END

#add_messages is a reducer function - a rule that controls how updates from nodes are combined to the existing state

from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

#global variable to store dicument content
document_content=""

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage],add_messages]

@tool
def update_tool(content:str)->str:
    """Updates the document with provided content"""
    global document_content
    document_content=content

    return f"Document has been updated successfully! Content\n{document_content}"

@tool
def save_tool(filename:str)->str:
    """Saves the current document to a text file and finish the process.

    Args:
        filename: Name for the text file
    """

    global document_content

    if not filename.endswith('.txt'):
        filename=f"{filename}.txt"

    try:
        with open(filename,'w') as file:
            file.write(document_content)
        print(f"\n Document has been saved to {filename}")
        return f"Document has been saved to {filename}"
    except Exception as e:
        return f"Error saving document: {str(e)}"

tools=[save_tool,update_tool]
model=ChatOllama(model="llama3.2").bind_tools(tools)  


def our_agent(state:AgentState)->AgentState:

    system_prompt=SystemMessage(content=f"""You are a Drafting Agent and a helpful writing assistant. Your job is to help users update and modify documents.

        -If the user wants to update or modify content, use the 'update' tool with the complete updated content.
        -If the user wants to save and finish, use the 'save' tool.
        -Make sure to always show the current document state after modification.

        The current document content is:
        
        {document_content}
        """
    )

    if not state['messages']:
        user_input="I'm ready to help you update a document.What would you like to create?"
        user_message = HumanMessage(content=user_input)

    else:
        user_input=input("\nHow would you liketo modify this document? ")
        print(f"\n User: {user_input}")
        user_message=HumanMessage(content=user_input)

    all_messages=[system_prompt]+list(state['messages'])+[user_message]

    response=model.invoke(all_messages)


    print(f"\n AI:{response.content}")
    if hasattr(response,"tool_calls") and response.tool_calls:
        print(f"USING TOOLS: {[tc['name'] for tc in response.tool_calls]}")
        print(f"TOOL CALLS: {response.tool_calls}")
        return {"messages":[user_message,response]}



def should_continue(state:AgentState)->str:
    """Determine if we should either loop or end the conversation"""

    messages=state['messages']

    if not messages:
        return "continue"

    #find most recent tool message
    for message in reversed(messages):
        #checks if this tool message comes from save tool
        if(isinstance(message,ToolMessage) and
           "saved" in message.content.lower() and
           "document" in message.content.lower()):

            return "end"

    return "continue"

def print_messages(messages):
    """Prints messages in readable format"""
    if not messages:
        return

    for message in messages[-3:]:
        if isinstance(message,ToolMessage):
            print(f"\n TOOL RESULT: {message.content}")

graph=StateGraph(AgentState)
graph.add_node("agent",our_agent)
graph.add_node("tools",ToolNode(tools))

graph.add_edge(START,"agent")
graph.add_edge("agent","tools")

graph.add_conditional_edges(
    "tools",
    should_continue,
    {
        "continue":"agent",
        "end":END
    }

)

app=graph.compile()

def run_document_agent():
    print("\n ====== DRAFTER ======")

    state={"messages": []}

    for step in app.stream(state,stream_mode="values"):
        if "messages" in step:
            print_messages(step["messages"])

    print("\n ====== DRAFTER FINISHED ======")
        

if __name__ == "__main__":
    run_document_agent()
