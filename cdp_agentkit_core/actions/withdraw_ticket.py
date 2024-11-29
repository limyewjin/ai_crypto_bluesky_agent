from collections.abc import Callable

from cdp import Wallet
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import ContractLogicError

from cdp_agentkit_core.actions import CdpAction

# Constants
TICKET_SYSTEM_ADDRESS_TESTNET = "0x1370732E8557475059949766dDA08Fa7f8B7f893"
L2_RESOLVER_ADDRESS_TESTNET = "0x6533C94869D28fAA8dF77cc63f9e2b2D6Cf77eBA"
WITHDRAW_TICKET_PROMPT = "Withdraw accumulated funds from the ticket system contract."

# ABIs for smart contracts
l2_resolver_abi = [
]

ticket_abi = [
    {
        "inputs": [],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class WithdrawTicketInput(BaseModel):
    """Input argument schema for withdrawing funds from the ticket system."""
    pass  # No inputs needed for withdrawal

def withdraw_ticket(wallet: Wallet) -> str:
    """Withdraw funds from the ticket system contract.
    
    Args:
        wallet (Wallet): The wallet to withdraw funds with

    Returns:
        str: Success message or error message
    """
    try:
        # Call the withdraw function
        wallet.invoke_contract(
            contract_address=TICKET_SYSTEM_ADDRESS_TESTNET,
            method="withdraw",
            args=[],
            abi=ticket_abi,
        )
        
        return "Successfully withdrew funds from ticket system"
    except ContractLogicError as e:
        return f"Contract error during withdrawal: {e!s}"
    except Exception as e:
        return f"Error withdrawing funds: {e!s}"

class WithdrawTicketAction(CdpAction):
    """Withdraw funds from Ticket System action."""
    name: str = "withdraw_ticket"
    description: str = WITHDRAW_TICKET_PROMPT
    args_schema: type[BaseModel] | None = WithdrawTicketInput
    func: Callable[..., str] = withdraw_ticket

def withdraw_contract_method_args() -> dict:
    """Create ticket arguments with resolver data.

    Args:
        ticket_id (str): The ID of the ticket
        bsky_handle (str): The Bluesky handle to associate
        is_mainnet (bool): True if on mainnet, False if on testnet

    Returns:
        dict: Formatted arguments for the ticket contract method
    """
    withdraw_args = {
        "request": []
    }
    return withdraw_args
