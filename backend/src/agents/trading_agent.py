"""
Coffee AI's LLM Trading Agent
Handles all LLM-based trading decisions
"""

# Keep only these prompts
TRADING_PROMPT = """
You are Coffee AI's AI Trading Assistant 

Analyze the provided market data and strategy signals (if available) to make a trading decision.

Market Data Criteria:
1. Price action relative to MA20 and MA40
2. RSI levels and trend
3. Volume patterns
4. Recent price movements

{strategy_context}

Respond in this exact format:
1. First line must be one of: BUY, SELL, or NOTHING (in caps)
2. Then explain your reasoning, including:
   - Technical analysis
   - Strategy signals analysis (if available)
   - Risk factors
   - Market conditions
   - Confidence level (as a percentage, e.g. 75%)

Remember: 
- Coffee AI always prioritizes risk management! 🛡️
- Never trade USDC or SOL directly
- Consider both technical and strategy signals
"""

ALLOCATION_PROMPT = """
You are Coffee AI's Portfolio Allocation Assistant 

Given the total portfolio size and trading recommendations, allocate capital efficiently.
Consider:
1. Position sizing based on confidence levels
2. Risk distribution
3. Keep cash buffer as specified
4. Maximum allocation per position

Format your response as a Python dictionary:
{
    "token_address": allocated_amount,  # In USD
    ...
    "USDC_ADDRESS": remaining_cash  # Always use USDC_ADDRESS for cash
}

Remember:
- Total allocations must not exceed total_size
- Higher confidence should get larger allocations
- Never allocate more than {MAX_POSITION_PERCENTAGE}% to a single position
- Keep at least {CASH_PERCENTAGE}% in USDC as safety buffer
- Only allocate to BUY recommendations
- Cash must be stored as USDC using USDC_ADDRESS: {USDC_ADDRESS}
"""

import enum
import functools
import json
import os
import threading
import time
from datetime import datetime, timedelta
from traceback import print_exc

import anthropic
import pandas as pd
from dotenv import load_dotenv

from src import nice_funcs as n

# Local imports
from src.config import *
from src.data.ohlcv_collector import collect_all_tokens, get_wallet_owned_tokens

# Load environment variables
load_dotenv()
mutex = threading.Lock()


def run_in_thread(func):
    """Decorator to run a function in a separate thread."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread  # Optionally return the thread object if you want to track it

    return wrapper


class AgentStatus(enum.Enum):
    INITIALIZED = "initialized"
    TRADING = "trading"
    SLEEPING = "sleeping"


class TradingAgent:
    tid: threading.Thread = None
    __stop = False

    def stop(self):
        if self.tid:
            self.__stop = True

    def __init__(self, run_id):
        self.setup(run_id)

    def setup(self, run_id):
        self.run_id = run_id
        self.status = AgentStatus.INITIALIZED
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
        self.logs = []
        if os.path.exists(f"runs/{self.run_id}_logs.json"):
            with open(f"runs/{self.run_id}_logs.json", "r") as f:
                self.logs = json.load(f)

        if os.path.exists(f"runs/{self.run_id}_recommendations_latest.csv"):
            self.recommendations_df = pd.read_csv(
                f"runs/{self.run_id}_recommendations_latest.csv"
            )
        else:
            self.recommendations_df = pd.DataFrame(
                columns=["token", "action", "confidence", "reasoning", "status"]
            )
        self.log("🤖 Coffee AI's LLM Trading Agent initialized!")

    def log(
        self, message: str, *ignore: str, also_print: bool = True, role="assistant"
    ):
        from anthropic.types import TextBlock

        """Log a message and optionally print it"""
        if isinstance(message, pd.DataFrame):
            message = message.to_string()
        if isinstance(message, TextBlock):
            message = message.text
        self.logs.append({"role": role, "time": time.time(), "message": message})
        if also_print:
            print(message)
        self.save_logs()

    def save_logs(self):
        """
        Save all logs from self.logs to a JSON file in the runs/ folder.
        The file name includes a timestamp so it won't be overwritten.
        """
        import json
        import os

        with mutex:
            # If there are no logs, you might not want to save an empty file
            if not self.logs:
                return

            for index, log in enumerate(self.logs):
                if isinstance(log, pd.DataFrame):
                    self.logs[index] = log.to_string()

            # Ensure the runs/ folder exists
            os.makedirs("runs", exist_ok=True)
            # Create a file name that includes the current time
            file_name = f"runs/{self.run_id}_logs.json"
            # Write logs to JSON
            with open(file_name, "w") as f:
                json.dump(self.logs, f, indent=2)
            print(f"✅ Logs saved to {file_name}")

    def analyze_market_data(self, token, market_data):
        """Analyze market data using Claude"""
        try:
            # Skip analysis for excluded tokens
            if token in EXCLUDED_TOKENS:
                self.log(f"⚠️ Skipping analysis for excluded token: {token}")
                return None

            # Prepare strategy context
            strategy_context = ""
            if "strategy_signals" in market_data:
                strategy_context = f"""
                                    Strategy Signals Available:
                                    {json.dumps(market_data["strategy_signals"], indent=2)}
                                    """
            else:
                strategy_context = "No strategy signals available."

            message = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": f"{TRADING_PROMPT.format(strategy_context=strategy_context)}\n\nMarket Data to Analyze:\n{market_data}",
                    }
                ],
            )

            # Parse the response - handle both string and list responses
            response = message.content
            if isinstance(response, list):
                # Extract text from TextBlock objects if present
                response = "\n".join(
                    [
                        item.text if hasattr(item, "text") else str(item)
                        for item in response
                    ]
                )

            lines = response.split("\n")
            action = lines[0].strip() if lines else "NOTHING"

            # Extract confidence from the response (assuming it's mentioned as a percentage)
            confidence = 0
            for line in lines:
                if "confidence" in line.lower():
                    # Extract number from string like "Confidence: 75%"
                    try:
                        confidence = int("".join(filter(str.isdigit, line)))
                    except:
                        confidence = 50  # Default if not found

            # Add to recommendations DataFrame with proper reasoning
            reasoning = (
                "\n".join(lines[1:])
                if len(lines) > 1
                else "No detailed reasoning provided"
            )
            self.recommendations_df = pd.concat(
                [
                    self.recommendations_df,
                    pd.DataFrame(
                        [
                            {
                                "token": token,
                                "action": action,
                                "confidence": confidence,
                                "reasoning": reasoning,
                                "status": "pending",
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

            self.log(f"🎯 Coffee AI's AI Analysis Complete for {token[:4]}!")
            return response

        except Exception as e:
            print_exc()
            self.log(f"❌ Error in AI analysis: {str(e)}")
            # Still add to DataFrame even on error, but mark as NOTHING with 0 confidence
            self.recommendations_df = pd.concat(
                [
                    self.recommendations_df,
                    pd.DataFrame(
                        [
                            {
                                "token": token,
                                "action": "NOTHING",
                                "confidence": 0,
                                "reasoning": f"Error during analysis: {str(e)}",
                                "status": "pending",
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
            return None

    def allocate_portfolio(self):
        MONITORED_TOKENS = get_wallet_owned_tokens(os.getenv("WALLET_ADDRESS"))
        """Get AI-recommended portfolio allocation"""
        try:
            self.log("\n💰 Calculating optimal portfolio allocation...", "cyan")
            max_position_size = usd_size * (MAX_POSITION_PERCENTAGE / 100)
            self.log(
                f"🎯 Maximum position size: ${max_position_size:.2f} ({MAX_POSITION_PERCENTAGE}% of ${usd_size:.2f})",
                "cyan",
            )

            # Get allocation from AI
            message = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are Coffee AI's Portfolio Allocation AI 
                        Given:
                        - Total portfolio size: ${usd_size}.00
                        - Maximum position size: ${max_position_size}.00 ({MAX_POSITION_PERCENTAGE}% of total)
                        - Minimum cash (USDC) buffer: {CASH_PERCENTAGE}%
                        - Available tokens: {MONITORED_TOKENS}
                        - USDC Address: {USDC_ADDRESS}

                        Provide a portfolio allocation that:
                        1. Never exceeds max position size per token
                        2. Maintains minimum cash buffer
                        3. Returns allocation as a JSON object with token addresses as keys and USD amounts as values
                        4. Uses exact USDC address: {USDC_ADDRESS} for cash allocation
                        Say I had $10 in USDC
                        Example format:
                        {{
                            "token_address": 1.5,
                            "{USDC_ADDRESS}": 8.5
                        }}""",
                    }
                ],
            )

            # Parse the response
            allocations = self.parse_allocation_response((message.content))
            if not allocations:
                return None

            # Fix USDC address if needed
            if "USDC_ADDRESS" in allocations:
                amount = allocations.pop("USDC_ADDRESS")
                allocations[USDC_ADDRESS] = amount

            # Validate allocation totals
            total_allocated = sum(allocations.values())
            if total_allocated > usd_size:
                self.log(
                    f"❌ Total allocation ${total_allocated:.2f} exceeds portfolio size ${usd_size:.2f}",
                    "red",
                )
                return None

            # Print allocations
            self.log("\n📊 Portfolio Allocation:", "green")
            for token, amount in allocations.items():
                token_display = "USDC" if token == USDC_ADDRESS else token
                self.log(f"  • {token_display}: ${amount:.2f}", "green")

            return allocations

        except Exception as e:
            self.log(f"❌ Error in portfolio allocation: {str(e)}", "red")
            return None

    def execute_allocations(self, allocation_dict):
        """Execute the allocations using AI entry for each position"""
        try:
            self.log("\n🚀 Coffee AI executing portfolio allocations...")

            for token, amount in allocation_dict.items():
                # Skip USDC and other excluded tokens
                if token in EXCLUDED_TOKENS:
                    self.log(f"💵 Keeping ${amount:.2f} in {token}")
                    continue

                self.log(f"\n🎯 Processing allocation for {token}...")

                try:
                    # Get current position value
                    current_position = n.get_token_balance_usd(token, logger=self.log)
                    target_allocation = amount

                    self.log(f"🎯 Target allocation: ${target_allocation:.2f} USD")
                    self.log(f"📊 Current position: ${current_position:.2f} USD")

                    if current_position < target_allocation:
                        self.log(f"✨ Executing entry for {token}")
                        n.ai_entry(token, amount, logger=self.log)
                        self.log(f"✅ Entry complete for {token}")
                    else:
                        self.log(f"⏸️ Position already at target size for {token}")

                except Exception as e:
                    print_exc()
                    self.log(f"❌ Error executing entry for {token}: {str(e)}")

                time.sleep(2)  # Small delay between entries

        except Exception as e:
            self.log(f"❌ Error executing allocations: {str(e)}")
            self.log("🔧 Coffee AI suggests checking the logs and trying again!")

    def handle_exits(self):
        """Check and exit positions based on SELL or NOTHING recommendations"""
        self.log("\n🔄 Checking for positions to exit...", "white", "on_blue")

        for index, row in self.recommendations_df.iterrows():
            token = row["token"]
            status = row["status"]
            # Skip excluded tokens (USDC and SOL)
            if token in EXCLUDED_TOKENS or status != "pending":
                continue

            action = row["action"]

            # Check if we have a position
            current_position = n.get_token_balance_usd(token, logger=self.log)

            if current_position > 0 and action in ["SELL"]:
                self.log(
                    f"\n🚫 AI Agent recommends {action} for {token}",
                    "white",
                    "on_yellow",
                )
                self.log(
                    f"💰 Current position: ${current_position:.2f}", "white", "on_blue"
                )
                try:
                    self.log(
                        "📉 Closing position with chunk_kill...", "white", "on_cyan"
                    )
                    n.chunk_kill(token, max_usd_order_size, slippage, logger=self.log)
                    self.log("✅ Successfully closed position", "white", "on_green")
                    self.recommendations_df.at[index, "status"] = "executed"
                except Exception as e:
                    self.log(f"❌ Error closing position: {str(e)}", "white", "on_red")
                    self.recommendations_df.at[index, "status"] = "failed"
            elif current_position > 0:
                self.log(
                    f"✨ Keeping position for {token} (${current_position:.2f}) - AI recommends {action}",
                    "white",
                    "on_blue",
                )
                self.recommendations_df.at[index, "status"] = "executed"

    def parse_allocation_response(self, response):
        response = str(response)
        print(f"{response=}")
        """Parse the AI's allocation response and handle both string and TextBlock formats"""
        try:
            # Handle TextBlock format from Claude 3

            # Find the JSON block between curly braces
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")

            json_str = response[start:end]

            # More aggressive JSON cleaning
            json_str = (
                json_str.replace("\n", "")  # Remove newlines
                .replace("    ", "")  # Remove indentation
                .replace("\t", "")  # Remove tabs
                .replace("\\n", "")  # Remove escaped newlines
                .replace(" ", "")  # Remove all spaces
                .strip()
            )  # Remove leading/trailing whitespace

            self.log("\n🧹 Cleaned JSON string:")
            self.log(json_str)

            # Parse the cleaned JSON
            allocations = json.loads(json_str)

            self.log("\n📊 Parsed allocations:")
            for token, amount in allocations.items():
                self.log(f"{token}: ${amount}")

            # Validate amounts are numbers
            for token, amount in allocations.items():
                if not isinstance(amount, (int, float)):
                    raise ValueError(f"Invalid amount type for {token}: {type(amount)}")
                if amount < 0:
                    raise ValueError(f"Negative allocation for {token}: {amount}")

            return allocations

        except Exception as e:
            self.log(f"❌ Error parsing allocation response: {str(e)}")
            try:
                # Construct a prompt to fix the response structure
                fix_prompt = f"""
                                The following response was expected to be a JSON object for portfolio allocations with token addresses as keys and USD amounts as values, but it is not in the correct format:
                                {response}

                                Please return only a properly formatted JSON object (no extra text) in the following format:
                                {{
                                    "token_address": allocated_amount,
                                    "USDC_ADDRESS": remaining_cash
                                }}
                            """
                fix_message = self.client.messages.create(
                    model=AI_MODEL,
                    max_tokens=AI_MAX_TOKENS,
                    temperature=AI_TEMPERATURE,
                    messages=[{"role": "user", "content": fix_prompt}],
                )
                fixed_response = (
                    fix_message.content.text
                    if hasattr(fix_message.content, "text")
                    else fix_message.content
                )
                self.log("🔍 Fixed response received:")
                self.log(fixed_response)

                # Try to extract the JSON block from the fixed response
                start = fixed_response.find("{")
                end = fixed_response.rfind("}") + 1
                if start == -1 or end == 0:
                    raise ValueError("No JSON object found in fixed response")

                fixed_json_str = fixed_response[start:end]
                fixed_json_str = (
                    fixed_json_str.replace("\n", "")
                    .replace("    ", "")
                    .replace("\t", "")
                    .replace("\\n", "")
                    .replace(" ", "")
                    .strip()
                )
                allocations = json.loads(fixed_json_str)

                self.log("\n📊 Parsed fixed allocations:")
                for token, amount in allocations.items():
                    self.log(f"  • {token}: ${amount}")

                # Validate the allocations as before
                for token, amount in allocations.items():
                    if not isinstance(amount, (int, float)):
                        raise ValueError(
                            f"Invalid amount type for {token}: {type(amount)}"
                        )
                    if amount < 0:
                        raise ValueError(f"Negative allocation for {token}: {amount}")

                return allocations
            except Exception as e2:
                self.log(f"❌ Error parsing fixed allocation response again: {str(e2)}")
                return None

    def process_user_input(self, user_input):
        MONITORED_TOKENS = get_wallet_owned_tokens(os.getenv("WALLET_ADDRESS"))
        """
        Convert the free-form user input into a structured recommendation.
        If the input is trivial (e.g., 'No need, this is fine') or yields an empty JSON,
        nothing is added and the agent continues.
        """
        try:
            log_length = len(self.logs)
            self.log(user_input, role="user")

            self.log("🔄 Collecting token details")
            token_info = collect_all_tokens(MONITORED_TOKENS, logger=self.log)
            history = self.logs
            fix_prompt = f"""
                        You are a trading recommendation assistant.
                        Your task is to convert the following unstructured free-form user input into a structured trading recommendation.
                        You will be provided with the hisotry of your and user's previous interactions and information about the tokens to evaluate.
                        The recommendation should be output as a JSON object with the following keys:
                        - "token": a token symbol,
                        - "action": one of "BUY", "SELL", or "NOTHING",
                        - "confidence": an integer percentage (default to 100 if not specified),
                        - "reasoning": a brief explanation.
                        If the user input does not contain any actionable recommendation, output an empty JSON object: {{}}
                        Token information:
                        "{token_info}"
                        
                        History:
                        "{history}"

                        User Input:
                        "{user_input}"

                        Only output the JSON object, with no additional text.
                        {{"token":"xxx", "action":"BUY", "confidence":100, "reasoning":"User provided recommendation."}}
                        """
            message = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                messages=[{"role": "user", "content": fix_prompt}],
            )
            structured_response = message.content

            if isinstance(structured_response, list):
                structured_response = (
                    structured_response[0].text
                    if hasattr(structured_response[0], "text")
                    else str(structured_response[0])
                )

            self.log("🔍 Structured recommendation from user input:")
            self.log(structured_response)
            recommendation = json.loads(structured_response)
            if not recommendation:
                self.log("ℹ️ No actionable recommendation extracted from user input.")
                return
            token = recommendation.get("token", "ALL")
            action = recommendation.get("action", None)
            confidence = recommendation.get("confidence", 100)
            reasoning = recommendation.get("reasoning", "User provided recommendation.")
            if action:
                new_row = {
                    "token": token,
                    "action": action,
                    "confidence": confidence,
                    "reasoning": reasoning,
                }
                self.recommendations_df = pd.concat(
                    [self.recommendations_df, pd.DataFrame([new_row])],
                    ignore_index=True,
                )
                self.log(f"🔄 Added structured user recommendation: {new_row}")
            else:
                self.log("ℹ️ No valid action found in recommendation.")
        except Exception as e:
            print_exc()
            self.log(f"❌ Error parsing structured recommendation: {str(e)}")
            self.log("ℹ️ Continuing without user recommendation.")
        finally:
            return self.logs[log_length:]

    def run(self):
        """Run the trading agent (implements BaseAgent interface)"""
        print("Starting cycle", self, self.__stop)
        self.tid = self._run_trading_cycle()

    @run_in_thread
    def _run_trading_cycle(self, strategy_signals=None):
        MONITORED_TOKENS = get_wallet_owned_tokens(os.getenv("WALLET_ADDRESS"))
        print("Starting cycle", self, self.__stop)
        """Run one complete trading cycle"""
        while not self.__stop:
            try:
                self.status = AgentStatus.TRADING
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log(
                    f"\n⏰ AI Agent Run Starting at {current_time}", "white", "on_green"
                )

                # Collect OHLCV data for all tokens
                self.log("📊 Collecting market data...", "white", "on_blue")
                market_data = collect_all_tokens(MONITORED_TOKENS, logger=self.log)

                # Analyze each token's data
                for token, data in market_data.items():
                    self.log(
                        f"\n🤖 AI Agent Analyzing Token: {token}", "white", "on_green"
                    )

                    # Include strategy signals in analysis if available
                    if strategy_signals and token in strategy_signals:
                        self.log(
                            f"📊 Including {len(strategy_signals[token])} strategy signals in analysis",
                            "cyan",
                        )
                        data["strategy_signals"] = strategy_signals[token]

                    analysis = self.analyze_market_data(token, data)
                    self.log(f"\n📈 Analysis for contract: {token}")
                    self.log(analysis)
                    self.log("\n" + "=" * 50 + "\n")

                # Show recommendations summary
                self.log("\n📊 Coffee AI's Trading Recommendations:", "white", "on_blue")
                summary_df = self.recommendations_df[
                    ["token", "action", "confidence", "status"]
                ].copy()
                self.log(summary_df.to_string(index=False))

                # Handle exits first
                self.handle_exits()

                # Then proceed with new allocations
                self.log(
                    "\n💰 Calculating optimal portfolio allocation...",
                    "white",
                    "on_blue",
                )
                allocation = self.allocate_portfolio()

                if allocation:
                    self.log(
                        "\n💼 Coffee AI's Portfolio Allocation:", "white", "on_blue"
                    )
                    self.log(json.dumps(allocation, indent=4))

                    self.log("\n🎯 Executing allocations...", "white", "on_blue")
                    self.execute_allocations(allocation)
                    self.log("\n✨ All allocations executed!", "white", "on_blue")
                else:
                    self.log("\n⚠️ No allocations to execute!", "white", "on_yellow")

                # Clean up temp data
                self.log("\n🧹 Cleaning up temporary data...", "white", "on_blue")
                try:
                    for file in os.listdir("temp_data"):
                        if file.endswith("_latest.csv"):
                            os.remove(os.path.join("temp_data", file))
                    self.log("✨ Temp data cleaned successfully!", "white", "on_green")
                except Exception as e:
                    self.log(
                        f"⚠️ Error cleaning temp data: {str(e)}", "white", "on_yellow"
                    )

            except Exception as e:
                self.log(f"\n❌ Error in trading cycle: {str(e)}", "white", "on_red")
                self.log(
                    "🔧 Coffee AI suggests checking the logs and trying again!",
                    "white",
                    "on_blue",
                )
            finally:
                self.recommendations_df.to_csv(
                    f"runs/{self.run_id}_recommendations_latest.csv", index=False
                )
                self.log(json.dumps(self.recommendations_df.to_dict()))
                self.status = AgentStatus.SLEEPING

            next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
            self.log(
                f"\n⏳ AI Agent run complete. Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}",
                "white",
                "on_green",
            )
            if not self.__stop:
                time.sleep(SLEEP_BETWEEN_RUNS_MINUTES * 60)


# def main():
#     """Main function to run the trading agent every 15 minutes"""
#     cprint("Coffee AI AI Trading System Starting Up! 🚀", "white", "on_blue")

#     agent = TradingAgent()
#     INTERVAL = SLEEP_BETWEEN_RUNS_MINUTES * 60  # Convert minutes to seconds

#     while True:
#         try:
#             agent.run_trading_cycle()

#             next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
#             cprint(
#                 f"\n⏳ AI Agent run complete. Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}",
#                 "white",
#                 "on_green",
#             )
#             # Sleep until next interval
#             time.sleep(INTERVAL)

#         except KeyboardInterrupt:
#             cprint(
#                 "\n👋 Coffee AI AI Agent shutting down gracefully...", "white", "on_blue"
#             )
#             break
#         except Exception as e:
#             cprint(f"\n❌ Error: {str(e)}", "white", "on_red")
#             cprint(
#                 "🔧 Coffee AI suggests checking the logs and trying again!",
#                 "white",
#                 "on_blue",
#             )
#             # Still sleep and continue on error
#             time.sleep(INTERVAL)


# if __name__ == "__main__":
#     main()
