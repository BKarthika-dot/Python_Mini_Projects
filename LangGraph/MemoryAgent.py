#AI ChatBot
# 1. Use different message types - HumanMessage and AIMessage
# 2. Maintain full conversation history using both message types
# 3. Create sophisticated conversation loop

from langgraph.graph import StateGraph,START,END
from langchain_core.messages import HumanMessage,AIMessage
from langchain_ollama import ChatOllama
from typing import TypedDict,List,Union


llm=ChatOllama(model="llama3.2")

class AgentState(TypedDict):
    messages:List[Union[HumanMessage,AIMessage]]

def process(state:AgentState)->AgentState:
    """Answers human request and stores it along with ai's response to retain memory"""

    response=llm.invoke(state['messages']) #we get an answer from the llm and store it in response
    print(f"AI: {response.content}\n")
    state['messages'].append(AIMessage(content=response.content))  #append llm's response to the state
    return state


graph=StateGraph(AgentState)
graph.add_node("Process",process)
graph.add_edge(START,"Process")
graph.add_edge("Process",END)

agent=graph.compile()

conversation_history=[]

user_input=input("Enter: ")

while user_input!="exit":
    conversation_history.append(HumanMessage(content=user_input))
    result=agent.invoke({"messages":conversation_history})
    conversation_history=result['messages']
    user_input=input("Enter: ")

with open( "conversation.txt","w") as file:
    file.write("Conversation history with AI Chatbot: \n\n\n")
    for messages in conversation_history:
        if isinstance(messages,HumanMessage):
            file.write(f"Human Input: {messages.content}")
        elif isinstance(messages,AIMessage):
            file.write(f"AI Response: {messages.content}")
    file.write("Conversation ended")

print("Conversation history updated in conversation.txt")



