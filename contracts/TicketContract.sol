// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TicketSystem {
    enum TicketState { NonExistent, Funded, Completed }
    
    struct Ticket {
        address owner;
        uint256 ticketId;
        uint256 amount;
        TicketState state;
        string bskyHandle;
    }
    
    address public owner;
    uint256 public constant TICKET_PRICE = 0.01 ether;
    
    mapping(uint256 => Ticket) public tickets;
    uint256 private nextTicketId = 1;
    
    event TicketCreated(uint256 indexed ticketId, address indexed owner, string bskyHandle);
    event TicketCompleted(uint256 indexed ticketId);
    
    constructor(address _owner) {
        require(_owner != address(0), "Invalid owner address");
        owner = _owner;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier validTicket(uint256 ticketId) {
        require(tickets[ticketId].state != TicketState.NonExistent, "Ticket does not exist");
        _;
    }
    
    function createTicket(string memory bskyHandle) external payable returns (uint256) {
        require(msg.value == TICKET_PRICE, "Incorrect payment amount");
        require(bytes(bskyHandle).length > 0, "Bluesky handle cannot be empty");
        
        uint256 ticketId = nextTicketId++;
        
        tickets[ticketId] = Ticket({
            owner: msg.sender,
            ticketId: ticketId,
            amount: msg.value,
            state: TicketState.Funded,
            bskyHandle: bskyHandle
        });
        
        emit TicketCreated(ticketId, msg.sender, bskyHandle);
        
        return ticketId;
    }
    
    function completeTicket(uint256 ticketId) external onlyOwner validTicket(ticketId) {
        require(tickets[ticketId].state == TicketState.Funded, "Ticket is not in Funded state");
        tickets[ticketId].state = TicketState.Completed;
        emit TicketCompleted(ticketId);
    }
    
    function getValidTicketId(string memory bskyHandle) external view returns (uint256) {       
        // Iterate backwards from most recent to oldest tickets
        for (uint256 i = nextTicketId - 1; i > 0; i--) {
            if (tickets[i].state == TicketState.NonExistent) continue;
            
            if (keccak256(bytes(tickets[i].bskyHandle)) == keccak256(bytes(bskyHandle))) {
                if (tickets[i].state == TicketState.Funded) {
                    return i;  // Found a valid funded ticket
                }
                break;  // Found a ticket for this handle but it's completed, no need to check older ones
            }
        }
        
        return 0;  // No valid ticket found
    }
    
    function withdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
}