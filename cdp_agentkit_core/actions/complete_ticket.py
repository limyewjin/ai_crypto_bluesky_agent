from collections.abc import Callable

from cdp import Wallet, Cdp
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import ContractLogicError

from cdp_agentkit_core.actions import CdpAction

# Constants
TICKET_SYSTEM_ADDRESS_TESTNET = "0xF0c37a5E8a46a6ED670F239f3be8ad81e0cbeeA5"
COMPLETE_TICKET_PROMPT = "Complete a ticket in the ticket system contract."

# ABIs for smart contracts
ticket_abi = [
    {
        "inputs": [{"internalType": "string", "name": "bskyHandle", "type": "string"}],
        "name": "completeTicket",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

class CompleteTicketInput(BaseModel):
    """Input argument schema for completing a ticket."""
    bsky_handle: str = Field(..., description="The Bluesky handle associated with the ticket to complete")

def complete_ticket(wallet: Wallet, cdp: Cdp, bsky_handle: str) -> str:
    """Complete a ticket in the ticket system contract.
    
    Args:
        wallet (Wallet): The wallet to complete the ticket with
        cdp (Cdp): CDP instance
        bsky_handle (str): The Bluesky handle associated with the ticket to complete

    Returns:
        str: Success message or error message
    """
    try:
        wallet.invoke_contract(
            contract_address=TICKET_SYSTEM_ADDRESS_TESTNET,
            method="completeTicket",
            args={"bskyHandle": bsky_handle},
            abi=ticket_abi,
        )
        
        return f"Successfully completed ticket for {bsky_handle}"
    except ContractLogicError as e:
        return f"Contract error during ticket completion: {e!s}"
    except Exception as e:
        return f"Error completing ticket: {e!s}"

class CompleteTicketAction(CdpAction):
    """Complete a ticket in the Ticket System action."""
    name: str = "complete_ticket"
    description: str = COMPLETE_TICKET_PROMPT
    args_schema: type[BaseModel] | None = CompleteTicketInput
    func: Callable[..., str] = complete_ticket

def complete_contract_method_args(bsky_handle: str) -> dict:
    """Create arguments for completing a ticket.

    Args:
        bsky_handle (str): The Bluesky handle associated with the ticket to complete

    Returns:
        dict: Formatted arguments for the ticket contract method
    """
    return {
        "bskyHandle": bsky_handle
    }
