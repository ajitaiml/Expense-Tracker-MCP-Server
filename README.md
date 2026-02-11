# 💰 Expense Tracker MCP Server

A custom Model Context Protocol (MCP) server that transforms Claude Desktop into a conversational personal finance assistant.

This project demonstrates integration between:
- LLM tool-calling architecture
- Structured database systems (MySQL)
- Custom backend logic using FastMCP (Python 3.11)

---

## 🚀 Features

- Conversational expense logging via Claude Desktop
- Add, edit, delete expenses
- Income tracking (salary / credits)
- Category-wise expense summaries
- Net balance calculation (Income – Expenses)
- Persistent MySQL backend storage

---

## 🛠 Tech Stack

- **Python 3.11.x**
- **FastMCP**
- **MySQL**
- **uv (Astral) for environment management**
- **Claude Desktop (MCP integration)**

---

## 📋 Prerequisites

1. Python 3.11 installed
2. MySQL Server running
3. Claude Desktop installed
4. uv installed (`pip install uv` or official installer)

---

## 🔧 Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/ajitaiml/Expense-Tracker-MCP-Server.git
cd Expense-Tracker-MCP-Server
