# 🚀 Point of Rental - AI Quote Copilot
<img width="300" height="300" alt="POR" src="https://github.com/user-attachments/assets/74a56f65-3cae-4e79-bbdf-f7630faa02ca" />


### “Are you tired of manually reading every customer email, typing it into POR, and building quotes line by line?”
### Well, now you don’t have to.

Meet AI Quote Copilot - an autonomous quoting system built for Point of Rental, inspired by HumanLayer’s philosophy of agentic automation.
It reads what customers write, understands it like a human, applies pricing logic, and generates a ready-to-review quote — instantly.

# 🧠 The Vision

At Point of Rental, your Customer Service Reps (CSRs) spend hours daily turning unstructured messages into structured rental quotes.

#### What if an AI could do that for them - instantly, consistently, and 24/7?

That’s what this project proves:
A HumanLayer-style AI Operator, trained for the rental domain, that handles the first 80% of quote generation before a human even touches it.

POR could deploy this as an internal Copilot - directly augmenting your existing workflow.

# ⚙️ System Architecture
| Layer                | Tech Stack              | Purpose                                                                                                                                 |
| -------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Frontend**         | Angular 17 + Tailwind 4 | Clean, modern UI matching POR branding. Built with glass panels, live state updates, and an intuitive form layout.                      |
| **Backend**          | FastAPI (Python)        | Core logic: takes free-text requests, runs through the LLM agent pipeline, applies pricing rules, and returns structured quote objects. |
| **Database**         | MySQL / MariaDB         | Stores all runs, quotes, and logs - creating a **data lake** for AI model improvement and auditability.                                 |
| **Containerization** | Docker + Docker Compose | Fully containerized for easy local dev, team onboarding, or deployment to POR cloud environments.                                       |

# 🧩 How It Works - The HumanLayer Way
| HumanLayer Principle            | How Quote Copilot Implements It                                          |
| ------------------------------- | ------------------------------------------------------------------------ |
| 🗣️ **Natural Input**           | Takes raw human messages (“Need 2 light towers this weekend in Dallas”). |
| 🧩 **Structured Understanding** | Extracts items, dates, tiers, and logistics context.                     |
| ⚖️ **Rule Application**         | Applies POR tier-based pricing, taxes, and policies.                     |
| 🧾 **Output Artifact**          | Generates a real quote object — not just text.                           |
| 👩‍💼 **Human Review**          | CSR can approve, adjust, and push to POR core.                           |

Instead of “an AI chat,” this is an AI employee — a virtual quoting assistant.

# 🧱 Backend Overview

## Stack:

* Python 3.11+

* FastAPI

* SQLAlchemy + MySQL

* OpenAI SDK (LLM logic)

* Pydantic for schemas

## Core endpoint:
```
POST /quote/run
```
#### Example payload:
```
{
  "request_text": "Need 3 scissor lifts for next weekend, Arlington TX",
  "customer_tier": "B",
  "location": "Arlington",
  "zip": "76019",
  "start_date": "2025-11-14",
  "end_date": "2025-11-16"
}
```
#### Response:
```
{
  "quote": {
    "items": [
      {"name": "Scissor Lift", "qty": 3, "unitPrice": 120.0, "subtotal": 360.0}
    ],
    "fees": [{"name": "Delivery", "price": 50.0}],
    "total": 410.0,
    "currency": "$",
    "notes": ["Based on weekend rates for Tier B"]
  }
}
```
# 💻 Frontend Overview

## Stack:

Angular 17 (Standalone Components)

TailwindCSS 4 (POR-branded color palette)

TypeScript + RxJS

## Features:

Input form for rental request

Auto-validation (dates, tier, zip, etc.)

Live result card: subtotal, tax, total, and AI notes

Reset + rerun controls

Glassmorphism + dark mode styling

# 🐳 Running Locally (Docker)

Everything is containerized for fast setup.
```
# clone repo
git clone https://github.com/nooraldeen00/point-of-rental-quote-copilot
cd point-of-rental-quote-copilot

# build + run full stack
docker-compose up --build

```

Frontend: http://localhost:4200

Backend API: http://localhost:8000/docs

MySQL: localhost:3306 (preconfigured volume + .env vars)

#### To stop everything:
```
docker-compose down
```

# 📊 Data Layer (MySQL)

Every quote request and AI output can be logged into MySQL for:

* Auditing

* Analytics (quote patterns, common requests, turnaround time)

* Model training (fine-tuning POR-specific agent behavior)

Example table structure:
```
quotes
 ├─ id
 ├─ request_text
 ├─ parsed_items
 ├─ total
 ├─ created_at
 └─ feedback_status
```
This makes the project not just functional - but scalable into a data asset.

# 🧬 Why This Aligns with POR’s Future
| Impact Area    | Benefit                                                      |
| -------------- | ------------------------------------------------------------ |
| CSR Efficiency | Handles quote prep in seconds.                               |
| Accuracy       | Standardized pricing logic and policies.                     |
| Training Data  | Every quote becomes new supervised data for next-gen POR AI. |
| Integration    | Easily connects to POR API or database.                      |
| Brand          | POR becomes a leader in AI-powered rental intelligence.      |

# 🏁 The Takeaway

#### This isn’t a demo - it’s a blueprint for how Point of Rental can embed AI directly into its daily operations.

It’s HumanLayer thinking applied to a real business domain -
an AI that doesn’t just talk - it works.

### Built clean. Built fast. Built for Point of Rental Software. ⚡

# 🙌 Shout-Out

Big shout-out to HumanLayer and Dex Horthy for pioneering the concept of agentic automation - inspiring this build.

Their work showed that AI agents don’t just chat - they can work like humans inside real businesses.
This project brings that same philosophy into the rental industry, showing what’s possible when we bridge AI reasoning with real-world operations.

# 💬 Contact
#### Developer: Nooraldeen Alsmady
#### Role: CS Senior @ UTA • AI + Systems Engineering
#### Email: [nooraldeenalsmady@gmail.com]
#### LinkedIn: https://www.linkedin.com/in/nooraldeen-alsmady-0765a9378
