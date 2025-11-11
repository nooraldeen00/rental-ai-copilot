FROM python:3.12-slim

WORKDIR /app

# copy requirements first (for docker cache efficiency)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy entire backend code
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
