FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create templates directory if not exists and copy templates
RUN mkdir -p templates
COPY templates/ templates/

ENV FLASK_APP=app.py
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV BASE_URL=http://localhost:5000

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]