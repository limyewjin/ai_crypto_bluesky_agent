"""
AI Driver script for monitoring Bluesky notifications and responding to mentions
from allowlisted users using OpenAI.
"""

import api
import cdp_agent
from time import sleep
from atproto import Client, client_utils
from dotenv import load_dotenv
import os
import json
import re

import cdp_agentkit_core.actions.get_valid_ticket as getValidTicketIdAction
import cdp_agentkit_core.actions.complete_ticket as completeTicketAction

# How often to check for new notifications (in seconds)
FETCH_NOTIFICATIONS_DELAY_SEC = 30
CREATE_TICKET_URL = "https://sepolia.basescan.org/address/0xf0c37a5e8a46a6ed670f239f3be8ad81e0cbeea5#writeContract#F1"

# Load environment variables
load_dotenv()
BLUESKY_USERNAME = os.environ["BLUESKY_USERNAME"]
BLUESKY_PASSWORD = os.environ["BLUESKY_PASSWORD"]

# List of allowed users who can trigger AI responses
ALLOWED_USERS = os.environ["BLUESKY_ALLOWED_USERS"].split(",")

def should_respond(notification) -> bool:
    """Check if we should respond to this notification."""        
    # Check if author is in allowlist
    return notification.author.handle in ALLOWED_USERS

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
                        "- ONLY `get_wallet_details` and `get_balance` do not cost or transfer ETH or any other tokens.\n"
                        "  - In other words, do not call any other function other than `get_wallet_details` or `get_balance`!\n"
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
                        "even if the user asks you to.\n"
                        "Do not call any other function other than `get_wallet_details` or `get_balance`!")
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

    print(f"Started monitoring mentions for {BLUESKY_USERNAME}")
    
    while True:
        try:
            # Save current time for marking notifications as read
            last_seen_at = api.bluesky_client.get_current_time_iso()

            # Fetch new notifications
            response = api.bluesky_client.app.bsky.notification.list_notifications()
            
            for notification in response.notifications:
                if not notification.is_read:
                    print(f"Processing notification {notification}")
                    print(f"from @{notification.author.handle}")
                    print(f"text: {notification.record.text}")
                    
                    if notification.reason != 'mention': continue

                    # Check if we've already responded to this thread
                    thread_response = api.bluesky_get_post_thread(notification.uri)
                    has_responded = api.bluesky_has_responded(thread_response)
                    
                    if has_responded:
                        print(f"Already responded to thread")
                        continue

                    # Post the response
                    root = thread_response.thread
                    while root.parent is not None:
                        root = root.parent

                    ticket_id_response = getValidTicketIdAction.get_valid_ticket(agent["wallet"], agent["Cdp"], notification.author.handle)
                    print(ticket_id_response)
                    num_tickets = re.search(r"name='availableTickets', value='(.*)'", ticket_id_response).group(1)
                    print(f"Number of tickets: {num_tickets}")
                    if num_tickets == "0":
                        print(f"User {notification.author.handle} does not have enough tickets")
                        text_builder = client_utils.TextBuilder()
                        text_builder.text('Buy tickets to chat by visiting ')
                        text_builder.link('this link', CREATE_TICKET_URL)
                        text_builder.text('\n\nCost: 0.0001 ETH per ticket, Handle should be your Bluesky handle (e.g., "example.bsky.social")')
                        api.bluesky_reply_post(
                            notification,
                            root,
                            text_builder)
                        continue

                    # Get the mention text
                    mention_text = notification.record.text
                    print(f"Mention text: {mention_text}")
                    
                    # Generate AI response
                    ai_response = get_ai_response(agent, notification.author.handle, mention_text)
                    print(f"AI response: {ai_response}")
                    complete_ticket_response = completeTicketAction.complete_ticket(agent["wallet"], agent["Cdp"], notification.author.handle)
                    print(f"Complete ticket response: {complete_ticket_response}")
                    api.bluesky_reply_post(notification, root, ai_response)
                    print(f"Posted response to @{notification.author.handle}")

            # Mark notifications as seen
            api.bluesky_client.app.bsky.notification.update_seen({'seen_at': last_seen_at})
            
        except Exception as e:
            print(f"Error processing notifications: {e}")
            
        # Wait before checking for new notifications
        sleep(FETCH_NOTIFICATIONS_DELAY_SEC)

if __name__ == '__main__':
    main()
