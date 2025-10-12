"""
Locust load testing configuration for AI Bookkeeper.

Usage:
    # Run with UI
    locust -f tests/performance/locustfile.py --host http://localhost:8000

    # Run headless
    locust -f tests/performance/locustfile.py --host http://localhost:8000 \
        --users 50 --spawn-rate 10 --run-time 5m --headless

    # Generate HTML report
    locust -f tests/performance/locustfile.py --host http://localhost:8000 \
        --users 50 --spawn-rate 10 --run-time 5m --headless \
        --html reports/load_test.html
"""
from locust import HttpUser, task, between, SequentialTaskSet
import json
import random
from datetime import datetime, timedelta


class AccountingWorkflow(SequentialTaskSet):
    """Sequential workflow simulating typical user actions."""
    
    def on_start(self):
        """Login and get token."""
        # Simulate login (adjust based on your auth implementation)
        response = self.client.post("/api/auth/login", json={
            "email": f"testuser{random.randint(1,100)}@example.com",
            "password": "test123"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Use dummy token for testing
            self.headers = {}
        
        # Select a random simulated company
        self.company_id = random.choice([
            "sim_hamilton_coffee",
            "sim_cincy_web",
            "sim_liberty_childcare",
            "sim_contreras_realestate",
            "sim_midwest_accounting"
        ])
    
    @task
    def view_dashboard(self):
        """Load dashboard (analytics)."""
        self.client.get(
            f"/api/analytics/automation-metrics",
            params={"company_id": self.company_id},
            headers=self.headers,
            name="/api/analytics/automation-metrics"
        )
    
    @task
    def view_transactions(self):
        """List transactions."""
        self.client.get(
            f"/api/transactions",
            params={"company_id": self.company_id, "limit": 50},
            headers=self.headers,
            name="/api/transactions"
        )
    
    @task
    def view_journal_entries(self):
        """List journal entries."""
        self.client.get(
            f"/api/journal-entries",
            params={"company_id": self.company_id, "status": "proposed", "limit": 50},
            headers=self.headers,
            name="/api/journal-entries"
        )
    
    @task
    def upload_transactions(self):
        """Upload a small CSV file."""
        # Generate small CSV
        csv_data = "date,amount,description,counterparty,currency\n"
        for i in range(10):
            date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
            amount = round(random.uniform(-500, 500), 2)
            csv_data += f"{date},{amount},Test Transaction {i},Test Vendor,USD\n"
        
        files = {'file': ('test.csv', csv_data, 'text/csv')}
        
        self.client.post(
            f"/api/ingest/csv",
            files=files,
            params={"company_id": self.company_id},
            headers=self.headers,
            name="/api/ingest/csv"
        )
    
    @task
    def propose_postings(self):
        """Request posting proposals."""
        self.client.post(
            f"/api/post/propose",
            json={
                "company_id": self.company_id,
                "limit": 20
            },
            headers=self.headers,
            name="/api/post/propose"
        )
    
    @task
    def run_reconciliation(self):
        """Run reconciliation."""
        self.client.post(
            f"/api/reconcile/run",
            json={"company_id": self.company_id},
            headers=self.headers,
            name="/api/reconcile/run"
        )
    
    @task
    def generate_pnl(self):
        """Generate P&L report."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        self.client.get(
            f"/api/analytics/pnl",
            params={
                "company_id": self.company_id,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            headers=self.headers,
            name="/api/analytics/pnl"
        )


class DashboardUser(HttpUser):
    """User that primarily views dashboards (read-heavy)."""
    tasks = [AccountingWorkflow]
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    weight = 3  # 3x more common than power users


class PowerUser(HttpUser):
    """Power user performing writes and batch operations."""
    tasks = [AccountingWorkflow]
    wait_time = between(1, 3)  # Faster workflow
    weight = 1


class HealthCheck(HttpUser):
    """Continuous health check monitoring."""
    wait_time = between(5, 10)
    weight = 1
    
    @task
    def check_health(self):
        """Check application health."""
        self.client.get("/healthz", name="/healthz")

