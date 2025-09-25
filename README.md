# PromptProof 🧾

**PromptProof** is a FastAPI application that generates cryptographically verifiable receipts for AI responses. Every AI interaction is recorded with a tamper-proof SHA256 hash, providing transparency and authenticity verification for AI-generated content.

## Overview

PromptProof addresses the growing need for AI transparency by:

- **🔐 Cryptographic Verification**: Each AI response gets a SHA256 hash computed from timestamp, model, prompt, and response
- **📊 Persistent Storage**: All receipts are stored in SQLite with unique hash constraints
- **🌐 Web Interface**: Simple frontend for testing and downloading receipts
- **✅ Verification Tools**: Standalone script to verify receipt authenticity
- **🔄 RESTful API**: Easy integration with existing systems

Perfect for scenarios requiring AI audit trails, content verification, or compliance documentation.

## How to Run Locally

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
# Clone and navigate to the project
git clone <repository-url>
cd promptproof

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

Create a `.env` file in the project root:

```bash
# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

Replace `your_openai_api_key_here` with your actual OpenAI API key.

### 3. Start the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- **API**: `http://localhost:8000`
- **Frontend**: `http://localhost:8000/static/index.html`
- **API Docs**: `http://localhost:8000/docs`

## How to Generate a Receipt

### Via Web Interface

1. Open `http://localhost:8000/static/index.html`
2. Enter your prompt in the textarea
3. Click "Generate Response"
4. View the AI response and cryptographic receipt

### Via API

```bash
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Explain quantum computing"}'
```

**Response format:**
```json
{
  "id": 1,
  "timestamp": "2025-09-25T10:30:45.123Z",
  "model": "gpt-4o-mini",
  "prompt": "Explain quantum computing",
  "response": "Quantum computing is...",
  "hash": "abc123...def789"
}
```

## How to View Stored Receipts

### Retrieve by ID

```bash
curl "http://localhost:8000/receipts/1"
```

### Database Access

Receipts are stored in `receipts.db` (SQLite):

```bash
sqlite3 receipts.db "SELECT id, timestamp, model FROM receipts;"
```

## How to Export/Download Receipts

### From Web Interface

1. Generate a receipt via the web interface
2. Click the **"📄 Download Receipt"** button
3. Receipt saves as `receipt_<timestamp>.json`

### Manual Export

```bash
# Export specific receipt via API
curl "http://localhost:8000/receipts/1" > receipt_1.json
```

## How to Verify Receipts with verify.py

The `verify.py` script provides cryptographic verification of receipt authenticity:

### Basic Usage

```bash
python verify.py receipt_2025-09-25T10-30-45-123Z.json
```

### Example Output

**Valid receipt:**
```
🔍 Verifying receipt: receipt_2025-09-25T10-30-45-123Z.json
--------------------------------------------------
Receipt is valid ✅
✓ Timestamp: 2025-09-25T10:30:45.123Z
✓ Model: gpt-4o-mini
✓ Hash: abc123...def789
```

**Tampered receipt:**
```
🔍 Verifying receipt: tampered_receipt.json
--------------------------------------------------
Tampered ❌
❌ Expected hash: abc123...def789
❌ Computed hash: xyz456...uvw012
```

### How Verification Works

1. **Hash Recomputation**: `SHA256(timestamp + model + prompt + response)`
2. **Comparison**: Computed hash vs. stored hash
3. **Result**: Valid ✅ or Tampered ❌

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information and frontend link |
| `GET` | `/health` | Health check |
| `POST` | `/generate` | Generate AI response with receipt |
| `GET` | `/receipts/{id}` | Retrieve stored receipt by ID |
| `GET` | `/static/index.html` | Web frontend |

## Project Structure

```
promptproof/
├── app/
│   └── main.py           # FastAPI application
├── static/
│   └── index.html        # Web frontend
├── verify.py             # Receipt verification script
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (create this)
├── receipts.db          # SQLite database (auto-created)
└── README.md            # This file
```

## Dependencies

- **FastAPI**: Web framework and API
- **SQLAlchemy**: Database ORM
- **OpenAI**: AI model integration
- **python-dotenv**: Environment variable loading
- **Uvicorn**: ASGI server

## Security Notes

- Store your OpenAI API key securely in `.env`
- The `.env` file is gitignored for security
- Receipts use SHA256 for cryptographic integrity
- Database uses unique constraints on hashes to prevent duplicates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please check the license file for details.