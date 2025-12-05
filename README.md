# 🚀 RentalAI Copilot
<img width="300" height="300" alt="RentalAI Copilot" src="https://github.com/user-attachments/assets/74a56f65-3cae-4e79-bbdf-f7630faa02ca" />


### "Are you tired of manually reading every customer email, typing it into your rental system, and building quotes line by line?"
### Well, now you don't have to.

Meet RentalAI Copilot - an autonomous quoting system for the equipment rental industry, inspired by HumanLayer's philosophy of agentic automation.
It reads what customers write, understands it like a human, applies pricing logic, and generates a ready-to-review quote - instantly.

# 🧠 The Vision

In the equipment rental industry, Customer Service Reps (CSRs) spend hours daily turning unstructured messages into structured rental quotes.

#### What if an AI could do that for them - instantly, consistently, and 24/7?

That's what this project proves:
A HumanLayer-style AI Operator, trained for the rental domain, that handles the first 80% of quote generation before a human even touches it.

Rental companies can deploy this as an internal Copilot - directly augmenting existing workflows.

# ⚙️ System Architecture
| Layer                | Tech Stack              | Purpose                                                                                                                                 |
| -------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Frontend**         | Angular 20 + Custom CSS | Clean, modern UI. Built with glass panels, live state updates, and an intuitive form layout.                      |
| **Backend**          | FastAPI (Python)        | Core logic: takes free-text requests, runs through the LLM agent pipeline, applies pricing rules, and returns structured quote objects. |
| **Database**         | MySQL / MariaDB         | Stores all runs, quotes, and logs - creating a **data lake** for AI model improvement and auditability.                                 |
| **Containerization** | Docker + Docker Compose | Fully containerized for easy local dev, team onboarding, or cloud deployment.                                       |

# 🧩 How It Works - The HumanLayer Way
| HumanLayer Principle            | How RentalAI Copilot Implements It                                          |
| ------------------------------- | ------------------------------------------------------------------------ |
| 🗣️ **Natural Input**           | Takes raw human messages ("Need 2 light towers this weekend in Dallas"). |
| 🧩 **Structured Understanding** | Extracts items, dates, tiers, and logistics context.                     |
| ⚖️ **Rule Application**         | Applies tier-based pricing, taxes, and policies.                     |
| 🧾 **Output Artifact**          | Generates a real quote object — not just text.                           |
| 👩‍💼 **Human Review**          | CSR can approve, adjust, and push to rental management system.                           |

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

TailwindCSS 4 (RentalAI-branded color palette)

TypeScript + RxJS

## Features:

Input form for rental request

Auto-validation (dates, tier, zip, etc.)

Live result card: subtotal, tax, total, and AI notes

Reset + rerun controls

Glassmorphism + dark mode styling

# 🚀 Getting Started

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker & Docker Compose** (recommended for quickest setup)
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **OR** for local development:
  - **Node.js** 20+ & npm ([Download](https://nodejs.org/))
  - **Python** 3.11+ ([Download](https://www.python.org/downloads/))
  - **MySQL** 8.0+ ([Download](https://dev.mysql.com/downloads/mysql/))

You'll also need:
- **OpenAI API Key** - Get one at [platform.openai.com](https://platform.openai.com/api-keys)

---

## ⚡ Quick Start (Docker - Recommended)

The fastest way to get running with everything containerized:

### 1. Clone the repository
```bash
git clone https://github.com/nooraldeen00/point-of-rental-quote-copilot
cd point-of-rental-quote-copilot
```

### 2. Configure environment variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Required: OPENAI_API_KEY=sk-proj-xxxxx...
```

### 3. Start the application
```bash
# Build and start all services (frontend, backend, database)
docker-compose up --build
```

**Access the application:**
- 🎨 **Frontend:** http://localhost:4200
- 🔧 **Backend API Docs:** http://localhost:8000/docs
- 🗄️ **MySQL:** localhost:3306 (credentials: `por`/`por`)

### 4. Stop the application
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

---

## 💻 Local Development (Without Docker)

If you prefer to run services locally for development:

### 1. Clone and configure
```bash
git clone https://github.com/nooraldeen00/point-of-rental-quote-copilot
cd point-of-rental-quote-copilot

# Create environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Set up MySQL database
```bash
# Start MySQL and create database
mysql -u root -p
```
```sql
CREATE DATABASE por;
CREATE USER 'por'@'localhost' IDENTIFIED BY 'por';
GRANT ALL PRIVILEGES ON por.* TO 'por'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# Load schema and seed data
mysql -u por -p por < backend/db/schema.sql
mysql -u por -p por < backend/db/seed.sql
```

### 3. Start the backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 4. Start the frontend
```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will be available at: http://localhost:4200

---

## 🔧 Configuration

### Backend Configuration (`.env`)

All backend configuration is done via environment variables:

```bash
# Required
OPENAI_API_KEY=sk-proj-xxxxx              # Your OpenAI API key

# Optional - LLM Configuration
LLM_PROVIDER=openai                       # openai or anthropic
LLM_MODEL=gpt-4o-mini                     # Model to use

# Optional - Database (auto-configured in Docker)
DATABASE_URL=mysql+pymysql://por:por@localhost:3306/por
```

See `.env.example` for all available options.

### Frontend Configuration

Frontend API URL is configured via Angular environments:

- **Development:** `frontend/src/environments/environment.ts`
  - Default: `http://localhost:8000`

- **Production:** `frontend/src/environments/environment.prod.ts`
  - Update `apiUrl` before deploying

---

# 📊 Data Layer (MySQL)

Every quote request and AI output can be logged into MySQL for:

* Auditing

* Analytics (quote patterns, common requests, turnaround time)

* Model training (fine-tuning RentalAI-specific agent behavior)

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

# 🧬 Benefits for Rental Companies
| Impact Area    | Benefit                                                      |
| -------------- | ------------------------------------------------------------ |
| CSR Efficiency | Handles quote prep in seconds.                               |
| Accuracy       | Standardized pricing logic and policies.                     |
| Training Data  | Every quote becomes new supervised data for continuous AI improvement. |
| Integration    | Easily connects to existing rental management systems.                      |
| Brand          | Demonstrates leadership in AI-powered rental intelligence.      |

# 🏁 The Takeaway

#### This isn't a demo - it's a blueprint for how rental companies can embed AI directly into daily operations.

It's HumanLayer thinking applied to a real business domain -
an AI that doesn't just talk - it works.

### Built clean. Built fast. Built for the rental industry. ⚡

# 🙌 Shout-Out

Big shout-out to HumanLayer and Dex Horthy for pioneering the concept of agentic automation - inspiring this build.

Their work showed that AI agents don’t just chat - they can work like humans inside real businesses.
This project brings that same philosophy into the rental industry, showing what’s possible when we bridge AI reasoning with real-world operations.

# 💬 Contact
#### Developer: Nooraldeen Alsmady
#### Role: CS Senior @ UTA • AI + Systems Engineering
#### Email: nooraldeenalsmady@gmail.com
#### LinkedIn: https://www.linkedin.com/in/nooraldeen-alsmady-0765a9378
