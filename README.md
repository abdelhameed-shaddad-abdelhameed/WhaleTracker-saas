# 🐋 WhaleHunter SaaS Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Web3](https://img.shields.io/badge/Web3.py-Blockchain-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**WhaleHunter** is an enterprise-grade SaaS solution designed for real-time cryptocurrency wallet tracking. It empowers users to monitor "Whale" movements across multiple EVM blockchains (Ethereum, BSC, Polygon, Base, etc.) with instant alerts and deep analytics.

---

## 📸 System Overview

### 📊 The Command Center (Dashboard)
A powerful dashboard providing a bird's-eye view of tracked assets, recent alerts, and system health status. Visualizes data using interactive charts to understand flow intent (Buying vs. Selling).

![Dashboard](assets/Screenshot%202026-01-29%20081620.jpg)

### 📡 Real-Time Market Feed
Watch transactions happen live. The engine scans blocks in the background and populates this feed with high-value movements, analyzing the intent behind every transaction using AI logic.

![Live Feed](assets/Screenshot%202026-01-29%20081743.jpg)

### 🎯 Smart Target Management
Easily add, edit, or remove wallets to track. Set specific thresholds for Native Coins (ETH/BNB) and ERC-20 tokens to filter out noise and focus on significant market moves.

![Target Management](assets/Screenshot%202026-01-29%20081718.jpg)

---

## 🚀 Key Features

* **🛡️ Multi-Tier Access System:**
    * **Free:** Basic tracking limits.
    * **Pro:** Unlocks Telegram Alerts & API Access.
    * **Enterprise:** Unlimited tracking, Webhooks, and Admin controls.
* **🔗 Custom RPC Architecture:**
    * Connect to *any* EVM chain by simply adding your private RPC URL.
    * Support for Layer 2s (Arbitrum, Optimism, Base) out of the box.
* **🤖 Intent Analysis Engine:**
    * Automatically classifies transactions: *Accumulation, Dumping, Stablecoin Rotation, etc.*
* **🔔 Multi-Channel Alerts:**
    * Get notified instantly via **Telegram Bot**.
    * **Webhook** integration for programmatic trading.

---

## ⚙️ Advanced Configuration

### 🔌 Custom Networks & RPCs
Pro and Enterprise users can extend the platform's capabilities by adding custom blockchain networks directly from the UI.

![Custom Networks](assets/Screenshot%202026-01-29%20081822.jpg)

### 🔑 API & Integrations
Developers can generate secure API keys to integrate WhaleHunter data into their own trading bots or dashboards.

![Settings](assets/Screenshot%202026-01-29%20081805.jpg)

### 🛠️ Root Admin Panel
Complete control over the SaaS ecosystem. Manage users, reset passwords, oversee global node connections, and monitor system-wide logs.

![Admin Panel](assets/Screenshot%202026-01-29%20081905.jpg)

---

## 📦 Installation & Setup

1.  **Clone the Repo**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/WhaleTracker-saas-V2.git](https://github.com/YOUR_USERNAME/WhaleTracker-saas-V2.git)
    cd WhaleTracker-saas-V2
    ```

2.  **Install Requirements**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    * **Frontend:** `streamlit run app.py`
    * **Backend Engine:** `python engine.py`

4.  **First Login:**
    The system will prompt you to create the **Root Admin** account upon the first launch.

---

## 🔮 Future Roadmap

- [ ] AI-Powered Price Prediction based on Whale moves.
- [ ] Mobile App (iOS/Android).
- [ ] Support for Solana & Bitcoin networks.
- [ ] Copy-Trading Integration.

---

<p align="center">
  Made with ❤️ by Abdelhameed Shaddad using <b>Streamlit</b> & <b>Web3.py</b>
</p>