# state.py

from typing import TypedDict, List

class AgentState(TypedDict):
    code: str
    context: str
    tests: str
    last_output: str
    step: int
    done: bool