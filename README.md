# Gestionale Fibra

A full-stack web management system for FTTH installation and telecom field operations. The system manages technicians, teams, work orders (WR), job states, PDF/WR OCR parsing, and includes a Telegram bot for field technicians.

## Features

- **FastAPI Backend**: Modular architecture with routers and services
- **PostgreSQL Database**: Async SQLAlchemy ORM with relationship management
- **Work Order Management**: Full CRUD operations with dynamic JSON fields
- **Team & Technician Management**: Organize field personnel with team assignments
- **PDF/OCR Parsing**: Extract work order data from PDFs using pdfplumber + pytesseract fallback
- **Telegram Bot Integration**: Webhook-ready bot for field technicians
  - New job notifications
  - Accept/refuse job actions
  - Close job workflow
  - Photo upload for documentation
- **Statistics Dashboard**: Real-time stats per day, operator, technician, and team
- **Bootstrap Dashboard**: Responsive web interface with ChartJS visualizations
- **Security**: API key authentication + JWT token support
- **Structured Logging**: JSON format logging with structlog

## Project Structure

```
Fibra/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment configuration loader
│   ├── logging_config.py        # Structured logging setup
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py              # Database session and base model
│   │   ├── technician.py        # Technician model
│   │   ├── team.py              # Team model
│   │   └── work.py              # Work order model with JSON fields
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── technician.py
│   │   ├── team.py
│   │   ├── work.py
│   │   └── stats.py
│   ├── routers/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── technicians.py
│   │   ├── teams.py
│   │   ├── works.py
│   │   ├── stats.py
│   │   └── telegram.py
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── pdf_ocr.py           # PDF/OCR parsing service
│   │   └── stats.py             # Statistics aggregation
│   ├── security/                # Authentication module
│   │   ├── __init__.py
│   │   └── auth.py              # API key + JWT handling
│   ├── telegram/                # Telegram bot module
│   │   ├── __init__.py
│   │   ├── bot.py               # Bot core functionality
│   │   └── handlers.py          # Command handlers
│   ├── static/                  # Static assets
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── dashboard.js
│   └── templates/               # Jinja2 templates
│       └── dashboard.html
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_schemas.py
│   ├── test_security.py
│   └── test_pdf_ocr.py
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore patterns
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Tesseract OCR (optional, for scanned PDF parsing)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Fibra.git
   cd Fibra
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Create database**
   ```bash
   # Create PostgreSQL database
   createdb fibra_db
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

   The application will be available at `http://localhost:8000`

## Configuration

Create a `.env` file based on `.env.example`:

```env
# Application
APP_NAME=Gestionale Fibra
APP_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fibra_db

# Security
API_KEY=your-api-key
JWT_SECRET_KEY=your-jwt-secret

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/telegram/webhook

# OCR
TESSERACT_CMD=/usr/bin/tesseract
```

## API Endpoints

### Technicians
- `GET /api/technicians` - List all technicians
- `GET /api/technicians/{id}` - Get technician by ID
- `POST /api/technicians` - Create new technician
- `PUT /api/technicians/{id}` - Update technician
- `DELETE /api/technicians/{id}` - Delete technician
- `GET /api/technicians/by-telegram/{telegram_id}` - Get technician by Telegram ID

### Teams
- `GET /api/teams` - List all teams
- `GET /api/teams/{id}` - Get team by ID
- `POST /api/teams` - Create new team
- `PUT /api/teams/{id}` - Update team
- `DELETE /api/teams/{id}` - Delete team

### Work Orders
- `GET /api/works` - List work orders with filters
- `GET /api/works/{id}` - Get work order by ID
- `POST /api/works` - Create new work order
- `PUT /api/works/{id}` - Update work order
- `DELETE /api/works/{id}` - Delete work order
- `POST /api/works/{id}/assign/{technician_id}` - Assign work to technician
- `POST /api/works/parse-pdf` - Parse work order from PDF

### Statistics
- `GET /api/stats` - Get complete statistics
- `GET /api/stats/daily` - Daily statistics
- `GET /api/stats/operators` - Statistics by operator
- `GET /api/stats/technicians` - Statistics by technician
- `GET /api/stats/teams` - Statistics by team

### Telegram
- `POST /telegram/webhook` - Telegram webhook endpoint
- `GET /telegram/set-webhook` - Set Telegram webhook URL

## Telegram Bot Commands

- `/start` - Register and get Telegram ID
- `/lavori` - View assigned jobs
- `/aiuto` - Help guide

### Interactive Actions
- **Accept Job** - Accept an assigned work order
- **Refuse Job** - Refuse a work order with reason
- **Send Photo** - Upload photos for documentation
- **Close Job** - Mark work as completed

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Formatting
```bash
black app/ tests/
```

### Linting
```bash
ruff check app/ tests/
```

## Database Models

### Technician
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | Technician name |
| phone | String(20) | Contact phone |
| email | String(100) | Email address |
| telegram_id | String(50) | Telegram user ID |
| team_id | Integer | Team reference |
| is_active | Boolean | Active status |

### Team
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | Team name |
| description | String(500) | Description |
| leader_id | Integer | Team leader ID |
| is_active | Boolean | Active status |

### Work
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| wr_number | String(50) | Work request number |
| operator | String(50) | Telecom operator |
| customer_name | String(200) | Customer name |
| customer_address | Text | Installation address |
| customer_phone | String(20) | Customer phone |
| scheduled_date | Date | Scheduled date |
| status | Enum | Work status |
| technician_id | Integer | Assigned technician |
| notes | Text | Additional notes |
| extra_data | JSONB | Dynamic fields |
| photos | JSONB | Photo references |
| completion_date | DateTime | Completion timestamp |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
