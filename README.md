# Price Comparison App

A modern, containerized web application for scraping and comparing product prices across multiple vendors. Built with **FastAPI**, **PostgreSQL**, and **Docker**.

## 🚀 Features

- **Multi-Vendor Scraping**: Asynchronous scraping engine supporting multiple e-commerce sites (e.g., Traklin, Neto).
- **FastAPI Backend**: robust REST API for managing products, vendors, and initiating scrapes.
- **PostgreSQL Database**: Persistent storage for scrape results and product history.
- **Dockerized**: Fully containerized environment for easy deployment and consistency.
- **Health Checks**: Integrated scripts to verify system health and API availability.

## 🛠️ Tech Stack

- **Language**: Python 3.x
- **Framework**: FastAPI
- **Database**: PostgreSQL 16
- **Scraping**: `aiohttp`, `selectolax`
- **Infrastructure**: Docker & Docker Compose

## 🏁 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd PriceComparisonApp
    ```

2.  **Environment Setup:**
    Copy the example environment file to create your own configuration:
    ```bash
    cp .env.example .env
    ```
    *Note: The default values in `.env.example` work out-of-the-box for local development.*

3.  **Build and Run:**
    Start the services using Docker Compose:
    ```bash
    docker-compose up --build
    ```
    The API will be available at `http://localhost:8000`.

## 📖 Usage

### API Endpoints

Once the app is running, access the interactive API documentation (Swagger UI) at:
**[http://localhost:8000/docs](http://localhost:8000/docs)**

Key endpoints include:
- `GET /scrape?query=<product>`: Trigger a multi-vendor scrape.
- `GET /vendors`: List supported vendors.
- `GET /products`: Retrieve stored product data.
- `GET /autosuggest?query=<term>`: Proxy for vendor autocomplete services.

### Utility Scripts

- **Health Check & Restart**:
    Restart the API container and verify it is responding correctly:
    ```bash
    ./verify_api.sh
    ```

- **Run Locally (without Docker)**:
    If you prefer to run Python scripts directly (ensure you have a virtual environment active):
    ```bash
    pip install -r requirements.txt
    python multi_vendor_scrape.py
    ```

## 📂 Project Structure

```
├── app/                 # FastAPI application source code
│   ├── main.py          # API Entry point and routes
│   └── ...
├── backend/             # Scraping logic and vendor modules
│   ├── vendor_registeration.py
│   └── ...
├── docker-compose.yml   # Container orchestration
├── init.sql             # Database initialization script
├── requirements.txt     # Python dependencies
└── verify_api.sh        # Health check utility
```

## 📝 Roadmap

- Sync Vendors from configuration to database automatically.
- Enhanced error handling (distinguish between network errors and "no results").
- Intelligent query generation (e.g., handling "GR-930" vs "GR930").

## 📄 License

[MIT](LICENSE)
