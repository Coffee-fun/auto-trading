# Auto Trading Swarms

## Project Structure

```
.
├── backend
│   ├── requirements.txt
│   └── src
│       └── server.py
└── frontend
    ├── package.json
    └── ...
```

## Prerequisites

- **Python 3.x** (tested on Python 3.11)
- **pip** (Python package manager)
- **pnpm** (to install and run the frontend; [installation guide](https://pnpm.io/installation))

---

## Getting Started

1. **Install TA-Lib** (required before installing the Python dependencies):
   - **Windows / Linux**:  
     You may install TA-Lib from its official [installation instructions](https://ta-lib.org/install/) 

2. **Install [`uv`](https://astral.sh/uv)** (or any other environment-specific dependencies):
   ```bash
   pip install uv
   ```

3. Add the following api keys to the [backend](./backend/) directory:
```bash
# backend/.env
RPC_ENDPOINT=https://api.mainnet-beta.solana.com
ANTHROPIC_KEY='sk-ant-...'
BIRDEYE_API_KEY='...'
SOLANA_PRIVATE_KEY='...'
WALLET_ADDRESS='...'
```



## Usage

1. run `python3 run.py`
2. Open your browser and navigate to the URL where the frontend is served (commonly [http://localhost:3000](http://localhost:3000)).

---

