from collections.abc import Callable

from cdp import Wallet, Cdp
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import ContractLogicError

from cdp_agentkit_core.actions import CdpAction

# Constants
TICKET_SYSTEM_ADDRESS_TESTNET = "0x1370732E8557475059949766dDA08Fa7f8B7f893"
COMPLETE_TICKET_PROMPT = "Complete a ticket in the ticket system contract."

# ABIs for smart contracts
ticket_abi = [
    {
        "inputs": [{"internalType": "uint256", "name": "ticketId", "type": "uint256"}],
        "name": "completeTicket",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

class CompleteTicketInput(BaseModel):
    """Input argument schema for completing a ticket."""
    ticket_id: int = Field(..., description="The ID of the ticket to complete")

def complete_ticket(wallet: Wallet, cdp: Cdp, ticket_id: int) -> str:
    """Complete a ticket in the ticket system contract.
    
    Args:
        wallet (Wallet): The wallet to complete the ticket with
        cdp (Cdp): CDP instance
        ticket_id (int): The ID of the ticket to complete

    Returns:
        str: Success message or error message
    """
    try:
        wallet.invoke_contract(
            contract_address=TICKET_SYSTEM_ADDRESS_TESTNET,
            method="completeTicket",
            args={"ticketId": ticket_id},
            abi=ticket_abi,
        )
        
        return f"Successfully completed ticket {ticket_id}"
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

def complete_contract_method_args(ticket_id: int) -> dict:
    """Create arguments for completing a ticket.

    Args:
        ticket_id (int): The ID of the ticket to complete

    Returns:
        dict: Formatted arguments for the ticket contract method
    """
    return {
        "ticketId": ticket_id
    }
