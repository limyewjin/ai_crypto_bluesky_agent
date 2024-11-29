from openai import OpenAI
from atproto import Client as atproto_client
from atproto import models as atproto_models
import json
from retrying import retry
from dotenv import load_dotenv
import os

from requests_oauthlib import OAuth1Session

load_dotenv()
openai_client = OpenAI()

BLUESKY_USERNAME = os.environ["BLUESKY_USERNAME"]
BLUESKY_PASSWORD = os.environ["BLUESKY_PASSWORD"]
BLUESKY_HANDLE = os.environ["BLUESKY_HANDLE"]

def bluesky_send_post(message):
  client = atproto_client()
  client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)
  post = client.send_post(message)
  return post

def bluesky_reply_post(post, text):
  client = atproto_client()
  client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)
  root_post_ref = atproto_models.create_strong_ref(post)
  reply_to_root = client.send_post(
    text=text,
    reply_to=atproto_models.AppBskyFeedPost.ReplyRef(parent=root_post_ref, root=root_post_ref),
  )
  return reply_to_root

def bluesky_get_post_thread(uri):
  client = atproto_client()
  client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)
  return client.get_post_thread(uri)

def bluesky_has_responded(thread_response):
  for reply in thread_response.thread.replies:
    if reply.post.author.handle == BLUESKY_HANDLE:
      return True
  return False

# Define a decorator to handle retrying on specific exceptions
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=100, wait_exponential_max=1000)
def generate_response(messages, tools=None, temperature=0.0, model="gpt-4o-mini"):
    """
    Generate a response using OpenAI API's Chat Completion feature.

    Args:
        messages (list): List of chat messages in the conversation. Each item is a dict with `role` (system, assistant, user) and `content`.
        temperature (float, optional): Controls the randomness of the response. Defaults to 0.5.

    Returns:
        str: The generated response from the chat model.

    Example messages = [
            {"role": "system", "content": "You are a helpful assistant in re-formatting text."},
            {"role": "user", "content": f"{chunk}\n--\nThe text above is a scrape from explainxkcd - it has line breaks in-between sentences and improper formatting. Clean up the text to have proper sentences and structure. Keep the original text intact - just clean text formatting (e.g., capitalization) and do not remove words."}]
    """
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            tools=tools,
        )

        return response.choices[0].message

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise