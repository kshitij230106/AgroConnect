# AgroConnect 🌱

## Intelligent Agricultural Input Discovery and Retailer Recommendation Platform

AgroConnect is an AI-powered agricultural assistance platform designed to help farmers quickly discover fertilizers, agricultural inputs, and nearby retailers through natural language conversations. The platform leverages Conversational AI, Natural Language Understanding (NLU), and a modern web-based interface to simplify agricultural resource accessibility.

---

## 🚀 Overview

Agricultural information and input accessibility remain major challenges for farmers. AgroConnect bridges this gap by providing an intelligent chatbot capable of understanding farmer queries, extracting relevant information, and recommending suitable agricultural products and retailers.

The system combines a Rasa-powered conversational backend with a React frontend to deliver an intuitive and scalable user experience.

---

## ✨ Features

### 🤖 Conversational AI

* Natural language interaction
* Context-aware conversations
* Multi-turn dialogue management
* Intelligent intent recognition
* Entity extraction and understanding

### 🌾 Agricultural Product Discovery

* Fertilizer search
* Product recommendations
* Retailer discovery
* District-specific product lookup

### 🌍 Multilingual Support

* English language support
* Hindi language support
* Extensible architecture for additional languages

### 🧠 Intelligent Entity Recognition

Automatically extracts:

* Fertilizer names
* Product names
* District names
* User locations
* Search intents

Example:

User Query:

```text
I need urea in Tirupati
```

Extracted Information:

```yaml
Intent: search_product
Product: Urea
District: Tirupati
```

---

## 🏗️ System Architecture

```text
+----------------------+
|      React UI        |
+----------+-----------+
           |
           v
+----------------------+
| AgroConnect Frontend |
+----------+-----------+
           |
           v
+----------------------+
|     Rasa Server      |
+----------+-----------+
           |
           v
+----------------------+
| Custom Actions Layer |
+----------+-----------+
           |
           v
+----------------------+
| SQLite Database      |
+----------------------+
```

---

## 🛠 Technology Stack

### Frontend

* React.js
* JavaScript (ES6+)
* CSS3

### Backend

* Python
* Rasa Open Source
* Custom Actions

### Database

* SQLite

### AI Components

* Rasa NLU
* Intent Classification
* Entity Recognition
* Dialogue Management
* Rule-Based Policies

### Development Tools

* Git
* GitHub
* VS Code

---

## 📁 Project Structure

```text
AgroConnect/
│
├── actions/
│   └── actions.py
│
├── backend/
│
├── data/
│   ├── nlu.yml
│   ├── stories.yml
│   └── rules.yml
│
├── frontend/
│   ├── src/
│   │   ├── Chatbot.jsx
│   │   ├── Chatbot.css
│   │   └── App.jsx
│
├── tests/
│
├── config.yml
├── credentials.yml
├── domain.yml
├── endpoints.yml
└── README.md
```

---

## 🧠 Natural Language Processing Pipeline

### Intent Classification

Supported intents include:

* greet
* goodbye
* search_product
* search_retailer
* ask_help

### Entity Extraction

Supported entities include:

* district
* fertilizer
* retailer
* product

### Dialogue Management

* Rule-based conversation flows
* Story-driven interactions
* Context preservation
* Dynamic response generation

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/kshitij230106/AgroConnect.git
cd AgroConnect
```

### Create Virtual Environment

```bash
python -m venv rasa_env
```

### Activate Environment

#### Windows

```bash
rasa_env\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Train Rasa Model

```bash
rasa train
```

### Start Action Server

```bash
rasa run actions
```

### Start Rasa Server

```bash
rasa run --enable-api --cors "*"
```

### Start Frontend

```bash
cd frontend
npm install
npm start
```

---

## 🔄 Query Processing Workflow

```text
User Query
     │
     ▼
Intent Detection
     │
     ▼
Entity Extraction
     │
     ▼
Database Lookup
     │
     ▼
Retailer Recommendation
     │
     ▼
Response Generation
```

Example:

```text
User:
Urea in Tirupati

↓
Intent: Search Product

↓
Entities:
Product = Urea
District = Tirupati

↓
Database Search

↓
Retailer Recommendations

↓
Response Sent To User
```

---

## 🎯 Future Enhancements

* Voice-based chatbot support
* Regional language expansion
* Real-time retailer inventory integration
* Weather-aware recommendations
* AI-powered crop advisory
* Fertilizer recommendation engine
* Mobile application
* GPS-based retailer discovery
* LLM integration for advanced reasoning

---

## 📈 Performance Objectives

* High intent classification accuracy
* Fast response generation
* Scalable database architecture
* Multi-language support
* Low-latency user interactions

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a Pull Request

---

## 👨‍💻 Author

**Kshitij Jha**

GitHub: https://github.com/kshitij230106

---

## 📄 License

This project is licensed under the MIT License.

---

### AgroConnect — Empowering Farmers Through Conversational AI 🌾🚜
