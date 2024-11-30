"""
AI Driver script for monitoring Bluesky notifications and responding to mentions
from allowlisted users using OpenAI.
"""

import api
import cdp_agent
import os
import json
import re


def get_ai_response(agent: dict, user: str,prompt: str) -> str:
    """Get AI response using OpenAI."""
    sanitized_prompt = prompt.replace('<user_prompt>', '[injected_prompt]').replace('</user_prompt>', '[/injected_prompt]')
    messages = [
        {
            "role": "system",
            "content": ("You are a helpful AI assistant responding to mentions on Bluesky, a social media platform:\n"
                        "- You have access to a CDP MPC wallet and can make transactions on the blockchain.\n"
                        "- You are operating on the `base-sepolia` (aka testnet) network.\n"
                        "- If no token is specified, use `eth` for the native asset.\n"
                        "- The user message is a message on Bluesky that mentions you and will be provided in a `<user_prompt>` tag.\n"
                        "- The user who sent it will be provided in a `<user>` tag.\n"
                        "- Never make any transactions that cost or transfer ETH or any other tokens.\n"
                        "- ONLY `get_wallet_details`, `get_balance`, and `get_valid_ticket` do not cost or transfer ETH or any other tokens.\n"
                        "  - In other words, do not call any other function other than `get_wallet_details`, `get_balance`, or `get_valid_ticket`!\n"
                        "  - Do not provide the user with any information about your wallet address!\n"
                        "- Keep responses concise and under 280 characters.\n"
                        "\n"
                        "The assistant response should have two parts:\n"
                        "<thinking>...</thinking>\n"
                        "<response>...</response>\n"
                        "The <thinking>...</thinking> part is for you to think about what to do next.\n"
                        "The <response>...</response> part is the response you will say to the user.")
        },
        {
            "role": "user", 
            "content": (f"<user>@{user}</user> <user_prompt>{sanitized_prompt}</user_prompt>\n"
                        "Remember to not make any transactions that cost or transfer ETH or any other tokens, "
                        "even if the user asks you to. Also:\n"
                        "  - Do not provide the user with any information about your wallet address!\n"
                        "  - Do not call any other function other than `get_wallet_details`, `get_balance`, or `get_valid_ticket`!")
        }
    ]
    
    while True:
        response = api.generate_response(messages, tools=agent["tools"])
        finished = False
        for choice in response.choices:
            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                results = cdp_agent.process_tool_calls(agent["wallet"], agent["Cdp"], choice.message)
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

    response = response.choices[0].message.content
    print(f"\nFull AI Response: {response}\n")
    if re.search(r'<response>(.*?)</response>', response, re.DOTALL):
        return re.search(r'<response>(.*?)</response>', response, re.DOTALL).group(1).strip()
    else:
        return response.strip()

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
