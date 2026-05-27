# Asset Management System

A comprehensive web-based application for managing organizational assets, employee records, asset assignments, and audit logging. Built with Flask and SQLAlchemy, this system provides an intuitive interface for tracking hardware and equipment across employees, with support for assignment history, return tracking, and exportable reports.

## Features

- **Asset Management** -- Full CRUD operations for assets with fields for name, serial number, category, vendor, and purchase date
- **Employee Management** -- Add, edit, and delete employee records with optional photo uploads
- **Asset Assignment** -- Assign assets to employees with notes, track return dates and return notes
- **Return Notes** -- Add notes when returning assets, stored separately from assignment notes
- **Smart Validation** -- Blocks future purchase dates and future return dates with clear error messages
- **Assignment History** -- Complete timeline of every asset assignment and return
- **Status Tracking** -- Automatic status indicators (Available / Assigned) for each asset
- **Search and Filtering** -- Search assets by name, serial number, or category; filter by category or status
- **Employee Search** -- Search employees by name, employee ID, or position; filter by company
- **Dashboard** -- Overview counts for total assets, assigned assets, available assets, employees, and active assignees
- **CSV Export** -- Export complete asset, employee, and assignment data to CSV
- **HTML Report** -- Generate a styled HTML report with summary cards and full data tables
- **Asset Print Report** -- Download a detailed HTML report for an individual asset with assignment history
- **Employee Print Report** -- Download a detailed HTML report for an individual employee with their asset history
- **Audit Logging** -- Automatic logging of all CREATE, UPDATE, DELETE, ASSIGN, RETURN, LOGIN, LOGOUT, and EXPORT actions
- **Authentication** -- Admin login with Flask-Login; default admin user created automatically on first run
- **Auto-Logout** -- Session expires automatically on browser close; always starts logged out
- **Toast Notifications** -- Action-based toast notifications showing actual success/error messages
- **Inter UI** -- Clean Google-quality interface with Inter font, breadcrumb navigation, and consistent white-card design
- **Responsive UI** -- Clean, modern interface with Inter font, breadcrumb navigation, and consistent Material-inspired card design

## Tech Stack

| Component       | Technology                                      |
|-----------------|-------------------------------------------------|
| Backend         | Python 3 / Flask 3.0                            |
| ORM             | SQLAlchemy (Flask-SQLAlchemy 3.1)               |
| Database        | SQLite                                           |
| Authentication  | Flask-Login 0.6 with Werkzeug password hashing  |
| Frontend        | Bootstrap 5.3, Bootstrap Icons, custom CSS/JS   |
| Templates       | Jinja2                                           |
| CSV Export      | Python csv module                                |
| HTML Reports    | Inline styled HTML generated server-side        |
| Font            | Inter (Google Fonts)                             |
| Notifications   | Bootstrap Toasts with custom JS                  |

## Project Structure

```
asset_management/
├── app/
│   ├── __init__.py              # Flask app factory, blueprint registration, DB init
│   ├── config.py                # App configuration (SECRET_KEY, DB URI, upload path)
│   ├── extensions.py            # Flask extensions (db, login_manager, bootstrap)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── asset.py             # Asset model (name, serial_no, category, etc.)
│   │   ├── employee.py          # Employee model (employee_id, name, position, etc.)
│   │   ├── assignment.py        # Assignment model (asset-employee link with dates)
│   │   ├── user.py              # User model (admin authentication)
│   │   └── audit_log.py         # AuditLog model (action trail for all changes)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Login/logout routes + default admin creation
│   │   ├── dashboard.py         # Dashboard overview route
│   │   ├── assets.py            # Asset CRUD, assign, return, print report
│   │   ├── employees.py         # Employee CRUD, print report
│   │   └── export.py            # CSV and HTML full-report export
│   ├── templates/
│   │   ├── base.html            # Base layout (Bootstrap 5, navbar, toast system)
│   │   ├── login.html           # Admin login page
│   │   ├── dashboard.html       # Summary dashboard
│   │   ├── assets_list.html     # Asset listing with search and filters
│   │   ├── asset_detail.html    # Single asset view + assignment history
│   │   ├── asset_form.html      # Add/edit asset form
│   │   ├── assign_asset.html    # Assign asset to employee form
│   │   ├── return_asset.html    # Return asset form
│   │   ├── employees_list.html  # Employee listing with search and filters
│   │   ├── employee_detail.html # Single employee view + asset history
│   │   └── employee_form.html   # Add/edit employee form
│   ├── static/
│   │   ├── css/custom.css       # Custom styles
│   │   ├── js/custom.js         # Client-side JavaScript
│   │   └── uploads/             # Employee photo uploads
│   └── utils/
│       └── __init__.py
├── instance/
│   ├── .gitkeep
│   └── assets.db                # SQLite database (auto-created on first run)
├── requirements.txt             # Python dependencies
├── run.py                       # Entry point -- start the app here
├── README.md                    # This file
└── spec.md                      # Project specification
```

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Quick Start

1. **Download the project and navigate to the directory:**

   ```bash
   cd asset_management
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**

   ```bash
   python3 run.py
   ```

4. **Open your browser:**

   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

The SQLite database (`instance/assets.db`) and the `uploads` directory are created automatically on first run. A default admin user is also created if one does not exist.

## Default Credentials

| Role  | Username | Password |
|-------|----------|----------|
| Admin | `admin`  | `123456` |

**Important:** Change the default password in a production environment.

## UI Design

The interface follows Google Material design principles:

- **Inter font** -- Clean, highly readable sans-serif typeface loaded from Google Fonts
- **White-card layout** -- All content in clean white cards with subtle elevation (shadows) instead of colored backgrounds
- **Breadcrumb navigation** -- Every page has breadcrumbs showing the current location
- **Consistent color palette** -- Blue (#1a73e8) as primary, with restrained use of accent colors
- **Toast notifications** -- Success/error/warning/info messages appear as slide-in toasts in the top-right corner
- **Responsive** -- Fully responsive design using Bootstrap 5.3 grid system

## How to Use

### Login

1. Click **Admin Login** in the top-right corner of the navigation bar.
2. Enter username `admin` and password `123456`.
3. You will be redirected to the Dashboard.

### Managing Assets

- **View all assets:** Navigate to the Assets section via the navigation bar. Use the search bar to find assets by name, serial number, or category. Filter by category or status (Available / Assigned).
- **Add an asset:** Click **Add Asset**, fill in the name, serial number, category, vendor, and purchase date, then click **Save Asset**.
- **View asset details:** Click on any asset card to see full details, current status, and complete assignment history.
- **Edit an asset:** On the asset detail page, click **Edit** to modify asset fields.
- **Delete an asset:** On the asset detail page, click **Delete** (only available when the asset is not currently assigned).

### Managing Employees

- **View all employees:** Navigate to the Employees section. Use the search bar to find employees by name, ID, or position. Filter by company.
- **Add an employee:** Click **Add Employee**, fill in employee ID, name, position, company, and optionally upload a photo, then click **Save Employee**.
- **View employee details:** Click on any employee card to see their information and asset assignment history.
- **Edit an employee:** On the employee detail page, click **Edit** to modify employee fields or upload a new photo.
- **Delete an employee:** On the employee detail page, click **Delete** (only available when the employee has no active asset assignments).

### Assigning and Returning Assets

- **Assign an asset:** Navigate to an asset detail page and click **Assign to Employee**. Select an employee, optionally add assign notes, and confirm. The asset status changes to "Assigned."
- **Return an asset:** On the asset detail page for an assigned asset, click **Mark as Returned**. Optionally add return notes and confirm. The asset status returns to "Available."

### Reports and Export

- **CSV Export:** From the Dashboard or any main page, use the **Export CSV** button to download a complete CSV report containing all assets, employees, and assignment history.
- **HTML Report:** Use the **Export HTML Report** button to download a styled HTML document with summary statistics, asset table, employee table, and assignment history.
- **Asset Reports:** On any asset detail page, click **Download Report** to get a detailed asset report with assignment history.
- **Employee Reports:** On any employee detail page, click **Download Report** to get a detailed employee report with asset history.

## Data Storage

- **Database:** The application uses SQLite, stored at `instance/assets.db`. This file is created automatically the first time the application runs. All data (assets, employees, assignments, users, audit logs) persists in this single file between sessions.
- **Uploaded photos:** Employee photo uploads are stored in `app/static/uploads/`. These are served statically via the `/static/uploads/` URL path.
- **Logs and reports:** The `logs/` and `reports/` directories are reserved for future use and currently contain only `.gitkeep` placeholders.
- **Session data:** Sessions are non-permanent and expire when the browser is closed. The server always starts with a logged-out state.

To reset the application completely, stop the server, delete `instance/assets.db`, and restart -- the database will be recreated and a fresh admin user will be generated.

## How to Transfer to Another Machine

1. Copy the entire `asset_management` folder to the target machine.
2. Ensure Python 3.8+ and pip are installed.
3. Open a terminal in the `asset_management` directory.
4. Install dependencies (Flask and SQLAlchemy):
   ```bash
   pip install -r requirements.txt
   ```
5. Run the application:
   ```bash
   python3 run.py
   ```
6. Open a browser and go to `http://127.0.0.1:5000`.

The database file (`instance/assets.db`) can be copied along with the project to preserve all existing data, or omitted to start with a fresh database that will be created automatically on first run.

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
