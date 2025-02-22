FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]
