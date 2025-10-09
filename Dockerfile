# Backend image (dev)
FROM python:3.11-slim AS backend-dev
WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
# For dev we will run with --reload via flask or use watchdog
WORKDIR /app/backend
CMD ["python", "app.py"]

# Frontend image (dev)
FROM node:20-alpine AS frontend-dev
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
WORKDIR /app/frontend
CMD ["npm", "start"]
