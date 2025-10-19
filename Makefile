.PHONY: help validate smoke usage monthend test-api test-e2e lint format clean

# Default target
help:
	@echo "AI Bookkeeper - Ad-Ready Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make validate   - Run pre-launch validation (all 8 criteria)"
	@echo "  make smoke      - Run E2E smoke tests against staging/production"
	@echo "  make usage      - Simulate transaction usage (600 tx for testing)"
	@echo "  make monthend   - Run month-end billing job"
	@echo "  make test-api   - Run API tests"
	@echo "  make test-e2e   - Run all E2E tests"
	@echo "  make lint       - Run linters (Python + TypeScript)"
	@echo "  make format     - Format code (Black + Prettier)"
	@echo "  make clean      - Clean temporary files"

# Pre-launch validation
validate:
	@echo "Running pre-launch validation..."
	@python3 scripts/validate_prelaunch.py --verbose

# E2E smoke tests
smoke:
	@echo "Running E2E smoke tests..."
	@cd frontend && npx playwright test ../e2e/ads_ready.spec.ts

# Simulate usage
usage:
	@echo "Simulating transaction usage..."
	@python3 scripts/simulate_usage.py

# Month-end billing
monthend:
	@echo "Running month-end billing..."
	@python3 scripts/run_month_end.py

# Month-end dry run
monthend-dry:
	@echo "Running month-end billing (DRY RUN)..."
	@python3 scripts/run_month_end.py --dry-run

# API tests
test-api:
	@echo "Running API tests..."
	@pytest tests/test_billing_v2.py -v

# All E2E tests
test-e2e:
	@echo "Running all E2E tests..."
	@cd frontend && npx playwright test ../e2e/

# Run all tests
test-all: test-api test-e2e

# Lint Python
lint-py:
	@echo "Linting Python..."
	@flake8 app/ scripts/ tests/ --max-line-length=120 --extend-ignore=E203,W503 || true

# Lint TypeScript
lint-ts:
	@echo "Linting TypeScript..."
	@cd frontend && npm run lint || true

# Lint all
lint: lint-py lint-ts

# Format Python
format-py:
	@echo "Formatting Python..."
	@black app/ scripts/ tests/ --line-length=120 || true

# Format TypeScript
format-ts:
	@echo "Formatting TypeScript..."
	@cd frontend && npx prettier --write "**/*.{ts,tsx,js,jsx}" || true

# Format all
format: format-py format-ts

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ Clean complete"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@cd frontend && npm install
	@echo "✅ Dependencies installed"

# Install Playwright browsers
install-playwright:
	@echo "Installing Playwright browsers..."
	@cd frontend && npx playwright install
	@echo "✅ Playwright browsers installed"

# Start local development
dev-api:
	@echo "Starting API server..."
	@python3 -m uvicorn app.api.main:app --reload --port 8000

dev-web:
	@echo "Starting frontend..."
	@cd frontend && npm run dev

# Database migrations
migrate:
	@echo "Running database migrations..."
	@alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@alembic revision --autogenerate -m "$(MSG)"

# Health checks
health:
	@echo "Checking API health..."
	@curl -s https://api.ai-bookkeeper.app/healthz | jq .
	@echo ""
	@echo "Checking frontend..."
	@curl -s -o /dev/null -w "Status: %{http_code}\n" https://app.ai-bookkeeper.app/

# Deploy (requires Render CLI)
deploy-api:
	@echo "Deploying API to Render..."
	@git push origin main
	@echo "✅ Pushed to GitHub. Render will auto-deploy."

deploy-web:
	@echo "Deploying frontend to Render..."
	@git push origin main
	@echo "✅ Pushed to GitHub. Render will auto-deploy."

# Stripe setup verification
verify-stripe:
	@echo "Verifying Stripe configuration..."
	@python3 -c "import json; data = json.load(open('config/stripe_price_map.json')); print('✅ Loaded', len(data.get('plans', {})), 'plans,', len(data.get('overage', {})), 'overage prices,', len(data.get('addons', {})), 'add-ons')"

# Show environment variables needed
env-check:
	@echo "Checking required environment variables..."
	@echo "Backend:"
	@python3 -c "import os; vars = ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'ALLOWED_ORIGINS']; [print(f'  {v}: {\"✅\" if os.getenv(v) else \"❌\"}') for v in vars]"
	@echo "Frontend:"
	@echo "  NEXT_PUBLIC_API_URL: $$NEXT_PUBLIC_API_URL"
	@echo "  NEXT_PUBLIC_GA_ID: $$NEXT_PUBLIC_GA_ID"

