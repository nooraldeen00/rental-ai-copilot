
<img width="300" height="300" alt="rentalAi-logo" src="https://github.com/user-attachments/assets/90019441-56f6-457e-bada-a8f4ed67a1ee" />

# RentalAI Copilot

**Autonomous AI Agent for Equipment Rental Quote Generation**

An intelligent agent system that transforms natural language into fully-priced rental quotes using multi-stage reasoning, knowledge retrieval, and GPT-4 orchestration. Built to demonstrate production-grade AI agent architecture in B2B SaaS.

> "I need a dozen tables and hundred chairs for a weekend event"
> → **Complete quote in <1 second**: $1,630.25 • 100 chairs • 12 tables • 3 days
> → Professional AI-generated explanation • Zero human intervention

---

## The Problem

Equipment rental companies process hundreds of quote requests daily. Customer Service Representatives spend **5-10 minutes per quote**:

- Interpreting vague requests ("need some chairs and tables for an event")
- Looking up SKUs from 1000+ inventory items across catalogs
- Calculating pricing (multi-day rates, volume discounts, customer tiers)
- Adding fees (delivery zones, damage waiver, tax)
- Writing professional explanations for customers

**Manual quoting doesn't scale. Errors cost revenue. Response time impacts conversion.**

RentalAI Copilot deploys an autonomous AI agent that handles the entire workflow in under 1 second.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Angular 19 + TypeScript | Interactive quote interface |
| Backend | FastAPI (Python 3.12) | API gateway & agent orchestration |
| Database | MySQL 8.0 | Inventory, pricing, and quote history |
| AI/LLM | OpenAI GPT-4o-mini | Natural language explanation generation |
| TTS | ElevenLabs API | Professional voice synthesis (multi-language) |
| Infrastructure | Docker Compose | Multi-container deployment |

---

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (recommended)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- Node.js 18+ (for local frontend development)

### 1. Clone & Configure

```bash
git clone https://github.com/nooraldeen00/rental-ai-copilot.git
cd rental-ai-copilot

# Copy environment template and add your OpenAI key
cp .env.example .env
# Edit .env and set: OPENAI_API_KEY=sk-proj-...
```

### 2. Start Backend Services (Docker)

```bash
docker-compose up -d
```

This starts:
- **MySQL 8.0** with pre-seeded inventory (30 items) and pricing policies
- **FastAPI backend** on `http://localhost:8000`

### 3. Start Frontend

```bash
cd frontend
npm install
npm start
```

Open **http://localhost:4200** in your browser.

### 4. Test It Out

Try this input:
```
Need 50 white folding chairs and 5 round tables for a corporate event this weekend
```

Set:
- **Tier**: B (Corporate - 5% discount)
- **Location**: Dallas, TX

Expected result:
- Parsed: 50x CHAIR-FOLD-WHT, 5x TABLE-60RND
- Duration: 3 days (weekend detected)
- Tier B discount: 5% applied
- AI explanation: Professional CSR-style summary

---

## How It Works

### Architecture Overview

```
┌──────────────┐     HTTP POST      ┌─────────────────────────────┐
│   Angular    │ ─────────────────► │   FastAPI Gateway           │
│   Frontend   │   /quote/run       │   (Agent Controller)        │
└──────────────┘                    └───────────┬─────────────────┘
                                                │
                    ┌───────────────────────────┴────────────────┐
                    ▼                                            ▼
        ┌───────────────────────┐             ┌──────────────────────────┐
        │  NLP Parsing Agent    │             │  Pricing Agent           │
        │  (item_parser.py)     │             │  (agent.py)              │
        │                       │             │                          │
        │  • 200+ synonyms      │             │  • Tier discount logic   │
        │  • Fuzzy matching     │             │  • Fee calculation       │
        │  • Size normalization │             │  • Tax computation       │
        └───────────┬───────────┘             └──────────┬───────────────┘
                    │                                     │
                    └─────────────┬───────────────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │   MySQL Knowledge Base  │
                    │   • 30 inventory SKUs   │
                    │   • Pricing policies    │
                    │   • Customer tiers      │
                    └─────────────┬───────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
        ┌──────────────────────┐   ┌─────────────────────┐
        │  Explanation Agent   │   │  Structured Logging │
        │  (OpenAI GPT-4o)     │   │  (JSON traces)      │
        └──────────────────────┘   └─────────────────────┘
```

### Multi-Stage Agent Pipeline

Unlike simple chatbots, RentalAI uses a **deterministic multi-stage pipeline**:

1. **Intent Understanding** — Extract items, quantities, and duration from natural language
2. **Knowledge Retrieval** — Query MySQL for SKU pricing and business rules
3. **Pricing Calculation** — Apply tier discounts, fees, and tax (no LLM involved)
4. **Explanation Generation** — GPT-4 produces a professional 2-3 sentence summary

**Why this matters**: Pricing is *deterministic* (from the database), not hallucinated by the LLM.

---

## Multi-Language Support

RentalAI supports **4 languages** for both AI-generated summaries and text-to-speech:

| Language | Code | AI Summary | TTS Voice |
|----------|------|------------|-----------|
| English | en-US | Native GPT-4 | Rachel (ElevenLabs) |
| Spanish | es-ES | Native GPT-4 | Domi (ElevenLabs) |
| Arabic | ar-SA | Native GPT-4 | Yosef (ElevenLabs) |
| Japanese | ja-JP | Native GPT-4 | Alice (ElevenLabs) |

When you switch languages in the UI:
- The AI explanation is **generated natively** in the target language (not translated)
- Text-to-speech uses a **native speaker voice** for natural pronunciation
- Technical notes remain consistent across languages

---

## Intelligent Item Parsing

The NLP parser handles diverse input formats with **200+ item synonyms**:

**Quantity Formats:**
- Numeric: `50 chairs`, `100 chairs`
- Word numbers: `ten speakers`, `twenty tables`
- Compound: `a dozen tables`, `half dozen chairs`
- Prefix format: `5x tables`, `qty 10 chairs`
- Natural phrases: `Need 10 speakers`, `Get me 5 tents`

**Size Specifications:**
- `60-inch round tables` → TABLE-60RND
- `8ft rectangular tables` → TABLE-8FT-RECT
- `60" round tables` → TABLE-60RND
- `20x20 tent` → TENT-20x20

**Duration Detection:**
- `weekend event` → 3 days
- `Friday through Sunday` → 3 days
- `for a week` → 7 days
- `5 day rental` → 5 days

---

## Tier-Based Pricing

Customer tiers affect discount rates:

| Tier | Name | Discount | Use Case |
|------|------|----------|----------|
| A | Premium | 15% | VIP/long-term customers |
| B | Corporate | 5% | Business accounts |
| C | Standard | 0% | Walk-in/new customers |

The AI explanation dynamically mentions discounts only when relevant:

> *"As a valued corporate customer, we've applied your 5% tier discount to this order..."*

---

## AI Explanation Generation

The explanation agent uses a **constrained prompt** to ensure quality:

```python
system_prompt = """You are a professional CSR for a premium rental company.
Generate a concise explanation that:
1. Acknowledges what the customer requested
2. Explains the equipment provided (WITHOUT listing exact prices)
3. Mentions tier discount ONLY if tier is A or B
4. Keep to 2-3 sentences maximum

NEVER hallucinate items not in the quote.
NEVER mention specific dollar amounts."""
```

**Fallback handling**: If OpenAI is unavailable, a static professional message is returned.

---

## Configuration

All configuration via `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-proj-...

# Optional: ElevenLabs TTS (for "Read Summary" feature)
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here

# Optional (auto-configured in Docker)
DATABASE_URL=mysql+pymysql://por:por@db:3306/por
LLM_MODEL=gpt-4o-mini          # or gpt-4o for higher quality
LOG_LEVEL=INFO
```

**Note**: If `ELEVENLABS_API_KEY` is not set, the TTS feature will return a 503 error with a helpful message.

---

## Running Without Docker (Optional)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start MySQL locally and create database
mysql -u root -e "CREATE DATABASE por;"
mysql -u root por < db/schema.sql
mysql -u root por < db/seed.sql

# Set environment
export DATABASE_URL=mysql+pymysql://root@localhost:3306/por
export OPENAI_API_KEY=sk-proj-...

# Run
uvicorn backend.app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## API Reference

See [`docs/API.md`](docs/API.md) for complete endpoint documentation.

### Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /quote/run` | POST | Generate quote from natural language |
| `GET /quote/runs/{id}` | GET | Get quote run history/steps |
| `GET /quote/runs/{id}/pdf` | GET | Download quote as PDF |
| `POST /quote/feedback` | POST | Submit rating (triggers goodwill discount if low) |
| `GET /inventory` | GET | List all inventory items |
| `POST /tts/speak` | POST | Convert text to speech (ElevenLabs) |
| `GET /tts/status` | GET | Check TTS service availability |
| `GET /health` | GET | Health check |

---

## Project Structure

```
rental-ai-copilot/
├── backend/
│   ├── core/
│   │   ├── agent.py              # Main quote orchestration
│   │   ├── item_parser.py        # NLP parsing (200+ synonyms)
│   │   ├── pdf_generator.py      # Quote PDF export
│   │   ├── logging_config.py     # Structured JSON logging
│   │   └── exceptions.py         # Custom error handling
│   ├── routes/
│   │   ├── quote.py              # /quote/* endpoints
│   │   ├── inventory.py          # /inventory endpoints
│   │   └── tts.py                # Text-to-speech (ElevenLabs)
│   ├── db/
│   │   ├── schema.sql            # Database schema
│   │   └── seed.sql              # 30 inventory items + policies
│   └── app.py                    # FastAPI entry point
├── frontend/                     # Angular 19 application
├── docs/
│   ├── ARCHITECTURE.md           # Detailed system design
│   └── API.md                    # API reference
├── docker-compose.yml            # Multi-container setup
└── .env.example                  # Environment template
```

---

## Integration with Real Rental Systems

This demo architecture is designed to integrate with enterprise rental platforms like **Point of Rental**:

```
┌─────────────────────────────────────────────────┐
│     Point of Rental / ERP System                │
│  • Inventory Management  • Delivery Scheduling  │
│  • Customer Database     • Invoicing & Payments │
└──────────────────┬──────────────────────────────┘
                   │ REST API / Webhook
                   ▼
┌─────────────────────────────────────────────────┐
│     RentalAI Agent Layer (This Project)         │
│  • Natural language understanding               │
│  • AI-powered quote generation                  │
│  • Tier-based pricing intelligence              │
└─────────────────────────────────────────────────┘
```

**Value Proposition**:

| Metric | Before (Manual) | After (AI Agent) |
|--------|----------------|------------------|
| Quote time | 5-10 minutes | <1 second |
| Error rate | 5-10% | <1% |
| After-hours | Unavailable | 24/7 self-service |

---

## Future Improvements

- [ ] **Real-time inventory availability** — Check stock before quoting
- [ ] **Multi-location support** — Route to nearest warehouse
- [ ] **Recommendation engine** — "Customers who rent tents also need..."
- [ ] **Negotiation agent** — Handle customer counteroffers
- [ ] **Analytics dashboard** — Quote conversion tracking
- [ ] **Seasonal pricing** — Automatic peak/off-peak rate adjustment

---

## The Interview Story

> **"Tell me about a project you're proud of"**

I built RentalAI Copilot, an autonomous AI agent system for equipment rental companies. The problem: CSRs spend 5-10 minutes manually generating quotes from vague requests like "need some chairs for an event."

**My solution**: A multi-stage agent architecture that:
1. Parses natural language using fuzzy matching + 200+ synonyms with size normalization
2. Retrieves pricing from MySQL with business logic (tier discounts, fees)
3. Calculates quotes *deterministically* (no hallucinations)
4. Generates professional explanations with GPT-4 in **4 languages** (en, es, ar, ja)
5. Provides natural TTS output using ElevenLabs native-speaker voices

**Key decisions**:
- **Hybrid architecture**: Symbolic pricing + neural NLP (best of both worlds)
- **Multi-stage reasoning**: Not a single LLM call — observable, debuggable
- **Native multi-language**: AI generates in target language, not translated
- **Graceful degradation**: Static fallback if OpenAI/ElevenLabs unavailable
- **Production patterns**: Structured logging, request tracing, Docker deployment

This demonstrates I can build *real AI systems*, not just prompt wrappers.

---

## License

MIT License

---

### Designed, engineered, and shipped by Nooraldeen Alsmady  
Full-Stack • AI/ML Systems Engineer

