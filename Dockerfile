FROM python:3.12-slim

WORKDIR /app

# Copy backend and frontend
COPY backend/ ./backend/
COPY assets/ ./assets/
COPY pages/ ./pages/
COPY components/ ./components/
COPY index.html ./

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 5000

# Run from project root so static_folder='../' resolves correctly
CMD ["python", "backend/app.py"]
