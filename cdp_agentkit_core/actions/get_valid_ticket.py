from collections.abc import Callable

from cdp import Wallet
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import ContractLogicError

from cdp_agentkit_core.actions import CdpAction

# Constants
TICKET_SYSTEM_ADDRESS_TESTNET = "0x1370732E8557475059949766dDA08Fa7f8B7f893"
L2_RESOLVER_ADDRESS_TESTNET = "0x6533C94869D28fAA8dF77cc63f9e2b2D6Cf77eBA"

# ABIs for smart contracts
l2_resolver_abi = [
]

ticket_abi = [
    {
        "inputs": [{"internalType": "string", "name": "bskyHandle", "type": "string"}],
        "name": "getValidTicketId",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class GetValidTicketInput(BaseModel):
    """Input argument schema for getting a valid ticket ID."""
    bsky_handle: str = Field(..., description="The Bluesky handle to check for valid ticket")

def get_valid_ticket(wallet: Wallet, bsky_handle: str) -> str:
    """Query the ticket system contract for a valid ticket ID.
    
    Args:
        wallet (Wallet): The wallet to query with
        bsky_handle (str): The Bluesky handle to check

    Returns:
        str: Ticket ID or error message
    """
    try:
        result = wallet.call_contract(
            contract_address=TICKET_SYSTEM_ADDRESS_TESTNET,
            method="getValidTicketId",
            args=[bsky_handle],
            abi=ticket_abi,
        )
        return f"Valid ticket ID for {bsky_handle}: {result}"
    except ContractLogicError as e:
        return f"Contract error checking ticket: {e!s}"
    except Exception as e:
        return f"Error checking ticket: {e!s}"

class GetValidTicketAction(CdpAction):
    def execute(self):
        # Implement your ticket validation logic here
        pass
