from dotenv import load_dotenv
import os
from cdp import Cdp, Wallet, WalletData
import json
from cdp_agentkit_core.actions import CDP_ACTIONS

# Configure a file to persist the agent's CDP MPC Wallet Data.
WALLET_DATA_FILE = "wallet_data.txt"

def init_agent(network_id='base-sepolia'):
  load_dotenv()
  Cdp.configure(
      api_key_name=os.environ["CDP_API_KEY_NAME"],
      private_key=os.environ["CDP_API_KEY_PRIVATE_KEY"].encode().decode('unicode-escape')
  )
  wallet_data_json = None
  if os.path.exists(WALLET_DATA_FILE):
      with open(WALLET_DATA_FILE) as f:
          wallet_data_json = f.read()
  values = {}
  if wallet_data_json:
    wallet_data = WalletData.from_dict(json.loads(wallet_data_json))
    wallet = Wallet.import_data(wallet_data)
  else:
    wallet = Wallet.create(network_id=network_id)
  values["wallet"] = wallet

  tools = []

  for action in CDP_ACTIONS:
      # Extract function specifications
      action_name = action.name
      action_description = action.description.strip()
      action_args_schema = action.args_schema.model_json_schema()
      action_args_schema["strict"] = True

      # Create the tool specification
      tool = {
          "type": "function",
          "function": {
              "name": action_name,
              "description": action_description,
              "parameters": action_args_schema
          }
      }
      
      # Append to the tools list
      tools.append(tool)

  # Print or use the tools list
  print(json.dumps(tools, indent=4))
  values["tools"] = tools
  return values

def process_tool_calls(wallet, response):
    tool_calls = response.tool_calls

    results = []

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        # Find the action in CDP_ACTIONS
        for action in CDP_ACTIONS:
            if action.name == tool_name:
                try:
                    # Validate and call the function
                    validated_args = action.args_schema(**arguments)
                    print(f"Validated args: {validated_args}")
                    result = action.func(wallet, **validated_args.dict())
                    results.append({"id": tool_call.id, "result": result})
                except Exception as e:
                    results.append({"id": tool_call.id, "error": str(e)})
                break
        else:
            # Handle case where the tool is not found
            results.append({"id": tool_call.id, "error": f"Tool '{tool_name}' not found"})

    return results