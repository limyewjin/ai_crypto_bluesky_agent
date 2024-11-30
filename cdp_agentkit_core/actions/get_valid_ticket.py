from collections.abc import Callable

from cdp import Wallet, Cdp, client
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import ContractLogicError
import json

from cdp_agentkit_core.actions import CdpAction

# Constants
TICKET_SYSTEM_ADDRESS_TESTNET = "0x1370732E8557475059949766dDA08Fa7f8B7f893"
GET_VALID_TICKET_PROMPT = "Check if a Bluesky handle (e.g., 'alice.bsky.social') has a valid ticket ID in the ticket system. This is needed before we will chat with a user."

# ABIs for smart contracts
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

def get_valid_ticket(wallet: Wallet, Cdp: Cdp, bsky_handle: str) -> str:
    """Query the ticket system contract for a valid ticket ID.
    
    Args:
        wallet (Wallet): The wallet to query with
        bsky_handle (str): The Bluesky handle to check

    Returns:
        str: Ticket ID or error message
    """
    try:
        request = client.models.read_contract_request.ReadContractRequest(
            abi=json.dumps(ticket_abi),
            args=json.dumps({ "bskyHandle": bsky_handle}),
            method="getValidTicketId")
        result = Cdp.api_clients.smart_contracts.read_contract(
            wallet.network_id,
            TICKET_SYSTEM_ADDRESS_TESTNET,
            request)
        # result looks like: "type='uint256' name=None value='1' values=None"
        return f"Ticket ID for {bsky_handle}: {result}"
    except ContractLogicError as e:
        return f"Contract error checking ticket: {e!s}"
    except Exception as e:
        return f"Error checking ticket: {e!s}"

class GetValidTicketAction(CdpAction):
    """Action to check for a valid ticket ID for a Bluesky handle."""
    name: str = "get_valid_ticket"
    description: str = GET_VALID_TICKET_PROMPT
    args_schema: type[BaseModel] | None = GetValidTicketInput
    func: Callable[..., str] = get_valid_ticket
