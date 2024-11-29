from collections.abc import Callable

from cdp import Wallet
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import ContractLogicError

from cdp_agentkit_core.actions import CdpAction

# Constants
TICKET_SYSTEM_ADDRESS_TESTNET = "0x2a5529d1d2e306efde258a2eed9e40df098da6b3"

# Contract addresses
L2_RESOLVER_ADDRESS_TESTNET = "0x6533C94869D28fAA8dF77cc63f9e2b2D6Cf77eBA"

# ABIs for smart contracts
l2_resolver_abi = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "node", "type": "bytes32"},
            {"internalType": "address", "name": "a", "type": "address"},
        ],
        "name": "setAddr",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "node", "type": "bytes32"},
            {"internalType": "string", "name": "newName", "type": "string"},
        ],
        "name": "setName",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

ticket_abi = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "ticketId", "type": "uint256"},
            {"internalType": "string", "name": "bskyHandle", "type": "string"}
        ],
        "name": "verifyTicket",
        "outputs": [
            {"internalType": "bool", "name": "isValid", "type": "bool"},
            {"internalType": "enum TicketSystem.TicketState", "name": "state", "type": "uint8"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


class ReadTicketInput(BaseModel):
    """Input argument schema for reading a ticket."""
    ticket_id: str = Field(
        ...,
        description="The ID of the ticket to read"
    )

def read_ticket(wallet: Wallet, ticket_id: int, bsky_handle: str) -> str:
    """Read a ticket's status and Bluesky handle.

    Args:
        wallet (Wallet): The wallet to read the ticket with
        ticket_id (str): The ID of the ticket to read

    Returns:
        str: Ticket information or error message
    """
    try:        
        # Then verify the ticket
        verify_result = wallet.invoke_contract(
            contract_address=TICKET_SYSTEM_ADDRESS_TESTNET,
            method="verifyTicket",
            args=[int(ticket_id), bsky_handle],
            abi=ticket_abi,
        )
        
        is_valid, verified_state = verify_result
        
        # Convert state to string
        state_mapping = {0: "NonExistent", 1: "Funded", 2: "Completed"}
        state_str = state_mapping.get(state, "Unknown")
        
        validity_str = "Valid" if is_valid else "Invalid"
        
        return (f"Ticket {ticket_id}:\n"
                f"Bluesky Handle: {bsky_handle}\n"
                f"Verification: {validity_str}")
    except Exception as e:
        return f"Error reading ticket: {e!s}"


class ReadTicketAction(CdpAction):
    """Read Ticket action."""
    name: str = "read_ticket"
    description: str = "Read a ticket's status and Bluesky handle given its ID"
    args_schema: type[BaseModel] | None = ReadTicketInput
    func: Callable[..., str] = read_ticket

def create_ticket_contract_method_args(ticket_id: str, bsky_handle: str, is_mainnet: bool) -> dict:
    """Create ticket arguments with resolver data.

    Args:
        ticket_id (str): The ID of the ticket
        bsky_handle (str): The Bluesky handle to associate
        is_mainnet (bool): True if on mainnet, False if on testnet

    Returns:
        dict: Formatted arguments for the ticket contract method
    """
    w3 = Web3()
    resolver_contract = w3.eth.contract(abi=l2_resolver_abi)
    
    # Create namehash from ticket ID
    name_hash = w3.keccak(text=ticket_id)
    
    # Encode the resolver data for setting the Bluesky handle
    name_data = resolver_contract.encode_abi("setName", args=[name_hash, bsky_handle])
    
    ticket_args = {
        "request": [
            ticket_id,
            L2_RESOLVER_ADDRESS_TESTNET,
            [name_data],
            True,
        ]
    }
    
    return ticket_args
