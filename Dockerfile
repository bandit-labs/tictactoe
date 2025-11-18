FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY TicTacToe/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy this folder (TicTacToe) into /app/TicTacToe inside container
COPY TicTacToe /app/TicTacToe

# Make TicTacToe a Python package
RUN touch /app/TicTacToe/__init__.py
RUN touch /app/TicTacToe/api/__init__.py
RUN touch /app/TicTacToe/engine/__init__.py

EXPOSE 8000

CMD ["uvicorn", "TicTacToe.app:app", "--host", "0.0.0.0", "--port", "8000"]
