# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.11-slim
WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy project configuration and dependency files
COPY pyproject.toml uv.lock ./

# Install python dependencies using uv
RUN uv sync --no-dev --frozen

# Copy the Python application code
COPY app ./app

# Copy the built React assets from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose the single port defined by Cloud Run (8080)
EXPOSE 8080

# Command to run the FastAPI server on 0.0.0.0:8080
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]