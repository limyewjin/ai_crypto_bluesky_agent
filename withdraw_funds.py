import cdp_agent
import cdp_agentkit_core.actions.withdraw_ticket as withdraw_ticket

agent = cdp_agent.init_agent()
withdraw_ticket.withdraw_ticket(agent["wallet"], agent["Cdp"])