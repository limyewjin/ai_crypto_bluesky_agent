"""
A test script for interacting with the Bluesky social network API.

This script demonstrates basic Bluesky API functionality by fetching and displaying
the authenticated user's notifications.
"""

import api

from time import sleep

from atproto import Client

# how often we should check for new notifications
FETCH_NOTIFICATIONS_DELAY_SEC = 3

from dotenv import load_dotenv
import os

load_dotenv()
BLUESKY_USERNAME = os.environ["BLUESKY_USERNAME"]
BLUESKY_PASSWORD = os.environ["BLUESKY_PASSWORD"]

def main() -> None:
    client = Client()
    client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)

    # fetch new notifications
    while True:
        # save the time in UTC when we fetch notifications
        last_seen_at = client.get_current_time_iso()

        response = client.app.bsky.notification.list_notifications()
        for notification in response.notifications:
            if True: #not notification.is_read:
                print(f'Got new notification! Type: {notification.reason}; from: {notification.author.did}')
                # example: "Got new notification! Type: like; from: did:plc:hlorqa2iqfooopmyzvb4byaz"
                if notification.reason == 'mention':
                  print(f'{notification.author.handle}: {notification.record.text}')
                  thread_response = api.bluesky_get_post_thread(notification.uri)
                  has_responded = api.bluesky_has_responded(thread_response)
                  print(f'has_responded: {has_responded}')
                  root = thread_response.thread
                  while root.parent is not None:
                      root = root.parent
                  if not has_responded:
                      api.bluesky_reply_post(notification, root, "response")

        # mark notifications as processed (isRead=True)
        client.app.bsky.notification.update_seen({'seen_at': last_seen_at})
        print('Successfully process notification. Last seen at:', last_seen_at)

        sleep(FETCH_NOTIFICATIONS_DELAY_SEC)

        break


if __name__ == '__main__':
    main()
