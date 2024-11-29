"""
AI Driver script for monitoring Bluesky notifications and responding to mentions
from allowlisted users using OpenAI.
"""

import api
import cdp_agent
import os
import json


def get_ai_response(agent: dict, user: str,prompt: str) -> str:
    """Get AI response using OpenAI."""
    messages = [
        {
            "role": "system",
            "content": ("You are a helpful AI assistant responding to mentions on Bluesky, a social media platform. "
                        "You have access to a CDP MPC wallet and can make transactions on the blockchain. You are operating "
                        "on the `base-sepolia` (aka testnet) network.  If no token is specified, use `eth` for the native asset. "
                        "The user message will be prefixed with `@<username>` and is a message on Bluesky that mentions you. "
                        "Keep responses concise and under 280 characters.")
        },
        {
            "role": "user", 
            "content": f"from @{user}: {prompt}"
        }
    ]
    
    while True:
        response = api.generate_response(messages, tools=agent["tools"])
        finished = False
        for choice in response.choices:
            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                results = cdp_agent.process_tool_calls(agent["wallet"], choice.message)
                print(results)
                for result in results:
                    function_call_result_message = {
                        "role": "tool",
                        "content": json.dumps(result["result"]),
                        "tool_call_id": result["id"]
                    }
                    messages.append(function_call_result_message)
            elif choice.finish_reason == "stop":
                finished = True
                break

        if finished:
            break

    return response.choices[0].message.content

def main() -> None:
    # Initialize Bluesky client
    agent = cdp_agent.init_agent()
    
    # Simple input loop
    while True:
        user_input = input("Enter your message (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
            
        # Using a test username for demonstration
        test_user = "yewjin.bsky.social"
        response = get_ai_response(agent, test_user, user_input)
        print(f"\nAI Response: {response}\n")

if __name__ == '__main__':
    main()
