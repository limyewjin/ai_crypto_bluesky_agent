// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TicketSystem {
    enum TicketState { NonExistent, Funded, Completed }
    
    struct TicketInfo {
        uint256 fundedCount;    // Number of funded tickets
        uint256 completedCount; // Number of completed tickets
    }
    
    address public owner;
    uint256 public constant TICKET_PRICE = 0.0001 ether;
    
    // Mapping from bluesky handle hash to ticket info
    mapping(bytes32 => TicketInfo) public tickets;
    
    event TicketsPurchased(string indexed bskyHandle, address indexed buyer, uint256 amount);
    event TicketCompleted(string indexed bskyHandle);
    
    constructor(address _owner) {
        require(_owner != address(0), "Invalid owner address");
        owner = _owner;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    function buyTickets(string calldata bskyHandle, uint256 numberOfTickets) external payable returns (bool) {
        require(numberOfTickets > 0, "Must buy at least one ticket");
        require(bytes(bskyHandle).length > 0, "Bluesky handle cannot be empty");
        
        uint256 totalCost = TICKET_PRICE * numberOfTickets;
        require(msg.value == totalCost, "Incorrect payment amount");
        
        bytes32 handleHash = keccak256(bytes(bskyHandle));
        TicketInfo storage info = tickets[handleHash];
        info.fundedCount += numberOfTickets;
        
        emit TicketsPurchased(bskyHandle, msg.sender, numberOfTickets);
        
        return true;
    }
    
    function completeTicket(string calldata bskyHandle) external onlyOwner {
        bytes32 handleHash = keccak256(bytes(bskyHandle));
        TicketInfo storage info = tickets[handleHash];
        
        require(info.fundedCount > info.completedCount, "No funded tickets available");
        
        info.completedCount++;
        emit TicketCompleted(bskyHandle);
    }
    
    function getTicketInfo(string calldata bskyHandle) external view returns (
        uint256 fundedCount,
        uint256 completedCount,
        uint256 availableTickets
    ) {
        bytes32 handleHash = keccak256(bytes(bskyHandle));
        TicketInfo storage info = tickets[handleHash];
        
        return (
            info.fundedCount,
            info.completedCount,
            info.fundedCount - info.completedCount
        );
    }
    
    function withdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
}