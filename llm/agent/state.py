from typing import TypedDict, Annotated, List, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    user_id: int
    deferred_action: Any