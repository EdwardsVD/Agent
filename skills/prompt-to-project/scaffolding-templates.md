# Standard Scaffolding Templates

## 1. Python Modular CLI / Backend Architecture
```
project/
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py       # Settings & environment loading
│   ├── models.py       # Data structures & classes
│   ├── services.py     # Core business logic
│   └── utils.py        # Shared helper functions
├── tests/
│   ├── __init__.py
│   └── test_core.py    # Comprehensive tests with unittest/pytest
└── main.py             # Entry point with CLI args / server runner
```

## 2. Full-Stack / API Scaffold (FastAPI / Flask / Express)
```
project/
├── .env.example
├── requirements.txt / package.json
├── README.md
├── src/
│   ├── app.py          # Framework initialization & middleware
│   ├── routes/         # Endpoint definitions
│   ├── controllers/    # Request/response logic
│   ├── models/         # Database / ORM schemas
│   └── database.py     # Connection manager (SQLite/Postgres)
├── static/             # Frontend assets (HTML/CSS/JS)
└── tests/
    └── test_api.py     # Endpoint tests
```

## 3. Automation / Termux Script Layout
```
script-tool/
├── tool.sh / tool.py   # Executable script with --help
├── config.json         # Optional configuration
└── test_tool.py        # Functional verification tests
```
