# API Reference

Base URL: `http://localhost:8000`

---

## Health Check

### `GET /health`

Returns service health status.

**Response**
```json
{
  "status": "healthy",
  "service": "RentalAI Copilot API"
}
```

---

## Quote Endpoints

### `POST /quote/run`

Generate a quote from natural language or structured input.

**Request Body**
```json
{
  "message": "50 chairs and 5 round tables for a weekend corporate event",
  "customer_tier": "B",
  "location": "Dallas, TX",
  "zip": "75201",
  "start_date": "2024-12-15",
  "end_date": "2024-12-17",
  "items": [],
  "seed": 0
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes* | Natural language request |
| `customer_tier` | string | No | "A", "B", or "C" (default: "C") |
| `location` | string | No | City/state for delivery |
| `zip` | string | No | ZIP code |
| `start_date` | string | No | ISO date (YYYY-MM-DD) |
| `end_date` | string | No | ISO date (YYYY-MM-DD) |
| `items` | array | Yes* | Explicit items list |
| `seed` | integer | No | Random seed for reproducibility |

*Either `message` or `items` must be provided.

**Response**
```json
{
  "run_id": 42,
  "quote": {
    "currency": "$",
    "items": [
      {
        "sku": "CHAIR-FOLD-WHT",
        "name": "White Folding Chair",
        "qty": 50,
        "days": 3,
        "dailyRate": 4.50,
        "unitPrice": 13.50,
        "subtotal": 675.00
      },
      {
        "sku": "TABLE-60RND",
        "name": "60\" Round Table",
        "qty": 5,
        "days": 3,
        "dailyRate": 18.00,
        "unitPrice": 54.00,
        "subtotal": 270.00
      }
    ],
    "subtotal": 897.75,
    "fees": [
      {"name": "Damage Waiver", "amount": 89.78},
      {"name": "Delivery & Pickup", "amount": 35.00}
    ],
    "tax": 97.14,
    "total": 1119.67,
    "notes": [
      "We're pleased to prepare your corporate event equipment! Your order includes 50 folding chairs and 5 round tables for a 3-day weekend rental. As a corporate customer, we've applied your 5% tier discount."
    ]
  }
}
```

**Example cURL**
```bash
curl -X POST http://localhost:8000/quote/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Need a scissor lift and generator for 5 days",
    "customer_tier": "B"
  }'
```

---

### `GET /quote/runs/{run_id}`

Retrieve the step-by-step trace of a quote run (useful for debugging).

**Response**
```json
{
  "run_id": 42,
  "steps": [
    {
      "id": 101,
      "kind": "normalize",
      "input_json": {"payload": {}},
      "output_json": {"items": [], "days": 3, "tier": "B"},
      "latency_ms": 5
    },
    {
      "id": 102,
      "kind": "policies",
      "input_json": {},
      "output_json": {"tier_discounts": {}, "tax_rate": {}},
      "latency_ms": 12
    },
    {
      "id": 103,
      "kind": "pricing",
      "input_json": {"items": [], "days": 3},
      "output_json": {"subtotal": 897.75, "total": 1119.67},
      "latency_ms": 45
    }
  ]
}
```

---

### `GET /quote/runs/{run_id}/pdf`

Download the quote as a PDF file.

**Response**: PDF binary with headers:
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="quote-42.pdf"`

**Example cURL**
```bash
curl -o quote.pdf http://localhost:8000/quote/runs/42/pdf
```

---

### `POST /quote/feedback`

Submit feedback for a quote. If rating <= 3, a 10% goodwill discount is automatically applied.

**Request Body**
```json
{
  "run_id": 42,
  "rating": 2,
  "note": "Price seems high for this quantity"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | integer | Yes | The quote run ID |
| `rating` | integer | Yes | 1-5 rating |
| `note` | string | No | Optional feedback text |

**Response**
```json
{
  "run_id": 42,
  "quote": {
    "currency": "$",
    "items": [],
    "subtotal": 897.75,
    "fees": [
      {"name": "Damage Waiver", "amount": 89.78},
      {"name": "Delivery & Pickup", "amount": 35.00},
      {"rule": "goodwill_discount", "amount": -89.78}
    ],
    "tax": 97.14,
    "total": 1029.89,
    "notes": []
  }
}
```

---

## Inventory Endpoints

### `GET /inventory`

List all inventory items with current stock levels.

**Response**
```json
{
  "items": [
    {
      "sku": "CHAIR-FOLD-WHT",
      "name": "White Folding Chair",
      "location": "Dallas",
      "on_hand": 500,
      "committed": 50,
      "available": 450
    }
  ]
}
```

### `GET /inventory/{sku}`

Get details for a specific SKU.

**Response**
```json
{
  "sku": "CHAIR-FOLD-WHT",
  "name": "White Folding Chair",
  "location": "Dallas",
  "on_hand": 500,
  "committed": 50,
  "available": 450,
  "rates": {
    "daily": 4.50,
    "weekly": 22.50,
    "monthly": 67.50,
    "delivery_fee_base": 25.00
  }
}
```

---

## Text-to-Speech Endpoints

### `POST /tts/speak`

Generate audio from the quote explanation using ElevenLabs.

**Request Body**
```json
{
  "text": "Your quote for 50 chairs and 5 tables is ready...",
  "voice_id": "optional-voice-id"
}
```

**Response**: Audio binary (MP3) with headers:
- `Content-Type: audio/mpeg`

> Note: Requires `ELEVENLABS_API_KEY` in environment.

---

## Error Responses

All errors return structured JSON:

```json
{
  "error": "ValidationError",
  "message": "Either 'message' or 'items' must be provided",
  "details": {
    "request_id": "abc123"
  }
}
```

| HTTP Status | Error Type | Description |
|-------------|------------|-------------|
| 400 | ValidationError | Invalid input data |
| 404 | ResourceNotFoundError | Run/quote not found |
| 500 | DatabaseError | MySQL connection failure |
| 500 | AIServiceError | OpenAI API failure |
| 500 | QuoteGenerationError | General quote failure |

---

## Rate Limits

No rate limiting is implemented in this demo. For production:
- Recommend: 100 requests/minute per IP
- OpenAI costs: ~$0.0001 per quote (GPT-4o-mini)
