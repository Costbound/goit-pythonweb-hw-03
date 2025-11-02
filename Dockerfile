FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-root

COPY . .

EXPOSE 3000

CMD ["poetry", "run", "python", "main.py"]