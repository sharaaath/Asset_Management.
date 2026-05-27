# Asset Management System -- Technical Specification

## 1. System Overview

### 1.1 Purpose
The Asset Management System is a web-based application for tracking organizational assets (hardware, equipment) assigned to employees. It provides complete lifecycle management from asset procurement through assignment, tracking, return, and disposal, with a full audit trail of all actions.

### 1.2 Scope
- Asset CRUD (Create, Read, Update, Delete)
- Employee CRUD with photo upload
- Asset-to-Employee assignment lifecycle (assign and return)
- Assignment history tracking per asset and per employee
- Search and filtering across assets and employees
- Dashboard with summary statistics
- Data export (CSV and HTML reports)
- Individual asset and employee print reports (HTML download)
- Audit logging of all system actions
- Admin authentication via Flask-Login

### 1.3 Default Credentials
| Role  | Username | Password |
|-------|----------|----------|
| Admin | `admin`  | `123456` |

---

## 2. Architecture

### 2.1 Framework
- **Language:** Python 3.8+
- **Web Framework:** Flask 3.0
- **Application Pattern:** Flask App Factory (`create_app()` in `app/__init__.py`)
- **Routing Pattern:** Blueprint-based modular routing
- **ORM:** SQLAlchemy 3.1 via Flask-SQLAlchemy
- **Database:** SQLite (development); swappable via `DATABASE_URL` environment variable
- **Template Engine:** Jinja2 server-side rendering
- **Frontend:** Bootstrap 5.3 + Bootstrap Icons + Inter font (Google Fonts) + custom CSS/JS

- **Authentication:** Flask-Login session-based
- **Session Storage:** Sessions non-permanent (expire on browser close)

### 2.2 Blueprint Structure
| Blueprint     | URL Prefix     | Module                |
|---------------|----------------|-----------------------|
| `auth`        | `/auth`        | `app/routes/auth.py`  |
| `dashboard`   | `/`            | `app/routes/dashboard.py` |
| `assets`      | `/assets`      | `app/routes/assets.py` |
| `employees`   | `/employees`   | `app/routes/employees.py` |
| `export`      | `/export`      | `app/routes/export.py` |

### 2.3 Project Structure
```
asset_management/
  app/
    __init__.py          # App factory, blueprint registration, DB init, admin seeding
    config.py            # Configuration (SECRET_KEY, DB URI, upload path)
    models/
      __init__.py        # Imports all models
      asset.py           # Asset model
      employee.py        # Employee model
      assignment.py      # Assignment model
      user.py            # User model
      audit_log.py       # AuditLog model
    routes/
      __init__.py        # Imports all blueprints
      auth.py            # Login/logout + user_loader + admin creation
      dashboard.py       # Homepage / dashboard
      assets.py          # Asset CRUD + assign/return + print report
      employees.py       # Employee CRUD + print report
      export.py          # CSV and HTML export
    templates/
      base.html          # Base layout (navbar, toast container, footer)
      login.html         # Login form
      dashboard.html     # Summary stats cards
      assets_list.html   # Asset table with search/filter
      asset_detail.html  # Single asset view + history
      asset_form.html    # Add/Edit asset form
      assign_asset.html  # Assign asset to employee
      return_asset.html  # Return asset form
      employees_list.html # Employee table with search/filter
      employee_detail.html # Single employee view + history
      employee_form.html # Add/Edit employee form
    static/
      css/custom.css     # Custom styles
      js/custom.js       # Toast system + form spinner + confirm helper
      uploads/           # Employee photo uploads directory
    utils/
      __init__.py
  instance/
    assets.db            # SQLite database (auto-created)
  spec.md                # Technical specification document
  run.py                 # Entry point
  requirements.txt       # Python dependencies
  README.md              # Project README
```

### 2.4 Application Initialization (`app/__init__.py`)
```
create_app(config_class=Config):
  1. Create Flask app
  2. Load config from Config class
  3. Initialize db, login_manager, bootstrap
  4. login_manager.login_view = 'auth.login'
  5. Register blueprints (auth, dashboard, assets, employees, export)
  6. With app context: create all DB tables, create default admin user
  7. Return app
```

### 2.5 Entry Point (`run.py`)
```
1. Import create_app
2. Call create_app() to get Flask app instance
3. Print startup banner with default credentials
4. app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 3. Complete Database Schema

### 3.1 Entity Relationship Summary
```
User 1---* AuditLog
Asset 1---* Assignment *---1 Employee
```

### 3.2 User Model (`app/models/user.py`)
**Table:** `users`

| Column         | Type          | Constraints                  |
|----------------|---------------|------------------------------|
| `id`           | Integer       | PRIMARY KEY, auto-increment  |
| `username`     | String(50)    | UNIQUE, NOT NULL             |
| `password_hash`| String(255)   | NOT NULL                     |
| `created_at`   | DateTime      | DEFAULT datetime.utcnow      |

**Mixins/Inheritance:**
- `UserMixin` (from Flask-Login) -- provides `is_authenticated`, `is_active`, `is_anonymous`, `get_id()`

**Relationships:** None defined as backrefs (referenced by AuditLog via `user_id`)

**Methods:**
- `set_password(password)` -- hashes password via `werkzeug.security.generate_password_hash`
- `check_password(password)` -- verifies hash via `werkzeug.security.check_password_hash`

### 3.3 Asset Model (`app/models/asset.py`)
**Table:** `assets`

| Column           | Type          | Constraints                  |
|------------------|---------------|------------------------------|
| `id`             | Integer       | PRIMARY KEY, auto-increment  |
| `name`           | String(100)   | NOT NULL                     |
| `serial_number`  | String(50)    | UNIQUE, NOT NULL             |
| `category`       | String(50)    | NOT NULL                     |
| `purchased_from` | String(100)   | nullable                     |
| `purchased_date` | Date          | nullable                     |
| `created_at`     | DateTime      | DEFAULT datetime.utcnow      |

**Relationships:**
- `assignments` -- one-to-many to `Assignment` via `backref='asset'`, lazy=True

**Properties:**
- `status` -- returns `'ASSIGNED'` if an active Assignment (returned_date IS NULL) exists; else `'AVAILABLE'`
- `assigned_to` -- return the Employee object of the active assignment; else `None`

### 3.4 Employee Model (`app/models/employee.py`)
**Table:** `employees`

| Column        | Type          | Constraints                  |
|---------------|---------------|------------------------------|
| `id`          | Integer       | PRIMARY KEY, auto-increment  |
| `employee_id` | String(20)    | UNIQUE, NOT NULL             |
| `name`        | String(100)   | NOT NULL                     |
| `position`    | String(100)   | nullable                     |
| `company`     | String(100)   | nullable                     |
| `photo_url`   | String(255)   | nullable                     |
| `created_at`  | DateTime      | DEFAULT datetime.utcnow      |

**Relationships:**
- `assignments` -- one-to-many to `Assignment` via `backref='employee'`, lazy=True

**Properties:**
- `currently_assigned_assets` -- filters `self.assignments` where `returned_date IS NULL` and `asset IS NOT NULL`; returns list of Asset objects
- `returned_assets` -- filters `self.assignments` where `returned_date IS NOT NULL` and `asset IS NOT NULL`; returns list of Asset objects
- `initials` -- first character of first + last name parts; returns single char if only one word; returns `'?'` for empty name

### 3.5 Assignment Model (`app/models/assignment.py`)
**Table:** `assignments`

| Column          | Type          | Constraints                          |
|-----------------|---------------|--------------------------------------|
| `id`            | Integer       | PRIMARY KEY, auto-increment          |
| `asset_id`      | Integer       | FOREIGN KEY -> `assets.id`, NOT NULL |
| `employee_id`   | Integer       | FOREIGN KEY -> `employees.id`, NOT NULL |
| `assigned_date` | DateTime      | NOT NULL, DEFAULT datetime.utcnow    |
| `returned_date` | DateTime      | nullable (NULL = currently assigned) |
| `notes`         | Text          | nullable                             |
| `return_notes`  | Text          | nullable                             |
| `created_at`    | DateTime      | DEFAULT datetime.utcnow              |

**Relationships (via backrefs):**
- `asset` -- belongs-to Asset (from `Asset.assignments`)
- `employee` -- belongs-to Employee (from `Employee.assignments`)

**Key Logic:**
- Active assignment: `returned_date IS NULL`
- Returned assignment: `returned_date IS NOT NULL`
- An asset can have at most ONE active assignment at any time (enforced by application logic, not DB constraint)

### 3.6 AuditLog Model (`app/models/audit_log.py`)
**Table:** `audit_logs`

| Column        | Type          | Constraints                  |
|---------------|---------------|------------------------------|
| `id`          | Integer       | PRIMARY KEY, auto-increment  |
| `action`      | String(50)    | NOT NULL                     |
| `table_name`  | String(50)    | NOT NULL                     |
| `record_id`   | Integer       | nullable                     |
| `old_value`   | Text          | nullable (JSON string)       |
| `new_value`   | Text          | nullable (JSON string)       |
| `timestamp`   | DateTime      | DEFAULT datetime.utcnow      |
| `user_id`     | Integer       | nullable                     |

**Static Method:**
- `log(action, table_name, record_id=None, old_value=None, new_value=None, user_id=None)` -- creates and commits an AuditLog entry. `old_value` and `new_value` are JSON-serialized via `json.dumps`.

**Logged Action Types:**
| Action   | table_name      | Trigger                          |
|----------|-----------------|----------------------------------|
| CREATE   | users           | Default admin creation           |
| CREATE   | assets          | New asset added                  |
| CREATE   | employees       | New employee added               |
| UPDATE   | assets          | Asset modified                   |
| UPDATE   | employees       | Employee modified                |
| DELETE   | assets          | Asset deleted (cascades assignments) |
| DELETE   | employees       | Employee deleted (only if no active assignments) |
| ASSIGN   | assignments     | Asset assigned to employee       |
| RETURN   | assignments     | Asset returned from employee     |
| LOGIN    | users           | Successful login                 |
| LOGOUT   | users           | Logout action                    |
| EXPORT   | assets          | Asset print report downloaded    |
| EXPORT   | employees       | Employee print report downloaded |
| EXPORT   | reports         | CSV or HTML export               |

---

## 4. Complete Route/Endpoint Reference

### 4.1 Auth Blueprint (`/auth`)

#### `GET /auth/login` -- `auth.login`
- **Purpose:** Display login form
- **Authentication:** None (public)
- **Template:** `login.html`
- **Behavior:** If user is already authenticated, redirect to dashboard

#### `POST /auth/login` -- `auth.login`
- **Purpose:** Authenticate user
- **Authentication:** None (public)
- **Form Fields:**
  - `username` (text, required)
  - `password` (password, required)
- **Validation:** Query User by username; check password hash
- **Success:** Create Flask-Login session (`session.permanent = False`), log audit entry (`LOGIN`), flash `'Welcome back!'` (success), redirect to `request.args.get('next')` or dashboard
- **Failure:** Flash `'Invalid username or password'` (danger), re-render `login.html`
- **Session Behavior:** `session.permanent = False` -- session expires on browser close

#### `GET /auth/logout` -- `auth.logout`
- **Purpose:** Log out current user
- **Authentication:** `@login_required`
- **Behavior:** Log audit entry (`LOGOUT`), call `logout_user()`, flash `'You have been logged out.'` (info), redirect to dashboard

### 4.2 Dashboard Blueprint (`/`)

#### `GET /` -- `dashboard.index`
- **Purpose:** Display dashboard with summary statistics
- **Authentication:** None (public)
- **Template:** `dashboard.html`
- **Data Passed:**
  - `total_assets` -- count of all assets
  - `assigned_assets` -- count of assignments where `returned_date IS NULL`
  - `available_assets` -- `total_assets - assigned_assets`
  - `total_employees` -- count of all employees
  - `employees_with_assets` -- distinct employees with at least one active assignment
- **UI Elements:**
  - Three stat cards (Total Assets, Assigned, Available)
  - Two clickable cards (Assets, Employees) linking to their list views
  - Export buttons (CSV, HTML) -- visible only when authenticated

### 4.3 Assets Blueprint (`/assets`)

#### `GET /assets/list` -- `assets.list`
- **Purpose:** List all assets with search and filter
- **Authentication:** None (public)
- **Template:** `assets_list.html`
- **Query Parameters:**
  - `search` (string) -- filters by name, serial_number, category (ILIKE)
  - `category` (string) -- exact match on category
  - `status` (string) -- `'available'` or `'assigned'`; subquery filter on Assignment.returned_date
- **Data Passed:** `assets`, `search_query`, `category_filter`, `status_filter`, `categories` (distinct list)
- **Behavior:** Ordered by `created_at DESC`. Add Asset button visible only when authenticated.

#### `GET /assets/` -- `assets.index`
- **Purpose:** Redirect to `/assets/list`

#### `GET /assets/detail/<int:asset_id>` -- `assets.detail`
- **Purpose:** Show single asset detail with assignment history
- **Authentication:** None (public)
- **Template:** `asset_detail.html`
- **Data Passed:** `asset`, `assignments` (ordered by `assigned_date DESC`), `employees`
- **Behavior:** 404 if asset not found. Action buttons (Assign/Return, Edit, Delete, Download Report) visible only when authenticated. Download Report generates a standalone HTML document.

#### `GET /assets/add` -- `assets.add`
- **Purpose:** Display add asset form
- **Authentication:** `@login_required`
- **Template:** `asset_form.html` (no `asset` context variable -- form is in create mode)
- **Form Fields:** name, serial_number, category, purchased_from, purchased_date

#### `POST /assets/add` -- `assets.add`
- **Purpose:** Create new asset
- **Authentication:** `@login_required`
- **Form Fields:**
  - `name` (text, required)
  - `serial_number` (text, required, must be unique)
  - `category` (select, required)
  - `purchased_from` (text, optional)
  - `purchased_date` (date, optional, format `YYYY-MM-DD`)
- **Validation:**
  - `purchased_date` must not be in the future (compared to `datetime.now().date()`)
  - `serial_number` must be unique; if duplicate, flash error and redirect to list
- **Success:** Insert Asset, commit, log audit (`CREATE`, `assets`), flash success, redirect to `assets.list`
- **Failure (future date):** Flash danger, redirect to `assets.add`

#### `GET /assets/edit/<int:asset_id>` -- `assets.edit`
- **Purpose:** Display edit asset form (pre-filled)
- **Authentication:** `@login_required`
- **Template:** `asset_form.html` (with `asset` context variable -- form is in edit mode)
- **Behavior:** 404 if asset not found

#### `POST /assets/edit/<int:asset_id>` -- `assets.edit`
- **Purpose:** Update existing asset
- **Authentication:** `@login_required`
- **Form Fields:** Same as add
- **Validation:** Future date check on `purchased_date`
- **Behavior:** Capture old values before update, commit changes, log audit (`UPDATE`, `assets`, old_value + new_value), flash success, redirect to `assets.detail`
- **Failure (future date):** Flash danger, redirect to `assets.edit`

#### `POST /assets/delete/<int:asset_id>` -- `assets.delete`
- **Purpose:** Delete asset and its assignment history
- **Authentication:** `@login_required`
- **Behavior:**
  1. Fetch asset (404 if not found)
  2. Log audit (`DELETE`, `assets`, old_value)
  3. Delete all related Assignment records (`Assignment.query.filter_by(asset_id=asset_id).delete()`)
  4. Delete asset
  5. Commit
  6. Flash success, redirect to `assets.list`

#### `GET /assets/assign/<int:asset_id>` -- `assets.assign`
- **Purpose:** Display assign form
- **Authentication:** `@login_required`
- **Template:** `assign_asset.html`
- **Behavior:**
  - Fetch asset (404 if not found)
  - Check if asset already has active assignment; if so, flash warning and redirect to detail
  - Pass `asset`, `employees`, `today` (current date string for display)

#### `POST /assets/assign/<int:asset_id>` -- `assets.assign`
- **Purpose:** Create assignment record
- **Authentication:** `@login_required`
- **Form Fields:**
  - `employee_id` (select, required)
  - `notes` (textarea, optional)
- **Behavior:**
  1. Check active assignment guard (same as GET)
  2. Create Assignment with `assigned_date = datetime.now()`
  3. Commit
  4. Log audit (`ASSIGN`, `assignments`, new_value includes asset name, employee name, date)
  5. Flash success, redirect to `assets.detail`

#### `GET /assets/return/<int:asset_id>` -- `assets.return_asset`
- **Purpose:** Display return form
- **Authentication:** `@login_required`
- **Template:** `return_asset.html`
- **Behavior:**
  - Fetch asset (404 if not found)
  - Check if asset has an active assignment; if not, flash warning and redirect to detail
  - Pass `asset` and `assignment`

#### `POST /assets/return/<int:asset_id>` -- `assets.return_asset`
- **Purpose:** Mark asset as returned
- **Authentication:** `@login_required`
- **Form Fields:**
  - `return_notes` (textarea, optional)
- **Validation:**
  - `returned_date` (datetime.now()) must not be before `assignment.assigned_date`; if invalid, flash danger and redirect to return form
- **Behavior:**
  1. Fetch active assignment
  2. Set `assignment.return_notes` and `assignment.returned_date`
  3. Commit
  4. Log audit (`RETURN`, `assignments`, new_value includes asset name, employee name, returned_date)
  5. Flash success, redirect to `assets.detail`

#### `GET /assets/print/<int:asset_id>` -- `assets.print_report`
- **Purpose:** Download HTML asset report
- **Authentication:** `@login_required`
- **Behavior:**
  1. Fetch asset (404 if not found)
  2. Fetch all assignments for asset (ordered by assigned_date DESC)
  3. Generate inline-styled HTML document
  4. Log audit (`EXPORT`, `assets`)
  5. Return `Response` with `Content-Disposition: attachment; filename="Asset_Report_<serial>_<timestamp>.html"`
- **Report Content:** Asset info (name, serial, category, vendor, purchase date, status) + assignment history table with employee, dates, notes, status badges

### 4.4 Employees Blueprint (`/employees`)

#### `GET /employees/list` -- `employees.list`
- **Purpose:** List all employees with search and filter
- **Authentication:** None (public)
- **Template:** `employees_list.html`
- **Query Parameters:**
  - `search` (string) -- filters by name, employee_id, position (ILIKE)
  - `company` (string) -- exact match on company
- **Data Passed:** `employees`, `search_query`, `company_filter`, `companies` (distinct list, non-null)
- **Behavior:** Ordered by `created_at DESC`. Add Employee button visible only when authenticated.

#### `GET /employees/detail/<int:employee_id>` -- `employees.detail`
- **Purpose:** Show single employee detail with asset assignment history
- **Authentication:** None (public)
- **Template:** `employee_detail.html`
- **Data Passed:** `employee`, `assignments` (ordered by `assigned_date DESC`)
- **Behavior:** 404 if employee not found. Action buttons visible only when authenticated.

#### `GET /employees/add` -- `employees.add`
- **Purpose:** Display add employee form
- **Authentication:** `@login_required`
- **Template:** `employee_form.html` (no `employee` context -- create mode)

#### `POST /employees/add` -- `employees.add`
- **Purpose:** Create new employee
- **Authentication:** `@login_required`
- **Form Fields:**
  - `employee_id` (text, required, unique)
  - `name` (text, required)
  - `position` (text, optional)
  - `company` (text, optional)
  - `photo` (file, optional, accept=image/*)
- **Photo Handling:**
  - If photo provided: generate filename `emp_<employee_id>_<8-char-uuid-hex>_<original-filename>`
  - Save to `app/static/uploads/` (create dir if not exists)
  - Set `photo_url = '/static/uploads/<filename>'`
- **Validation:** Check for duplicate `employee_id`; if exists, flash danger and redirect to list
- **Success:** Insert Employee, commit, log audit (`CREATE`, `employees`), flash success, redirect to `employees.list`

#### `GET /employees/edit/<int:employee_id>` -- `employees.edit`
- **Purpose:** Display edit employee form (pre-filled)
- **Authentication:** `@login_required`
- **Template:** `employee_form.html` (with `employee` context -- edit mode)

#### `POST /employees/edit/<int:employee_id>` -- `employees.edit`
- **Purpose:** Update existing employee
- **Authentication:** `@login_required`
- **Form Fields:** Same as add (employee_id is NOT editable -- not present in form for edit mode effectively, though not explicitly prevented)
- **Behavior:**
  1. Capture old values (name, position, company)
  2. Update fields
  3. If new photo uploaded: generate filename `emp_<id>_<8-char-uuid-hex>_<filename>`, save, update `photo_url`
  4. Commit
  5. Log audit (`UPDATE`, `employees`, old_value + new_value)
  6. Flash success, redirect to `employees.detail`

#### `POST /employees/delete/<int:employee_id>` -- `employees.delete`
- **Purpose:** Delete an employee
- **Authentication:** `@login_required`
- **Validation:** Check for active assignments (returned_date IS NULL). If any exist, flash danger (`'Cannot delete employee with active asset assignments! Please return all assets first.'`) and redirect to detail.
- **Behavior:**
  1. Fetch employee (404 if not found)
  2. Count active assignments; if > 0, block deletion
  3. Log audit (`DELETE`, `employees`, old_value)
  4. Delete employee (does NOT cascade delete assignments -- only possible if no active assignments exist; historical assignments remain in DB with broken FK if employee deleted)
  5. Commit
  6. Flash success, redirect to `employees.list`

#### `GET /employees/print/<int:employee_id>` -- `employees.print_report`
- **Purpose:** Download HTML employee report
- **Authentication:** `@login_required`
- **Behavior:**
   1. Fetch employee (404 if not found)
   2. Fetch all assignments for employee (ordered by assigned_date DESC)
   3. Generate inline-styled HTML document with two tables: Currently Assigned Assets and Full Assignment History
   4. Log audit (`EXPORT`, `employees`)
   5. Return `Response` with `Content-Disposition: attachment; filename="Employee_Report_<employee_id>_<timestamp>.html"`

### 4.5 Export Blueprint (`/export`)

#### `GET /export/csv` -- `export.export_csv`
- **Purpose:** Download complete CSV report
- **Authentication:** `@login_required`
- **Behavior:**
  1. Generate CSV with three sections:
     - **=== ASSETS ===**: Columns = ID, Name, Serial Number, Category, Purchased From, Purchased Date, Status, Assigned To
     - **=== EMPLOYEES ===**: Columns = ID, Employee ID, Name, Position, Company, Total Assets Assigned, Currently Assigned
     - **=== ASSIGNMENT HISTORY ===**: Columns = Asset, Asset Serial, Employee, Employee ID, Assigned Date, Returned Date, Status, Assign Notes, Return Notes
  2. Log audit (`EXPORT`, `reports`, format=CSV)
  3. Return `Response` with `Content-Type: text/csv` and `Content-Disposition: attachment; filename="asset_report_<timestamp>.csv"`

#### `GET /export/html` -- `export.export_html`
- **Purpose:** Download complete HTML report
- **Authentication:** `@login_required`
- **Behavior:**
  1. Query all assets, employees, assignments
  2. Generate inline-styled HTML document with:
     - Summary cards (Total Assets, Assigned, Available)
     - Assets table
     - Employees table
     - Assignment History table
  3. Log audit (`EXPORT`, `reports`, format=HTML)
  4. Return `Response` with `Content-Type: text/html` and `Content-Disposition: attachment; filename="asset_report_<timestamp>.html"`

---

## 5. Complete Data Flow

### 5.1 Asset CRUD Flow

#### Add Asset
```
User clicks "Add New Asset" (visible only if authenticated)
  -> GET /assets/add
  -> Render asset_form.html (no asset object -- create mode)
User fills form, clicks "Save Asset"
  -> POST /assets/add
  -> Parse form fields
  -> Validate: if purchased_date is future:
       -> flash('Not able to add asset in the future date!', 'danger')
       -> redirect /assets/add
  -> Validate: if serial_number already exists:
       -> flash('Asset with Serial Number "..." already exists!', 'danger')
       -> redirect /assets/list
  -> Create Asset model instance
  -> db.session.add(asset)
  -> db.session.commit()
  -> AuditLog.log('CREATE', 'assets', asset.id, new_value={...}, user_id=current_user.id)
  -> flash('Asset "..." added successfully!', 'success')
  -> redirect /assets/list
```

#### Edit Asset
```
User navigates to asset detail page, clicks "Edit" (visible only if authenticated)
  -> GET /assets/edit/<id>
  -> Fetch Asset (404 if not found)
  -> Render asset_form.html with asset object (edit mode -- pre-filled)
User modifies fields, clicks "Update Asset"
  -> POST /assets/edit/<id>
  -> Capture old_values dict
  -> Update asset fields from form
  -> Validate: if purchased_date is future:
       -> flash('Not able to add asset in the future date!', 'danger')
       -> redirect /assets/edit/<id>
  -> db.session.commit()
  -> AuditLog.log('UPDATE', 'assets', asset.id, old_value=..., new_value=..., user_id=current_user.id)
  -> flash('Asset "..." updated successfully!', 'success')
  -> redirect /assets/detail/<id>
```

#### Delete Asset
```
User navigates to asset detail page, clicks "Delete" (visible only if authenticated)
  -> JavaScript confirm dialog
  -> POST /assets/delete/<id>
  -> Fetch Asset (404 if not found)
  -> AuditLog.log('DELETE', 'assets', asset_id, old_value=..., user_id=current_user.id)
  -> Assignment.query.filter_by(asset_id=asset_id).delete()   # Cascade delete assignments
  -> db.session.delete(asset)
  -> db.session.commit()
  -> flash('Asset "..." deleted successfully!', 'success')
  -> redirect /assets/list
```

### 5.2 Employee CRUD Flow

#### Add Employee
```
User clicks "Add New Employee" (visible only if authenticated)
  -> GET /employees/add
  -> Render employee_form.html (no employee object -- create mode)
User fills form, optionally uploads photo, clicks "Save Employee"
  -> POST /employees/add (enctype=multipart/form-data)
  -> Parse form fields
  -> Handle photo upload:
       if photo and photo.filename:
         -> Generate uuid-based filename
         -> os.makedirs(upload_folder, exist_ok=True)
         -> photo.save(photo_path)
         -> photo_url = '/static/uploads/<filename>'
  -> Validate: if employee_id already exists:
       -> flash('Employee with ID "..." already exists!', 'danger')
       -> redirect /employees/list
  -> Create Employee model instance
  -> db.session.add(employee)
  -> db.session.commit()
  -> AuditLog.log('CREATE', 'employees', employee.id, new_value={...}, user_id=current_user.id)
  -> flash('Employee "..." added successfully!', 'success')
  -> redirect /employees/list
```

#### Edit Employee
```
User navigates to employee detail page, clicks "Edit" (visible only if authenticated)
  -> GET /employees/edit/<id>
  -> Fetch Employee (404 if not found)
  -> Render employee_form.html with employee object (edit mode -- pre-filled)
User modifies fields, optionally uploads new photo, clicks "Update Employee"
  -> POST /employees/edit/<id> (enctype=multipart/form-data)
  -> Capture old_values dict
  -> Update employee fields
  -> Handle photo upload (same as add, but filename uses employee.id)
  -> db.session.commit()
  -> AuditLog.log('UPDATE', 'employees', employee.id, old_value=..., new_value=..., user_id=current_user.id)
  -> flash('Employee "..." updated successfully!', 'success')
  -> redirect /employees/detail/<id>
```

#### Delete Employee
```
User navigates to employee detail page, clicks "Delete" (visible only if authenticated)
  -> JavaScript confirm dialog
  -> POST /employees/delete/<id>
  -> Fetch Employee (404 if not found)
  -> Count active assignments (returned_date IS NULL) for this employee
  -> Guard: if active_assignments > 0:
       -> flash('Cannot delete employee with active asset assignments!', 'danger')
       -> redirect /employees/detail/<id>
  -> AuditLog.log('DELETE', 'employees', employee.id, old_value=..., user_id=current_user.id)
  -> db.session.delete(employee)
  -> db.session.commit()
  -> flash('Employee "..." deleted successfully!', 'success')
  -> redirect /employees/list
```

### 5.3 Asset Assignment Flow

#### Assign Asset
```
User navigates to asset detail page, clicks "Assign to Employee" (visible only if authenticated)
  -> GET /assets/assign/<asset_id>
  -> Fetch Asset (404 if not found)
  -> Guard: if active_assignment exists:
       -> flash('This asset is already assigned to someone!', 'warning')
       -> redirect /assets/detail/<asset_id>
  -> Render assign_asset.html with asset, employees list, today date

User selects employee, optionally adds notes, clicks "Confirm Assignment"
  -> POST /assets/assign/<asset_id>
  -> Guard: same as GET (double-check)
  -> Parse employee_id, notes
  -> Create Assignment with assigned_date = datetime.now()
  -> db.session.add(assignment)
  -> db.session.commit()
  -> AuditLog.log('ASSIGN', 'assignments', assignment.id, new_value={...}, user_id=current_user.id)
  -> flash('Asset "..." assigned to ...!', 'success')
  -> redirect /assets/detail/<asset_id>
```

#### Return Asset
```
User navigates to asset detail page (asset is assigned), clicks "Mark as Returned"
  -> GET /assets/return/<asset_id>
  -> Fetch Asset (404 if not found)
  -> Guard: if no active assignment:
       -> flash('This asset is not currently assigned!', 'warning')
       -> redirect /assets/detail/<asset_id>
  -> Render return_asset.html with asset and assignment info

User optionally adds return notes, clicks "Confirm Return"
  -> POST /assets/return/<asset_id>
  -> Parse return_notes
  -> Set returned_date = datetime.now()
  -> Validate: if returned_date < assignment.assigned_date:
       -> flash('Return date cannot be before assigned date!', 'danger')
       -> redirect /assets/return/<asset_id>
  -> assignment.return_notes = return_notes
  -> assignment.returned_date = returned_date
  -> db.session.commit()
  -> AuditLog.log('RETURN', 'assignments', assignment.id, new_value={...}, user_id=current_user.id)
  -> flash('Asset "..." returned from ...!', 'success')
  -> redirect /assets/detail/<asset_id>
```

### 5.4 Export Flow

#### CSV Export
```
User clicks "Export CSV" button (visible on dashboard when authenticated)
  -> GET /export/csv
  -> @login_required
  -> Create io.StringIO buffer
  -> Write header rows: report title, timestamp, blank line
  -> Write === ASSETS === section:
       Query all assets; for each: write ID, Name, Serial Number, Category, Purchased From, Purchased Date, Status, Assigned To
  -> Write === EMPLOYEES === section:
       Query all employees; for each: write ID, Employee ID, Name, Position, Company, Total Assigned, Currently Assigned
  -> Write === ASSIGNMENT HISTORY === section:
       Query all assignments (ordered by assigned_date DESC); for each: write Asset, Serial, Employee, Employee ID, Assigned Date, Returned Date, Status, Assign Notes, Return Notes
  -> AuditLog.log('EXPORT', 'reports', new_value={format: 'CSV', filename: ...}, user_id=current_user.id)
  -> Return Response with Content-Type: text/csv, Content-Disposition: attachment
```

#### HTML Export
```
User clicks "Export HTML Report" button (visible on dashboard when authenticated)
  -> GET /export/html
  -> @login_required
  -> Query all assets, all employees, all assignments
    -> Generate full inline-styled HTML document containing:
        - Summary section with timestamp
        - Summary cards (Total Assets, Assigned, Available) with left-border accents
        - Assets table (ID, Name, Serial, Category, Vendor, Date, Status, Assigned To)
        - Employees table (ID, Employee ID, Name, Position, Company, Total Assigned, Currently Using)
        - Assignment History table (Asset, Serial, Employee, Emp ID, Assigned Date, Returned Date, Status, Notes) with `word-break: break-word`
   -> AuditLog.log('EXPORT', 'reports', new_value={format: 'HTML', filename: ...}, user_id=current_user.id)
   -> Return Response with Content-Type: text/html, Content-Disposition: attachment
```

### 5.5 Print Report Flow

#### Asset Print Report
```
User clicks "Download Report" on asset detail page
   -> GET /assets/print/<asset_id>
   -> @login_required
   -> Fetch asset and all assignments
   -> Generate inline-styled standalone HTML document
   -> AuditLog.log('EXPORT', 'assets', ...)
   -> Return as attachment download
```

#### Employee Print Report
```
User clicks "Download Report" on employee detail page
   -> GET /employees/print/<employee_id>
   -> @login_required
   -> Fetch employee and all assignments
   -> Generate inline-styled standalone HTML document
   -> Columns: Asset Name, Serial, Category, Emp ID, Assigned Date, Returned Date, Status, Assign Notes, Return Notes (Status before notes)
   -> AuditLog.log('EXPORT', 'employees', ...)
   -> Return as attachment download
```

### 5.6 Authentication Flow

#### Login
```
User clicks "Admin Login" in navbar (visible when not authenticated)
  -> GET /auth/login
  -> If already authenticated: redirect to dashboard
  -> Render login.html

User enters username/password, clicks "Login"
  -> POST /auth/login
  -> Query User by username
  -> If user exists AND check_password(password) passes:
        -> login_user(user)
        -> AuditLog.log('LOGIN', 'users', user.id)
       -> flash('Welcome back!', 'success')
       -> Redirect to ?next= parameter or dashboard
  -> Else:
       -> flash('Invalid username or password', 'danger')
       -> Re-render login.html
```

#### Logout
```
User clicks "Logout" in navbar (visible when authenticated)
  -> GET /auth/logout
  -> @login_required guard (redirects to /auth/login if not authenticated)
  -> AuditLog.log('LOGOUT', 'users', current_user.id)
  -> logout_user()
  -> flash('You have been logged out.', 'info')
  -> redirect to dashboard
```

### 5.7 Audit Log Flow
```
Every mutating operation follows this pattern:
  1. Perform the operation (create/update/delete/assign/return)
  2. Commit to database
  3. Call AuditLog.log(action, table_name, record_id, old_value, new_value, user_id)
  4. AuditLog.log() creates AuditLog instance, JSON-serializes old/new values, adds to session, commits
  5. Return response to user

Authenticated actions always include current_user.id.
Default admin creation logs with user_id = admin.id (self-referential).
```

---

## 6. Frontend / Template Structure

### 6.1 Template Inheritance Chain
```
base.html
  -> login.html
  -> dashboard.html
  -> assets_list.html
  -> asset_detail.html*
  -> asset_form.html
  -> assign_asset.html
  -> return_asset.html
  -> employees_list.html
  -> employee_detail.html*
  -> employee_form.html
    * asset_detail.html and employee_detail.html use {% block extra_js %} for optional scripts
```

### 6.2 Base Template (`base.html`)
- **CSS Dependencies:**
  - Inter font (Google Fonts CDN)
  - Bootstrap 5.3.2 (CDN)
  - Bootstrap Icons 1.11.1 (CDN)
  - Custom CSS (`/static/css/custom.css`)
- **JS Dependencies:**
  - Bootstrap 5.3.2 bundle (CDN)
  - Custom JS (`/static/js/custom.js`)
- **Layout:**
  - Fixed-top navbar with brand ("Asset Manager"), navigation links (Dashboard, Assets, Employees), username display + Logout button (when authenticated), or Admin Login button (when anonymous)
  - Breadcrumb navigation bar (below navbar) showing current page hierarchy
  - Toast notification container (position-fixed, top-right, z-index 9999)
  - Flash message `div.alert` elements (hidden via inline `<style>.alert{display:none!important}</style>` before Bootstrap loads, plus `.d-none`)
  - Main content block (`{% block content %}`)
  - Footer (copyright)
  - `{% block extra_js %}` for page-specific scripts

### 6.3 Toast Notification System
1. Server sets flash messages with categories (success, danger, warning, info)
2. `base.html` renders flash messages as hidden `div.alert` elements with `.d-none` class
3. `custom.js` on page load:
   - Iterates all `.alert` elements
   - Detects category from CSS class (`alert-success`, `alert-danger`, `alert-warning`, `alert-info`)
   - Extracts text content (excluding child nodes like button)
   - Calls `showToast(title, message, category)` which:
     - Sets toast title and message
     - Sets appropriate icon class (bi-check-circle, bi-x-circle, etc.)
     - Shows Bootstrap toast with 5-second delay
   - Hides alert elements after 100ms

### 6.4 Form Submission Spinner Behavior
- `custom.js` attaches `submit` event listener to all `form[method="POST"]` elements
- On submit: finds the submit button
- If button does NOT have class `.no-spinner`:
  - Disables the button
  - Replaces inner HTML with `<span class="spinner-border spinner-border-sm me-2"></span>Processing...`
- Exception: `.no-spinner` class is applied to the return form's Confirm Return button (to allow redirect behavior)

### 6.5 Key UI Components

#### Stat Cards (dashboard.html)
Three white cards with left-border accent in a row:
- Total Assets (blue left border, `bi-box-seam`)
- Assigned (orange left border, `bi-people`)
- Available (green left border, `bi-check-circle`)

#### Asset Table (assets_list.html)
- Search bar (name, serial, category)
- Category dropdown filter (distinct categories from DB)
- Status dropdown filter (All / Available / Assigned)
- Table columns: Name (linked), Serial Number, Category, Purchased From, Purchased Date, Status (badge with employee name or "Available"), Actions (View button, Download Report button)
- "Add New Asset" button (visible when authenticated)

Note: The Download Report button generates a standalone HTML report document with `btn-outline-primary btn-sm` styling.

#### Asset Detail (asset_detail.html)
- Asset info card and assignment history table stacked vertically in full-width cards
- Single "Download Report" button (HTML report only)

Note: The Download Report button generates a standalone HTML report document.

#### Employee Table (employees_list.html)
- Search bar (name, ID, position)
- Company dropdown filter (distinct companies from DB)
- Table columns: Employee (photo/initials + name linked), Employee ID, Position, Company, Current Assets (count badge), Total History (count badge), Actions (View button)

#### Employee Detail (employee_detail.html)
- Full-width layout
- Left profile card (4 cols): Photo or initials circle, name, position, employee ID, company, join date, action buttons
- Right section (8 cols): Currently Assigned Assets table + Full Assignment History table

Note: The Download Report button generates a standalone HTML report document with `btn-outline-primary btn-sm` styling.

#### Forms
- `asset_form.html`: Fields = Name, Serial Number (text), Category (select from predefined list), Purchased From (text), Purchased Date (date input)
- `employee_form.html`: Fields = Employee ID (text), Full Name (text), Position (text), Company (text), Photo (file input, accept=image/*). Has `enctype="multipart/form-data"`. Shows current photo thumbnail in edit mode.
- `assign_asset.html`: Asset info alert, Employee dropdown, Assign Notes textarea (no date field -- timestamp is auto-recorded)
- `return_asset.html`: Assignment info alert (asset, serial, assigned to, assigned date), Return Notes textarea (no date field -- timestamp is auto-recorded)

### 6.6 Toast Notification Implementation Detail
The toast notification system uses Bootstrap 5 Toasts:
1. Flash messages are stored as hidden `div.alert.d-none` elements with category classes
2. On page load, `custom.js` iterates `.alert` elements, extracts text content (excluding child nodes), maps category to icon:
   - `success` -> `bi-check-circle-fill` (green)
   - `danger` -> `bi-x-circle-fill` (red)
   - `warning` -> `bi-exclamation-triangle-fill` (yellow)
   - `info` -> `bi-info-circle-fill` (blue)
3. Toast title is set to the flash message text (no separate body section)
4. Toasts auto-hide after 5 seconds
5. All alert elements are hidden 100ms after processing

---

## 7. Security

### 7.1 Authentication
- All mutation routes (add/edit/delete/assign/return/export/print/logout) are protected by Flask-Login's `@login_required` decorator
- List and detail views are public (read-only access without login)
- Login is required for the `next` parameter (redirect after login)

### 7.2 Session Management
- Sessions are non-permanent, deleted when browser closes
- `SESSION_COOKIE_HTTPONLY = True` -- JavaScript cannot access session cookie
- `SESSION_COOKIE_SECURE = False` -- cookies sent over HTTP (development mode)
- `SECRET_KEY` defaults to `'asset-mgmt-secret-key-2024-v2'` (configurable via `SECRET_KEY` environment variable)
- Changing `SECRET_KEY` invalidates all existing sessions

### 7.3 Password Security
- Passwords hashed using Werkzeug's `generate_password_hash` (default: pbkdf2:sha256)
- Default admin password `123456` -- documented for development; production should change
- No password change/reset mechanism (admin credentials are set via the default admin seeder)

### 7.4 File Upload Security
- Photo upload filename uses UUID hex (8 chars) to prevent filename collisions and predictable filenames:
  - Pattern: `emp_<employee_id>_<uuid_hex8>_<original_filename>`
- Max content length set to 16MB (`MAX_CONTENT_LENGTH = 16 * 1024 * 1024`)
- Upload folder: `app/static/uploads/` (auto-created)
- No explicit file type validation beyond browser's `accept="image/*"`

### 7.5 Input Validation
- Serial number uniqueness enforced on asset creation (duplicate check before insert)
- Employee ID uniqueness enforced on employee creation
- Future date prohibited for purchased_date (compared against `datetime.now().date()`)
- Return date validated to not be before assigned date

### 7.6 CSRF Protection
- No explicit CSRF tokens (no Flask-WTF CSRF protection used)
- Forms use POST method but lack CSRF tokens
- The application relies on the `@login_required` decorator and session-based auth as implicit protection

---

## 8. Data Portability

### 8.1 File Paths
- **Database:** `instance/assets.db` (relative to project root; path built in `config.py`)
- **Photo uploads:** `app/static/uploads/` (relative to project root)
- **All paths are relative** -- no absolute paths are hardcoded

### 8.2 Transfer Procedure
1. Copy the entire `asset_management/` folder to the target machine
2. Ensure Python 3.8+ is installed
3. `pip install -r requirements.txt`
4. `python3 run.py`
5. Open browser to `http://127.0.0.1:5000`

### 8.3 Data Persistence
- The SQLite database file (`instance/assets.db`) persists all data between restarts
- Deleting `instance/assets.db` and restarting will recreate the database with a fresh schema and default admin user
- Photo files in `app/static/uploads/` persist independently of the database

### 8.4 Dependencies
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Bootstrap4==4.0.2
Werkzeug==3.0.1
python-dotenv==1.0.0
```

---

## 9. Configuration Reference

### 9.1 Config Class (`app/config.py`)

| Key                        | Default Value                                      | Description                        |
|----------------------------|----------------------------------------------------|------------------------------------|
| `SECRET_KEY`               | `asset-mgmt-secret-key-2024-v2` (or env var)       | Flask session signing key          |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False`                                       | Disable SQLAlchemy event system    |
| `SQLALCHEMY_DATABASE_URI`  | `sqlite:///<project_root>/instance/assets.db` (or env var) | Database connection string  |
| `UPLOAD_FOLDER`            | `app/static/uploads/`                              | Employee photo upload directory    |
| `MAX_CONTENT_LENGTH`       | `16 * 1024 * 1024` (16MB)                          | Max upload file size               |
| `SESSION_COOKIE_SECURE`    | `False`                                            | Allow cookies over HTTP            |
| `SESSION_COOKIE_HTTPONLY`  | `True`                                             | Prevent JS cookie access           |

---

## 10. Known Limitations and Observations

1. **No CSRF Protection:** Forms use plain POST without CSRF tokens -- vulnerable to cross-site request forgery.
2. **Cascade Delete on Assets:** Deleting an asset deletes all related Assignment records via `Assignment.query.filter_by(asset_id=asset_id).delete()`. Historical audit log entries referencing the asset/assignment IDs remain (value data is JSON-stringified at log time).
3. **Orphaned Assignments on Employee Delete:** Deleting an employee does NOT cascade to assignments (only blocked if active assignments exist). If an employee with only returned (historical) assignments is deleted, those assignment records remain in the DB with `employee_id` pointing to a non-existent employee, causing template rendering errors if those records are accessed.
4. **No Input Sanitization:** User-supplied values (particularly `notes`, `return_notes`, `name`, etc.) are rendered directly in templates without explicit escaping (Jinja2 auto-escapes by default, but HTML report generation uses f-strings which do NOT auto-escape).
5. **Upload File Type Validation:** No server-side validation of uploaded file types beyond the `MAX_CONTENT_LENGTH` size limit.
6. **Session Non-Persistence:** Session cookies are deleted when the browser closes (non-permanent sessions). The `SECRET_KEY` was updated to `v2` to invalidate any lingering persistent sessions.
