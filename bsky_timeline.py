"""
A test script for interacting with the Bluesky social network API.

This script demonstrates basic Bluesky API functionality by fetching and displaying
the authenticated user's home timeline. Posts are displayed in reverse chronological
order, showing both original posts and reposts with their authors.
"""

from atproto import Client

from dotenv import load_dotenv
import os

load_dotenv()
BLUESKY_USERNAME = os.environ["BLUESKY_USERNAME"]
BLUESKY_PASSWORD = os.environ["BLUESKY_PASSWORD"]

def main() -> None:
    client = Client()
    client.login(BLUESKY_USERNAME, BLUESKY_PASSWORD)

    print('Home (Following):\n')

    # Get "Home" page. Use pagination (cursor + limit) to fetch all posts
    timeline = client.get_timeline(algorithm='reverse-chronological')
    for feed_view in timeline.feed:
        action = 'New Post'
        if feed_view.reason:
            action_by = feed_view.reason.by.handle
            action = f'Reposted by @{action_by}'

        post = feed_view.post.record
        author = feed_view.post.author

        print(f'[{action}] {author.display_name}: {post.text}')


if __name__ == '__main__':
    main()
