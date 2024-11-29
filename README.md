# CDP AgentKit Bluesky Bot

A simplified implementation of a Bluesky bot powered by OpenAI and Coinbase's CDP AgentKit Core. This bot monitors Bluesky mentions and responds with AI-generated messages that can interact with blockchain functionality through CDP.

## Overview

This project uses:
- [CDP AgentKit Core](https://github.com/coinbase/cdp-agentkit/tree/master) for blockchain interactions
- OpenAI for generating responses
- Bluesky's atproto client for social media interactions

The bot monitors mentions on Bluesky and responds to allowlisted users with AI-generated messages that can perform blockchain operations like:
- Deploying NFTs and tokens
- Checking wallet balances
- Transferring assets
- Interacting with Zora's WOW protocol
- Requesting testnet funds

## Setup

1. Clone the repository

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Set up environment variables:

```
cp sample_env .env
```

## License

Apache-2.0 License - see LICENSE.md for details.
