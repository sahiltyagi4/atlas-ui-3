#!/usr/bin/env python3
"""
MCP tool to interact with INTERSECT (https://www.ornl.gov/intersect).
"""

import logging
import json
import yaml
import sys

from fastmcp import FastMCP
from typing import Dict, Any, Union

from intersect_sdk import (
    INTERSECT_JSON_VALUE,
    IntersectClient,
    IntersectClientCallback,
    IntersectClientConfig,
    IntersectDirectMessageParams,
    default_intersect_lifecycle_loop,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ClientExitError(Exception):
    """Custom exception for handling intentional client exit"""


class RosOrchestrator:
    def __init__(self, destination=None) -> None:
        if destination is None:
            raise ValueError("Destination must be specified!")

    def client_callback(
        self,
        source: str,
        operation: str,
        _has_error: bool,
        payload: INTERSECT_JSON_VALUE,
    ) -> None:
        print()
        print("Source: ", json.dumps(source))
        print("Operation: ", json.dumps(operation))
        print("Payload: ", json.dumps(payload))
        print()
        raise ClientExitError

    def event_callback(
        self,
        source: str,
        operation: str,
        event_name: str,
        payload: INTERSECT_JSON_VALUE,
    ) -> IntersectClientCallback:
        print()
        print("Source: ", json.dumps(source))
        print("Operation: ", json.dumps(operation))
        print("Event Name: ", json.dumps(event_name))
        print("Payload: ", json.dumps(payload))
        print()
        raise ClientExitError


mcp = FastMCP(name="Atlas_INTERSECT")


@mcp.tool
def launch_intersect(
    num_of_options: int = 4, print_name: str = "control_dwell_rook"
) -> Dict[str, Any]:
    # Load settings
    with open(sys.argv[1], mode="r", encoding="utf-8") as config_reader:
        from_config_file = yaml.safe_load(config_reader)

    # Intialize the client & orchestrator
    ros_hierarchy_str = ".".join(from_config_file["hierarchy_ros"].values())
    # Set options for messages that can be sent to the virtual experiment client
    options = {
        "1": {"operation": "RosPrinterCapability.status", "payload": None},
        "2": {
            "operation": "RosPrinterCapability.run_experiment",
            "payload": json.dumps(
                {
                    "number_of_options": num_of_options,
                    "print_name": print_name,
                }
            ),
        },
        "3": {
            "operation": "RosPrinterCapability.consume_data",
            "payload": json.dumps(
                {
                    "layer_number": 2,
                    "reheat_power": 222,
                    "dwell_0": 22,
                    "dwell_1": 22,
                }
            ),
        },
        "4": {
            "operation": "RosPrinterCapability.consume_data",
            "payload": json.dumps(
                {
                    "layer_number": 3,
                    "reheat_power": 333,
                    "dwell_0": 33,
                    "dwell_1": 33,
                }
            ),
        },
        "5": {
            "operation": "RosPrinterCapability.wait",
            "payload": 1,
        },
        "6": {
            "operation": "RosPrinterCapability.printer_stop",
            "payload": None,
        },
        "7": {
            "operation": "RosPrinterCapability.consume_data",
            "payload": json.dumps({"service_command": "reset"}),
        },
    }

    operation = None
    payload = None

    operation = options["2"]["operation"]
    payload = options["2"]["payload"]

    if operation is not None:
        try:
            initial_messages = [
                IntersectDirectMessageParams(
                    destination=ros_hierarchy_str,
                    operation=operation,
                    payload=payload,
                )
            ]
            orchestrator = RosOrchestrator(ros_hierarchy_str)
            config = IntersectClientConfig(
                **from_config_file,
                initial_message_event_config=IntersectClientCallback(
                    messages_to_send=initial_messages,
                ),
            )
            client = IntersectClient(
                config=config,
                user_callback=orchestrator.client_callback,
                event_callback=orchestrator.event_callback,
            )

            # Start the client
            default_intersect_lifecycle_loop(
                client,
            )
        except ClientExitError:
            pass

    return {
        "results": {
            "json_payload": payload,
        }
    }


if __name__ == "__main__":
    mcp.run()
