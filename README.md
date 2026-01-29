# 🐋 WhaleTracker SaaS

**WhaleTracker** is a powerful SaaS platform designed to monitor and track large cryptocurrency transactions ("Whales") across multiple EVM blockchains in real-time. Built with **Python** and **Streamlit**.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red)
![Database](https://img.shields.io/badge/Database-SQLAlchemy-green)

## 🚀 Key Features

### 💎 Multi-Tier SaaS System
- **Free Tier:** Basic access with limited tracking slots.
- **Pro Tier:** Unlocks API access, Telegram alerts, and custom network management.
- **Enterprise Tier:** Unlimited access with dedicated Webhook integration and full admin controls.

### 🛠️ Core Functionality
- **Real-Time Monitoring:** A dedicated background engine (`engine.py`) scans blockchains for transactions matching user criteria.
- **Custom RPC Support:** Pro/Enterprise users can add their own private RPC nodes for any EVM chain (Base, Arbitrum, etc.).
- **Smart Alerts:** Instant notifications via Telegram bots or Webhooks when a "Whale" moves funds.
- **Admin Panel:** A comprehensive dashboard for the Root Admin to manage users, generate API keys, and oversee global system chains.

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/abdelhameed-shaddad-abdelhameed/WhaleTracker-saas.git](https://github.com/abdelhameed-shaddad-abdelhameed/WhaleTracker-saas.git)
   cd WhaleTracker-saas
Create a Virtual Environment (Optional but Recommended):

Bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
Install Dependencies:

Bash
pip install -r requirements.txt
Initialize Database:
The system will automatically create whales.db on the first run.

🏃‍♂️ Usage
1. Run the Dashboard (Frontend)
Bash
streamlit run app.py
2. Run the Scanning Engine (Backend)
Open a new terminal and run:

Bash
python engine.py
🔐 Setup & Login
First Run: When you launch the app for the first time, you will be prompted to create the Root Admin account.

User Management: The Admin can generate API keys and passwords for new users via the Admin Panel.

🛠️ Tech Stack
Frontend: Streamlit

Backend: Python

Database: SQLite (via SQLAlchemy ORM)

Blockchain Interaction: Web3.py

Visualization: Plotly