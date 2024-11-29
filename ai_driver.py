"""
AI Driver script for monitoring Bluesky notifications and responding to mentions
from allowlisted users using OpenAI.
"""

import api
import cdp_agent
from time import sleep
from atproto import Client
from dotenv import load_dotenv
import os
import json


# How often to check for new notifications (in seconds)
FETCH_NOTIFICATIONS_DELAY_SEC = 30

# Load environment variables
load_dotenv()
BLUESKY_USERNAME = os.environ["BLUESKY_USERNAME"]
BLUESKY_PASSWORD = os.environ["BLUESKY_PASSWORD"]

# List of allowed users who can trigger AI responses
ALLOWED_USERS = os.environ["BLUESKY_ALLOWED_USERS"].split(",")

def should_respond(notification) -> bool:
    """Check if we should respond to this notification."""
    if notification.reason != 'mention':
        return False
        
    # Check if author is in allowlist
    return notification.author.handle in ALLOWED_USERS

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
                    
                    if should_respond(notification):
                        # Get the mention text
                        mention_text = notification.record.text
                        print(f"Mention text: {mention_text}")
                        
                        # Check if we've already responded to this thread
                        thread_response = api.bluesky_get_post_thread(notification.uri)
                        has_responded = api.bluesky_has_responded(thread_response)
                        
                        if not has_responded:
                            # Generate AI response
                            ai_response = get_ai_response(agent, notification.author.handle, mention_text)
                            print(f"AI response: {ai_response}")
                            
                            # Post the response
                            root = thread_response.thread
                            while root.parent is not None:
                                root = root.parent
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
