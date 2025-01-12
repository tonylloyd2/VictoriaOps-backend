
# FactoryOps Backend

FactoryOps is a robust backend solution designed to manage and optimize factory operations efficiently. This system integrates modules for production tracking, human resources, inventory management, order processing, and advanced analytics, enabling factories to improve productivity, reduce waste, and streamline workflows.

## Features

### 1. **Human Resource Management**
- Maintain detailed employee records, including roles, salaries, and contact information.
- Role-based access control for different levels of employees (e.g., factory workers, managers).
- Attendance tracking with status (Present, Absent, Leave) and working hours.
- Shift scheduling and productivity tracking per employee.
- Automated payroll calculations, including overtime and role-specific rates.
- Workforce analytics for performance reviews.

### 2. **Inventory Management**
- Real-time tracking of raw material stock levels (e.g., cement, sand, aggregates).
- Material categorization and unit-based stock management.
- Supplier management, including contact details and purchase orders.
- Automated reorder triggers based on stock levels and reorder points.
- Material cost tracking and analysis for budgeting.
- Stock audit records for accountability and traceability.

### 3. **Production Management**
- End-to-end tracking of production processes for items like blocks, cabros, and other products.
- Production scheduling tools for workflow optimization.
- Resource allocation for labor and materials during production.
- Quality control checkpoints and defect rate tracking to maintain standards.
- Integration with raw material usage to ensure efficient production.
- Real-time updates on production status (Scheduled, In Progress, Completed).

### 4. **Order Management**
- Customer order creation and management with real-time inventory checks.
- Tracking material availability for order fulfillment feasibility.
- Notifications for stock conflicts, order delays, or production bottlenecks.
- Delivery status tracking and order invoicing.
- Integration with finished goods inventory for seamless distribution.

### 5. **Product Management**
- Maintain a database of products with specifications and types.
- Forecast demand for products based on historical trends and analytics.
- Track production volumes and quality checks for finished goods.
- Finished goods inventory management with stock levels and availability.

### 6. **Output Tracking**
- Monitor and record production output, including finished goods ready for sale or delivery.
- Seamless integration between production and product inventory modules.
- Generate output reports detailing quantities produced, defect rates, and quality standards.

### 7. **Reporting and Analytics**
- Dynamic performance dashboards to visualize key metrics:
  - Production efficiency.
  - Material usage and costs.
  - Employee productivity and attendance.
- Generate customizable reports for factory managers, such as:
  - Daily/Weekly/Monthly production summaries.
  - Inventory usage and reorder alerts.
  - Workforce productivity analysis.
- Predictive analytics for demand forecasting and operational planning.

---

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL (or any other preferred relational database)
- Git
- Docker (for containerized deployment)

### Installation Steps
1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd FactoryOps
   ```

2. **Set Up a Virtual Environment:**
   ```bash
   python3 -m venv env
   source env/bin/activate  # For Linux/MacOS
   env\Scripts\activate     # For Windows
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file at the root directory and include the following:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=True
   DATABASE_URL=postgres://username:password@localhost:5432/factoryops
   ```

5. **Apply Database Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a Superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```

---

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login.
- `POST /api/auth/register/` - User registration.
- `POST /api/auth/logout/` - User logout.

### Human Resource Management
- `GET /api/hr/employees/` - List all employees.
- `POST /api/hr/employees/` - Add a new employee.
- `PATCH /api/hr/employees/<id>/` - Update employee details.
- `DELETE /api/hr/employees/<id>/` - Delete an employee.
- `GET /api/hr/attendance/` - View attendance records.

### Inventory Management
- `GET /api/inventory/materials/` - List materials and stock levels.
- `POST /api/inventory/materials/` - Add a new material.
- `GET /api/inventory/suppliers/` - List all suppliers.
- `POST /api/inventory/reorder/` - Create a reorder request.

### Production Management
- `POST /api/production/orders/` - Create a new production order.
- `GET /api/production/status/` - View production status.
- `POST /api/production/quality-check/` - Log quality control checks.

### Orders Management
- `GET /api/orders/` - List all orders.
- `POST /api/orders/` - Create a new customer order.
- `GET /api/orders/<id>/status/` - View the status of a specific order.

### Analytics
- `GET /api/analytics/reports/` - Generate performance reports.
- `GET /api/analytics/dashboard/` - View dashboard metrics.

---

## Testing

1. **Run Unit Tests:**
   ```bash
   python manage.py test
   ```

2. **Run Integration Tests:**
   ```bash
   pytest
   ```

---

## Deployment

### Using Docker
1. Build the Docker image:
   ```bash
   docker build -t factoryops-backend .
   ```

2. Run the Docker container:
   ```bash
   docker-compose up
   ```

---

## Contributing

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m 'Add feature-name'`.
4. Push to the branch: `git push origin feature-name`.
5. Submit a pull request for review.

---

## License

This project is licensed under the MIT License.
