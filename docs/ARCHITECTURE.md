# Architecture Overview

This document provides a deeper look at RentalAI Copilot's system design, data flows, and key architectural decisions.

---

## System Components

### 1. Frontend (Angular 19)

**Location**: `frontend/src/`

The frontend is a single-page Angular application that:
- Provides a form for customer message, tier, location, and date selection
- Calls the `/quote/run` API endpoint
- Displays the quote breakdown (items, fees, tax, total)
- Shows AI-generated explanation notes
- Supports PDF download and text-to-speech playback

### 2. API Gateway (FastAPI)

**Location**: `backend/app.py`, `backend/routes/`

FastAPI serves as the API gateway and agent controller:
- Validates incoming requests
- Creates tracing records for observability
- Orchestrates the multi-stage agent pipeline
- Returns structured JSON responses

**Middleware**:
- `RequestLoggingMiddleware` — Logs all requests with unique IDs
- `CORSMiddleware` — Allows frontend origins

### 3. Agent Core

**Location**: `backend/core/`

The agent system consists of multiple specialized modules:

| Module | Purpose |
|--------|---------|
| `agent.py` | Main orchestration loop, pricing calculation |
| `item_parser.py` | NLP parsing, fuzzy matching, synonym resolution |
| `pdf_generator.py` | Generate downloadable PDF quotes |
| `tracing.py` | Record agent steps for debugging |
| `exceptions.py` | Custom error types with structured details |

### 4. Database (MySQL 8.0)

**Location**: `backend/db/`

Schema tables:
- `inventory` — SKUs, names, stock levels
- `rates` — Daily/weekly/monthly pricing, delivery fees
- `policies` — Business rules (tax rate, damage waiver %, tier discounts)
- `customers` — Customer records with tier assignment
- `runs` — Agent execution records
- `steps` — Detailed step traces for each run

---

## Data Flow: Quote Generation

```
Customer Input
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /quote/run                                                │
│  {                                                              │
│    "message": "50 chairs and 5 tables for the weekend",        │
│    "customer_tier": "B",                                        │
│    "location": "Dallas, TX"                                     │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Intent Parsing (item_parser.py)                       │
│  ├─ Tokenize message                                            │
│  ├─ Match quantities: "50", "5", "weekend" → 3 days            │
│  ├─ Match items: "chairs" → CHAIR-FOLD-WHT                     │
│  │               "tables" → TABLE-8FT-RECT                     │
│  └─ Output: [{sku, quantity, confidence}, ...]                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Knowledge Retrieval (agent.py)                        │
│  ├─ Fetch pricing policies from MySQL                          │
│  ├─ Fetch rates for each SKU                                   │
│  └─ Fetch inventory names for display                          │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Pricing Calculation (agent.py)                        │
│  ├─ Base: qty × daily_rate × days                              │
│  ├─ Tier discount: tier_discounts[B] = 5%                      │
│  ├─ Damage waiver: 10% of subtotal                             │
│  ├─ Delivery fee: max(delivery_fee_base across items)          │
│  └─ Tax: 9.5% of (subtotal + fees)                             │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Explanation Generation (OpenAI)                       │
│  ├─ Build context: items, tier, discount, total                │
│  ├─ Call GPT-4o-mini with constrained system prompt            │
│  └─ Fallback: Static message if API fails                      │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Response                                                       │
│  {                                                              │
│    "run_id": 42,                                                │
│    "quote": {                                                   │
│      "items": [...],                                            │
│      "subtotal": 897.75,                                        │
│      "fees": [...],                                             │
│      "tax": 105.69,                                             │
│      "total": 1108.44,                                          │
│      "notes": ["AI-generated explanation..."]                   │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Item Parser Design

The item parser (`backend/core/item_parser.py`) is the NLP brain of the system.

### Synonym Mapping

Over 100 synonyms map natural language to SKUs:

```python
ITEM_SYNONYMS = {
    "chair": ["CHAIR-FOLD-WHT"],
    "pa system": ["SPEAKER-PA-PRO"],
    "sound system": ["SPEAKER-PA-PRO"],
    "scissor lift": ["LIFT-SCISSOR-19"],
    ...
}
```

### Quantity Parsing

Handles both numeric and word quantities:

| Input | Parsed |
|-------|--------|
| "50 chairs" | 50 |
| "dozen tables" | 12 |
| "a hundred chairs" | 100 |
| "twenty uplights" | 20 |

### Fuzzy Matching

Uses `difflib.SequenceMatcher` for typo tolerance:

```python
"chiar" → "chair" (similarity: 0.8) → CHAIR-FOLD-WHT
```

### Duration Detection

Extracts rental duration from message:

| Input | Days |
|-------|------|
| "for 5 days" | 5 |
| "weekend event" | 3 |
| "for a week" | 7 |

---

## Pricing Calculation

The pricing engine is **deterministic** — no LLM involvement:

```python
def _compute(items, days, policies, tier):
    # 1. Calculate base subtotal
    for item in items:
        unit_price = daily_rate × days
        subtotal += qty × unit_price

    # 2. Apply tier discount
    discount_pct = policies["tier_discounts"][tier]["pct"]
    subtotal_after_discount = subtotal × (1 - discount_pct)

    # 3. Add fees
    damage_waiver = subtotal_after_discount × 0.10
    delivery_fee = max(delivery_fee_base for each item)

    # 4. Calculate tax
    taxable = subtotal_after_discount + damage_waiver + delivery_fee
    tax = taxable × tax_rate

    # 5. Final total
    total = taxable + tax
```

---

## Observability

### Structured Logging

All logs are JSON-formatted with correlation IDs:

```json
{
  "timestamp": "2024-12-08T10:30:00Z",
  "level": "INFO",
  "message": "Quote computed for run 42",
  "extra_fields": {
    "run_id": 42,
    "subtotal": 897.75,
    "total": 1108.44,
    "item_count": 2
  }
}
```

### Step Tracing

Every agent stage is recorded in the `steps` table:

| Step | Purpose |
|------|---------|
| `normalize` | Input parsing results |
| `policies` | Fetched business rules |
| `pricing` | Calculated quote breakdown |
| `policy_guardrails` | Validation checks |
| `feedback_apply` | Post-feedback adjustments |

Query a run's trace:
```bash
curl http://localhost:8000/quote/runs/42
```

---

## Error Handling

Custom exceptions with structured error responses:

```python
class RentalAIException(Exception):
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or {}
```

Exception types:
- `ValidationError` — Invalid input data
- `DatabaseError` — MySQL connection/query failures
- `AIServiceError` — OpenAI API failures
- `ResourceNotFoundError` — Run/quote not found

---

## Security Considerations

- **No secrets in code** — All API keys via environment variables
- **Input validation** — Pydantic models validate all requests
- **SQL injection prevention** — SQLAlchemy parameterized queries
- **CORS restricted** — Only localhost and GitHub Codespaces origins

---

## Performance

Benchmark results (local Docker, M1 Mac):

| Stage | Latency |
|-------|---------|
| Item parsing | ~8ms |
| Database queries | ~45ms |
| Pricing calculation | ~12ms |
| OpenAI API | ~380ms |
| **Total** | **~450ms** |

The OpenAI call dominates latency. Using `gpt-4o-mini` keeps costs at ~$0.0001/quote.
