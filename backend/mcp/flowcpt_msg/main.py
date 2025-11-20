#!/usr/bin/env python3
"""
MCP to retrieve msg status from Flowcept.
"""

import threading

from fastmcp import FastMCP
from typing import Dict, Any

from flowcept.flowceptor.consumers.base_consumer import BaseConsumer


class FlowceptConsumer(BaseConsumer):
    def __init__(self):
        super().__init__()
        self.event = threading.Event()
        self.msg_result = None

    def message_handler(self, msg_obj: Dict) -> bool:
        if msg_obj.get("type", "") == "task":
            print(
                f"Received task: subtype={msg_obj.get('subtype', '')} activity_id={msg_obj.get('activity_id', '')}"
            )
            # FILTER BY subtypes:
            # agent_task, call_agent_task, data_message
            if msg_obj.get("subtype", "") in ["agent_task", "call_agent_task"]:
                self.msg_result = msg_obj
                self.event.set()
                return True

        else:
            print(f"We got a msg with different type: {msg_obj.get('type', None)}")
        return True


mcp = FastMCP(name="MCP_Flowcept")


@mcp.tool
def get_flowcept_msg() -> Dict[str, Any]:
    flowcept_communicator = FlowceptConsumer()
    flowcept_communicator.event.clear()
    flowcept_communicator.start(threaded=True)

    flowcept_communicator.event.wait()
    flowcept_communicator.stop_consumption()

    return {
        "results": flowcept_communicator.msg_result,
    }


if __name__ == "__main__":
    mcp.run()
