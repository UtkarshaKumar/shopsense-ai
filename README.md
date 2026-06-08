# B2B Commerce Agent

> A ReAct (Reasoning + Acting) agent for automating B2B eCommerce workflows on SAP Commerce Cloud.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Overview

This project implements a **ReAct agent from scratch** that automates B2B commerce workflows. It connects to a mock SAP Commerce Cloud API (OCC REST) to demonstrate agent capabilities without requiring an SAP license.

**Key Features:**
- 🤖 **ReAct Pattern**: Full reasoning loop (Thought → Action → Observation)
- 🛒 **Commerce Tools**: Inventory check, cart management, order placement
- 🔌 **Mock SAP API**: Realistic OCC REST endpoints for demonstration
- 🎨 **Streamlit UI**: Real-time visualization of agent thinking process
- 🔧 **Extensible**: Swap mock API for real SAP Commerce Cloud

**Why This Matters:**
As a Product Manager, understanding agent architecture at a systems level enables better AI product decisions. This project demonstrates that depth while solving a real B2B commerce problem.

---

## 🚀 Quick Start

```bash
# Clone and navigate to project
cd b2b-commerce-agent

# Install dependencies
pip install -r requirements.txt

# Start the mock SAP Commerce API
python -m src.api.mock_sap_api

# In another terminal, start the agent UI
streamlit run src/ui/streamlit_app.py
```

Open http://localhost:8501 to see the demo.

---

## 📁 Project Structure

```
b2b-commerce-agent/
├── specs/
│   └── b2b-commerce-agent.md     # Feature specification (Multi-Agent SWE Workflow)
├── workflow/                      # Multi-Agent SWE Workflow tooling
│   ├── orchestrate.sh
│   ├── WORKFLOW.md
│   └── ...
├── src/
│   ├── agent/
│   │   └── react_agent.py        # Core ReAct loop implementation
│   ├── tools/
│   │   └── commerce_tools.py     # B2B commerce tool definitions
│   ├── api/
│   │   └── mock_sap_api.py       # Mock SAP Commerce OCC API
│   ├── llm/
│   │   └── llm_client.py         # LLM integration (OpenAI)
│   ├── ui/
│   │   └── streamlit_app.py      # Portfolio demo interface
│   └── data/
│       ├── products.json         # Product catalog
│       ├── customers.json        # B2B customer accounts
│       └── inventory.json        # Stock levels
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

---

## 🎬 Demo

### Example Workflow

**Input:** *"Check if customer ACME-123 has latex gloves in stock and add 100 units to their cart"*

**Agent Thinking:**
```
Thought: I need to look up customer ACME-123 first to understand their account.
Action: customer_lookup({"customer_id": "ACME-123"})
Observation: Customer found. Name: ACME Medical Supplies. Preferred warehouse: CA-01.

Thought: Now I need to find the product code for latex gloves.
Action: product_search({"query": "latex gloves"})
Observation: Found 1 product: SKU-LG-001 - Latex Examination Gloves (Box of 100)

Thought: Now I'll check inventory at the customer's preferred warehouse.
Action: inventory_check({"product_code": "SKU-LG-001", "warehouse": "CA-01"})
Observation: Stock level: 500 units available

Thought: Good, there's sufficient stock. I'll create a cart and add 100 units.
Action: cart_create({"customer_id": "ACME-123"})
Observation: Cart created. ID: cart-78291

Thought: Now add the items to the cart.
Action: cart_add_item({"cart_id": "cart-78291", "product_code": "SKU-LG-001", "quantity": 100})
Observation: Items added. Cart total: $450.00

Final Answer: I've checked inventory for ACME-123 and added 100 units of latex gloves (SKU-LG-001) to cart-78291. The cart total is $450.00. Would you like to place the order?
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  STREAMLIT UI                                               │
│  - Natural language input                                   │
│  - Real-time thought visualization                          │
│  - Action history display                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  REACT AGENT CORE                                           │
│  - ReAct loop: Thought → Action → Observation              │
│  - Tool registry with validation                            │
│  - LLM integration (OpenAI GPT-4/Claude)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  COMMERCE TOOLS                                             │
│  - inventory_check                                          │
│  - customer_lookup                                          │
│  - cart_create / cart_add_item                              │
│  - place_order                                              │
│  - product_search                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  MOCK SAP COMMERCE API                                      │
│  - OCC REST endpoints                                       │
│  - Realistic JSON responses                                 │
│  - Swap for real SAP Commerce via config                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **Python 3.10+**: Core language
- **OpenAI API**: LLM for reasoning (GPT-4 or Claude)
- **FastAPI**: Mock SAP Commerce API
- **Streamlit**: Demo UI
- **Pydantic**: Data validation
- **Pytest**: Testing

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

---

## 📚 Learning Resources

### ReAct Pattern
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [LangChain ReAct Documentation](https://python.langchain.com/docs/modules/agents/agent_types/react)

### SAP Commerce Cloud
- [SAP Commerce OCC REST API](https://help.sap.com/docs/SAP_COMMERCE_CLOUD_PUBLIC_CLOUD/6596768252f0494d978574016c68738b/5c207d4dbb1e4914bf18f405d0918c0f.html)
- [OCC API Tutorial](https://help.sap.com/docs/SAP_COMMERCE/9d346683b0084f2939c25d7a9842f53a/8c1c194e8669101492b6c78d070e3099.html)

---

## 🔮 Future Enhancements

- [ ] Real SAP Commerce Cloud connector
- [ ] Multi-agent orchestration (router + specialist agents)
- [ ] Persistent conversation memory
- [ ] Function calling with actual SAP IDoc/BAPI integration
- [ ] Voice interface using Whisper + TTS

---

## 👤 Author

**Utkarsh Kumar**
- B2B eCommerce & AI Enablement specialist
- [Portfolio](https://utkarshakumar.github.io/) | [LinkedIn](https://linkedin.com/in/utkkumar)

---

## 📝 License

MIT License — feel free to use this as a template for your own projects.

---

*Built with the Multi-Agent SWE Workflow: Builder + Reviewer agents, quality gates, and structured review cycles.*


---

> **Attribution Notice**
> Cloning, copying, or reusing this code or design without credit is a copyright violation. If you use any part of this work, you must attribute the original author and link back to this repository.
> © Utkarsha Kumar. All rights reserved.
