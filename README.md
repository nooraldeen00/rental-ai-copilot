# 🚀 Point of Rental — AI Quote Copilot

### “Are you tired of manually reading every customer email, typing it into POR, and building quotes line by line?”
### Well, now you don’t have to.

Meet AI Quote Copilot — an autonomous quoting system built for Point of Rental, inspired by HumanLayer’s philosophy of agentic automation.
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

FastAPI

SQLAlchemy + MySQL

OpenAI SDK (LLM logic)

Pydantic for schemas


