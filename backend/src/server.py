import json
import os
import random
from os import environ

import uvicorn
from dotenv import find_dotenv, set_key
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

env_path = find_dotenv()
print(f"{env_path=}")

# Import your TradingAgent class and any relevant modules
from src.agents.trading_agent import TradingAgent


def generate_unique_run_id(runs_folder="runs"):
    """
    Generate a unique 10-digit run ID such that no file in the runs folder
    starts with that number.
    """
    # Ensure the folder exists
    os.makedirs(runs_folder, exist_ok=True)

    while True:
        run_id = random.randint(10**9, 10**10 - 1)  # Generates a 10-digit number
        run_id_str = str(run_id)
        existing_files = os.listdir(runs_folder)
        if not any(fname.startswith(run_id_str) for fname in existing_files):
            with open(runs_folder + "/" + run_id_str + "_logs.json", "w") as f:
                f.write("[]")
            return f"{run_id}"


def get_runs_ids(runs_folder="runs"):
    """
    Get a list of all runs in the runs folder.
    """
    # Ensure the folder exists
    os.makedirs(runs_folder, exist_ok=True)
    files = os.listdir(runs_folder)
    names = list(set([file.split("_")[0] for file in files]))
    return names


# Create a single, global instance of the TradingAgent

agent: TradingAgent = None


def update_agent(run_id):
    global agent
    if agent:
        agent.stop()
    agent = TradingAgent(run_id=run_id)
    return agent


# agent.setup(run_id="***")
# Initialize FastAPI
app = FastAPI(title="Coffee Auto Trader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """
    Basic health check or greeting endpoint.
    """
    return {"message": "AI Trading System is up and running!"}


@app.get("/recommendations")
def get_recommendations():
    """
    Returns the current DataFrame of recommendations as JSON.
    """
    # Convert the DataFrame to a list of dictionaries
    data = agent.recommendations_df.to_dict(orient="records")
    return JSONResponse(content=data)


@app.get("/create_new_run")
def start_new_run():
    """
    Starts a new trading run with a unique run ID.
    """
    global agent
    unique_run_id = generate_unique_run_id()
    return {"run_id": unique_run_id, "status": "ready"}


@app.get("/runs")
def get_runs():
    """
    Returns a list of all runs in the runs folder.
    """
    runs = get_runs_ids()
    return {"runs": runs}


@app.get("/runs/{run_id}/logs")
def get_run_logs(run_id: str):
    """
    Returns the logs for a specific run.
    """
    try:
        with open(f"runs/{run_id}_logs.json", "r") as file:
            logs = json.load(file)

    except FileNotFoundError:
        return {"error": "Run ID not found"}
    return {"logs": logs, "status": agent.status if agent else "IDLE"}


class runTradingCycleReq(BaseModel):
    run_id: str | None


@app.post("/run_cycle")
def run_trading_cycle(req: runTradingCycleReq):
    """
    Triggers the trading cycle in the background, so the client doesn't have to wait.
    """
    # Even with an error it mostly returns logs
    run_id = req.run_id
    try:
        if run_id:
            agent = update_agent(run_id)
        agent.run()
    except Exception:
        return {"status": "Error", "logs": []}
    return {"status": "Started"}


class UserFeedbackReq(BaseModel):
    feedback: str


@app.post("/user_feedback")
def user_feedback(req: UserFeedbackReq):
    """
    Endpoint to accept free-form user feedback or recommendations.
    The TradingAgent will parse and incorporate them into the next cycle.
    """
    feedback = req.feedback
    try:
        logs = agent.process_user_input(feedback)
        return {
            "status": "Feedback processed, will be incorporated in the next run",
            "logs": logs,
        }
    except Exception:
        return {"status": "Error processing feedback"}


class Keys(BaseModel):
    BIRDEYE_API_KEY: str | None = None
    ANTHROPIC_KEY: str | None = None
    SOLANA_PRIVATE_KEY: str | None = None
    WALLET_ADDRESS: str | None = None


@app.post("/update-keys")
def update_keys(req: Keys):
    if req.ANTHROPIC_KEY:
        set_key(env_path, "ANTHROPIC_KEY", req.ANTHROPIC_KEY)
        environ["ANTHROPIC_KEY"] = req.ANTHROPIC_KEY
    if req.BIRDEYE_API_KEY:
        set_key(env_path, "BIRDEYE_API_KEY", req.BIRDEYE_API_KEY)
        environ["BIRDEYE_API_KEY"] = req.BIRDEYE_API_KEY
    if req.SOLANA_PRIVATE_KEY:
        set_key(env_path, "SOLANA_PRIVATE_KEY", req.SOLANA_PRIVATE_KEY)
        environ["SOLANA_PRIVATE_KEY"] = req.SOLANA_PRIVATE_KEY
    if req.WALLET_ADDRESS:
        set_key(env_path, "WALLET_ADDRESS", req.WALLET_ADDRESS)
        environ["WALLET_ADDRESS"] = req.WALLET_ADDRESS
    return {"ok": True}


@app.get("/has-keys")
def has_keys():
    k = ["BIRDEYE_API_KEY", "ANTHROPIC_KEY", "SOLANA_PRIVATE_KEY", "WALLET_ADDRESS"]
    has = [x for x in k if environ.get(x)]
    missing = [x for x in k if not environ.get(x)]
    return {"has": has, "missing": missing}


if __name__ == "__main__":
    # Run the server using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
