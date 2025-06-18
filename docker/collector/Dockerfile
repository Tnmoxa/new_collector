FROM python:3.12.1-slim as builder

WORKDIR /install

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip wheel --no-deps --wheel-dir /wheels -r requirements.txt

FROM python:3.12.1-slim

WORKDIR /collector

COPY --from=builder /wheels /wheels

COPY requirements.txt .

RUN pip install --no-deps --no-index --find-links=/wheels -r requirements.txt

COPY . .

CMD ["python3", "statistics_collector/main.py"]