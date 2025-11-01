import asyncio
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from llm.agent.state import AgentState
from telegram_bot.actions import (
    view_notes as view_notes_async,
    add_note as add_note_async,
    delete_note as delete_note_async,
    edit_note as edit_note_async,
    find_by_tag as find_by_tag_async,
    get_help as get_help_async,
    report_issue as report_issue_async,
)

@tool
async def get_help_tool() -> str:
    """Returns a help message with instructions on how to use the bot."""
    return await get_help_async()

@tool
async def report_issue_tool(report_text: str) -> dict:
    """Reports an issue or suggestion to the developer."""
    return await report_issue_async(report_text)

@tool
async def view_notes_tool() -> str:
    """Shows all notes."""
    # This is a placeholder. The actual implementation is in call_tools.
    pass

@tool
async def add_note_tool(note_text: str) -> str:
    """Adds a note."""
    # This is a placeholder. The actual implementation is in call_tools.
    pass

@tool
async def delete_note_tool(note_id: int) -> str:
    """Deletes a note."""
    # This is a placeholder. The actual implementation is in call_tools.
    pass

@tool
async def edit_note_tool(note_id: int, new_text: str) -> str:
    """Edits a note."""
    # This is a placeholder. The actual implementation is in call_tools.
    pass

@tool
async def find_by_tag_tool(tag: str) -> str:
    """Finds notes by tag."""
    # This is a placeholder. The actual implementation is in call_tools.
    pass

tools = [
    view_notes_tool,
    add_note_tool,
    delete_note_tool,
    edit_note_tool,
    find_by_tag_tool,
    get_help_tool,
    report_issue_tool,
]

llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
llm_with_tools = llm.bind_tools(tools)

async def call_model(state: AgentState):
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

async def call_tools(state: AgentState):
    tool_messages = []
    deferred_action = None
    user_id = state["user_id"]

    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        
        if tool_name == "view_notes_tool":
            message = await view_notes_async(user_id)
        elif tool_name == "add_note_tool":
            message = await add_note_async(user_id, **tool_input)
        elif tool_name == "delete_note_tool":
            message = await delete_note_async(**tool_input)
        elif tool_name == "edit_note_tool":
            message = await edit_note_async(**tool_input)
        elif tool_name == "find_by_tag_tool":
            message = await find_by_tag_async(user_id, **tool_input)
        elif tool_name == "get_help_tool":
            message = await get_help_async()
        elif tool_name == "report_issue_tool":
            result = await report_issue_async(**tool_input)
            deferred_action = {"action": result["action"], "text": result["text"]}
            message = result["user_message"]
        else:
            continue

        tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=message))

    return {"messages": tool_messages, "deferred_action": deferred_action}

def should_continue(state: AgentState):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

async def run_agent_async(user_input: str, user_id: int):
    messages = [HumanMessage(content=user_input)]
    return await app.ainvoke({"messages": messages, "user_id": user_id, "deferred_action": None})

def run_agent(user_input: str, user_id: int):
    return asyncio.run(run_agent_async(user_input, user_id))