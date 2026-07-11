.PHONY: install run backend frontend deploy undeploy

# Suppress disruptive Python warnings (like Experimental Features)
export PYTHONWARNINGS=ignore

# ---------------------------------------------------------
# Installs all necessary dependencies (Python & Node)
# ---------------------------------------------------------
install:
	@echo "--- Installing Python backend dependencies via uv..."
	uv sync --link-mode=copy
	@echo "--- Installing React frontend dependencies via npm..."
	cd frontend && npm install
	@echo "--- Installation complete! You can now use 'make run'."

# ---------------------------------------------------------
# Starts the servers
# ---------------------------------------------------------
run:
	@echo ""
	@echo "**********************************************************"
	@echo "*                                                        *"
	@echo "*     SOCRATIC DUEL IS STARTING...                       *"
	@echo "*                                                        *"
	@echo "*     NOTE: Please ignore the 127.0.0.1 address!         *"
	@echo "*                                                        *"
	@echo "*  -> OPEN YOUR BROWSER HERE: http://localhost:5173      *"
	@echo "*                                                        *"
	@echo "**********************************************************"
	@echo ""
	@uv run python -c "input('>>> Press ENTER to start the servers... ')"
	@make -j 2 backend frontend

backend:
	@echo "--- Starting Uvicorn API Server..."
	uv run python -m uvicorn app.main:app --reload --reload-dir app

frontend:
	@echo "--- Starting Vite Development Server..."
	cd frontend && npm run dev

# ---------------------------------------------------------
# Deployment to Google Cloud
# ---------------------------------------------------------
deploy:
	@echo ""
	@echo "========================================================="
	@echo "   PREREQUISITES FOR GOOGLE CLOUD DEPLOYMENT"
	@echo "========================================================="
	@echo " 1. CLI: The 'Google Cloud CLI' (gcloud) must be installed."
	@echo " 2. LOGIN: You must be logged in -> 'gcloud auth login'"
	@echo " 3. PROJECT: An active project must be set -> 'gcloud config set project YOUR_PROJECT_ID'"
	@echo " 4. APIs: The following APIs must be enabled in the Cloud project:"
	@echo "    - Cloud Build API    (cloudbuild.googleapis.com)"
	@echo "    - Cloud Run API      (run.googleapis.com)"
	@echo "    - Secret Manager API (secretmanager.googleapis.com)"
	@echo "    - Service Usage API  (serviceusage.googleapis.com)"
	@echo " 5. BILLING: The project must have an active billing account."
	@echo "========================================================="
	@echo ""
	@uv run python -c "input('>>> If all prerequisites are met, press ENTER for deployment... ')"
	@echo "--- Building and deploying application code to Cloud Run..."
	@uv run python -c "import subprocess, sys; p = subprocess.check_output('gcloud config get-value project', shell=True, text=True).strip(); sys.exit(subprocess.call(f'uvx google-agents-cli deploy --service-name socratic-duel-live --min-instances 0 --no-confirm-project --project {p}', shell=True))"
	@echo "--- Making the service public (Public Access)..."
	@uv run python -c "import subprocess, sys; p = subprocess.check_output('gcloud config get-value project', shell=True, text=True).strip(); sys.exit(subprocess.call(f'gcloud run services add-iam-policy-binding socratic-duel-live --region=us-east1 --member=allUsers --role=roles/run.invoker --project {p}', shell=True))"
	@echo "========================================================="
	@echo "🎉 Deployment successful!"

# ---------------------------------------------------------
# Removes the service from the Cloud
# ---------------------------------------------------------
undeploy:
	@echo ""
	@echo "========================================================="
	@echo "   DELETE SERVICE FROM GOOGLE CLOUD"
	@echo "========================================================="
	@uv run python -c "input('>>> WARNING: The service will be deleted. Press ENTER to confirm or CTRL+C to cancel... ')"
	@echo "--- Removing Cloud Run Service 'socratic-duel-live'..."
	gcloud run services delete socratic-duel-live --region=us-east1 --quiet
	@echo "--- Service successfully deleted!"

# ---------------------------------------------------------
# Run Tests
# ---------------------------------------------------------
test:
	@echo "--- Running Unit and Integration Tests..."
	uv run pytest tests/unit tests/integration --html=report.html --self-contained-html
