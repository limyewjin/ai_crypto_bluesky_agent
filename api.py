import openai
import json
import time
from retrying import retry
from dotenv import load_dotenv
import os
import tiktoken

from requests_oauthlib import OAuth1Session

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

TWITTER_CONSUMER_KEY = os.environ["TWITTER_API_KEY"]
TWITTER_CONSUMER_SECRET = os.environ["TWITTER_API_KEY_SECRET"]
TWITTER_ACCESS_TOKEN = os.environ["TWITTER_ACCESS_TOKEN"]
TWITTER_ACCESS_TOKEN_SECRET = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

def create_tweet_payload(text, reply_tweet_id=None, quote_tweet_id=None):
  payload = {"text": text}
  if reply_tweet_id:
    payload["reply"] = { "in_reply_to_tweet_id": reply_tweet_id }
  if quote_tweet_id:
    payload["quote_tweet_id"] = quote_tweet_id
  return payload

def send_tweet(text, reply_tweet_id=None, quote_tweet_id=None):
  payload = create_tweet_payload(text, reply_tweet_id=reply_tweet_id, quote_tweet_id=quote_tweet_id)

  oauth = OAuth1Session(
      TWITTER_CONSUMER_KEY,
      client_secret=TWITTER_CONSUMER_SECRET,
      resource_owner_key=TWITTER_ACCESS_TOKEN,
      resource_owner_secret=TWITTER_ACCESS_TOKEN_SECRET,
  )

  # Making the request
  response = oauth.post(
      "https://api.twitter.com/2/tweets",
      json=payload,
  )

  if response.status_code != 201:
      raise Exception(
          "Request returned an error: {} {}".format(response.status_code, response.text)
      )

  print("Response code: {}".format(response.status_code))

  # Saving the response as JSON
  json_response = response.json()
  return json_response

def send_tweets(tweets):
  reply_tweet_id = None
  responses = []
  for i, tweet in enumerate(tweets):
    print(f"sending {i+1} / {len(tweets)}: {tweet}")
    try:
      response = send_tweet(tweet, reply_tweet_id=reply_tweet_id)
      reply_tweet_id = response["data"]["id"]
    except Exception as e:
      print(f"Error {e}")
      response = send_tweet(tweet, reply_tweet_id=reply_tweet_id)
      reply_tweet_id = response["data"]["id"]
    responses.append(response)
  return responses

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=100, wait_exponential_max=1000)
def get_next_step(messages, functions, function_call='auto', model='gpt-3.5-turbo-0613'):
    # Step 1: send the conversation and available functions to GPT
    #messages = [{"role": "user", "content": "What should I do next?"}]
    #functions = [
    #    {
    #        "name": "turing_action",
    #        "description": "Call out what to do next in AI chat game",
    #        "parameters": {
    #            "type": "object",
    #            "properties": {
    #                "action": {
    #                    "type": "string",
    #                    "description": "The next action to take",
    #                    "enum": ["talk", "pause"],
    #                },
    #                "text": {
    #                    "type": "string",
    #                    "description": "What to say, present when talking",
    #                },
    #                "wait_in_s": {
    #                    "type": "string",
    #                    "description": "How long to wait, in seconds",
    #                },
    #            },
    #            "required": ["action"],
    #        },
    #    }
    #]
    # function_call = {'name': 'turing_action'}
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        return response["choices"][0]["message"]
    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def is_correct(original, answer, question, model='gpt-3.5-turbo-0613'):
    # use this if you can fit source content in it
    # original: source content
    # answer: answer received
    # question: for LLM to answer
    messages = [{"role": "system", "content": "You are a helpful AI in assessing the quality of answers."},
      {"role": "user", "content": f"The source content is:\n{original}\n--\nThe answer generated was:\n{answer}\n--\n{question}"}]
    functions = [
        {
            "name": "is_correct",
            "description": "Assesses the quality and correctness of the answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "correct": {
                        "type": "string",
                        "description": "Is the answer generated correctly?",
                        "enum": ["true", "false"],
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Rationale for whether or not the answer was generated correctly",
                    },
                },
                "required": ["correct", "rationale"],
            },
        }
    ]
    function_call = {'name': 'is_correct'}
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        response_message = response["choices"][0]["message"]
        function_args = json.loads(response_message['function_call']['arguments'])
        return function_args
    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def is_good_response(response, question, model='gpt-4'):
    # response = answer from LLM
    # question = "Evaluate if the response received has useful articles and links to the articles in it."
    messages = [{'role': 'system',
      'content': f"You are a helpful AI which helps to assess responses."},
      {'role': 'user',
      'content': f'Here\'s the text we received:\n{response}\n---\n{question}'}]
    functions = [
          {
              "name": "is_good_response",
              "description": "Function call to whether or not the response extracted useful articles and links.",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "rating": {
                          "type": "string",
                          "description": "Was the response good or bad",
                          "enum": ["good", "bad"],
                      },
                      "rationale": {
                          "type": "string",
                          "description": "rationale for the rating given",
                      },
                  },
                  "required": ["rating", "rationale"],
              },
          }
      ]
    function_call = {'name': 'is_good_response'}
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        response_message = response["choices"][0]["message"]
        function_args = json.loads(response_message['function_call']['arguments'])
        return function_args
    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


# Define a decorator to handle retrying on specific exceptions
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=100, wait_exponential_max=1000)
def generate_response(messages, temperature=0.0, top_p=1, frequency_penalty=0.0, model="gpt-3.5-turbo"):
    """
    Generate a response using OpenAI API's ChatCompletion feature.

    Args:
        messages (list): List of chat messages in the conversation. Each item is a dict with `role` (system, assistant, user) and `content`.
        temperature (float, optional): Controls the randomness of the response. Defaults to 0.5.
        top_p (float, optional): Controls the nucleus sampling. Defaults to 1.
        max_tokens (int, optional): Maximum tokens in the response. Defaults to 1024.

    Returns:
        str: The generated response from the chat model.

    Example messages = [
            {"role": "system", "content": "You are a helpful assistant in re-formatting text."},
            {"role": "user", "content": f"{chunk}\n--\nThe text above is a scrape from explainxkcd - it has line breaks in-between sentences and improper formatting. Clean up the text to have proper sentences and structure. Keep the original text intact - just clean text formatting (e.g., capitalization) and do not remove words."}]
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=0
        )

        message = json.loads(str(response.choices[0].message))
        return message["content"].strip()

    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

