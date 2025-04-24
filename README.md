# Restaurant Monitoring System

A FastAPI-based backend system for monitoring restaurant statuses in the US. The system tracks whether restaurants are online during their business hours and generates reports on their uptime and downtime.

## Features

- Upload store status, business hours, and timezone data via CSV files
- Generate reports showing uptime and downtime for each store
- Support for different timezones and business hours
- Background report generation
- CSV report download

## Project Structure

```
.
├── controllers/
│   ├── csv_controller.py      # Handles CSV uploads
│   ├── report_controller.py   # Handles report generation
│   └── __init__.py
├── models/
│   ├── store.py              # Store model
│   ├── business_hours.py     # Business hours model
│   ├── store_status.py       # Store status model
│   ├── report.py            # Report model
│   └── __init__.py
├── database.py              # Database configuration
├── main.py                 # FastAPI application
└── README.md              # Project documentation
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Start the server:
```bash
uvicorn main:app --reload --port 5000
```

The server will start at http://localhost:5000

## Database Configuration

The system uses SQLite as its database, which is configured in `database.py`. The database file (`restaurant_monitoring.db`) will be automatically created in your project directory when you first run the application.

### Database Location
- The SQLite database file is stored at: `./restaurant_monitoring.db`
- All data from CSV uploads is stored in this SQLite database
- The database is automatically created and managed by SQLAlchemy

### Database Schema
The database contains the following tables:
- `store`: Stores store information and timezones
- `business_hours`: Stores business hours for each store
- `store_status`: Stores status updates for each store
- `report`: Stores generated reports

### Viewing the Database
You can view the database using:
1. SQLite Browser (GUI tool)
2. SQLite command line:
```bash
sqlite3 restaurant_monitoring.db
```
3. Python script:
```python
import sqlite3
conn = sqlite3.connect('restaurant_monitoring.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())
```

## API Endpoints

### 1. Upload Store Status
- **URL**: `/api/upload/store-status`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Required CSV columns**: `store_id`, `timestamp_utc`, `status`
- **Example**:
```bash
curl -X POST -F "file=@store_status.csv" http://localhost:5000/api/upload/store-status
```

### 2. Upload Business Hours
- **URL**: `/api/upload/business-hours`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Required CSV columns**: `store_id`, `day`, `start_time_local`, `end_time_local`
- **Example**:
```bash
curl -X POST -F "file=@business_hours.csv" http://localhost:5000/api/upload/business-hours
```

### 3. Upload Timezones
- **URL**: `/api/upload/timezones`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Required CSV columns**: `store_id`, `timezone_str`
- **Example**:
```bash
curl -X POST -F "file=@timezones.csv" http://localhost:5000/api/upload/timezones
```

### 4. Trigger Report Generation
- **URL**: `/api/trigger_report`
- **Method**: `POST`
- **Response**: Returns a report ID
- **Example**:
```bash
curl -X POST http://localhost:5000/api/trigger_report
```

### 5. Get Report Status
- **URL**: `/api/get_report/{report_id}`
- **Method**: `GET`
- **Response**: Returns report status or CSV file
- **Example**:
```bash
curl http://localhost:5000/api/get_report/{report_id}
```

## Report Format

The generated report is a CSV file containing:
- store_id
- uptime_last_hour (in minutes)
- uptime_last_day (in hours)
- uptime_last_week (in hours)
- downtime_last_hour (in minutes)
- downtime_last_day (in hours)
- downtime_last_week (in hours)

## Usage Examples

### Uploading Data
1. Prepare your CSV files with the required columns
2. Upload each file using the respective endpoint
3. Verify the upload was successful

### Generating Reports
1. Trigger a report generation:
```bash
curl -X POST http://localhost:5000/api/trigger_report
```
2. Note the returned report_id
3. Check report status:
```bash
curl http://localhost:5000/api/get_report/{report_id}
```
4. Download the report when complete

## Notes

- Business hours are considered in the store's local timezone
- Uptime/downtime calculations are based on business hours
- Reports are generated in the background
- The system uses SQLite for data storage
- All timestamps are stored in UTC

## Example Report Generated

[Download Latest Report](https://github.com/Abhiram0304/Abhiram_24-04-2025/blob/main/uploads/report_56fe3631-19ba-4d50-ba0e-72275049fd9a.csv)
