# Quality Assurance Test Plan: AlphaHub Distributed Infrastructure

**Автор**: Quinn (Test Architect & Quality Advisor BMad Agent)  
**Статус**: Production-Ready Test Spec  
**Методология**: BDD (Given-When-Then), Chaos Testing, Integration-First  
**Технологии**: Pytest, Testcontainers-python, K6 (Load Testing), Toxiproxy

---

## 1. Сценарии Тестирования (BDD Given-When-Then Specs)

Для подтверждения надежности системы и отказоустойчивости распределенных компонентов (вебхуки, Redis, RabbitMQ, TimescaleDB) мы внедряем следующие приемочные сценарии.

### 1.1. Вебхук-Шлюз: Нагрузочное тестирование и производительность (Load Test Gateway)
* **GIVEN** (Дано): FastAPI Webhook Gateway запущен в Docker с лимитом пула соединений DB = 10.
* **WHEN** (Когда): Утилита K6 подает нагрузку 1000 запросов/сек в течение 5 минут на эндпоинт `/gateway/evm`.
* **THEN** (Тогда): Шлюз возвращает `HTTP 202` на все запросы, среднее время ответа (p95) составляет `< 100ms`, и утилита мониторинга фиксирует 0 потерянных транзакций в очередях.

### 1.2. Хаос-Тестирование: Падение и восстановление RabbitMQ (Failover Testing)
* **GIVEN**: Шлюз FastAPI запущен, но служба RabbitMQ принудительно остановлена (симуляция падения ноды).
* **WHEN**: Поступает транзакционный вебхук на `/gateway/ton`.
* **THEN**: Шлюз возвращает статус `202 Accepted` и записывает сырой JSON транзакции в локальный SSD-лог (SQLite/RocksDB) во избежание потери данных.
* **AND WHEN** (И когда): Служба RabbitMQ запускается обратно.
* **THEN**: Фоновый демон-репликатор перечитывает локальный SSD-лог, публикует все отложенные события в очередь `ton_transactions` и очищает буферные файлы.

### 1.3. Безопасность: Предотвращение Replay-атак вебхуков (Signature Expiry)
* **GIVEN**: Вебхук с уникальным хэшем транзакции и валидной подписью провайдера был успешно обработан 10 минут назад.
* **WHEN**: Злоумышленник повторно отправляет идентичный JSON-пакет с той же подписью на `/gateway/evm`.
* **THEN**: Шлюз отклоняет запрос с ошибкой `HTTP 403 Forbidden`, определяя истечение времени жизни запроса (timestamp skew > 5 минут) или дубликат подписи.

### 1.4. Отказоустойчивость: Обработка некорректных транзакций (Poison Pill Scenario)
* **GIVEN**: Воркер-декодер слушает очередь `raw_blockchain_events`.
* **WHEN**: В очередь попадает поврежденный или некорректный JSON-пакет (например, отсутствует адрес контракта или объем сделки отрицательный).
* **THEN**: Воркер перехватывает ошибку валидации Pydantic, логирует инцидент, отклоняет сообщение без повторной отправки в очередь (`requeue=False`) с перенаправлением в Dead Letter Queue (`raw_blockchain_events.dlx`) для предотвращения зацикливания воркера.

### 1.5. Производительность: Дедупликация на уровне Redis Bloom Filter
* **GIVEN**: Redis Bloom Filter инициализирован в кэш-слое шлюза.
* **WHEN**: 10 идентичных транзакционных вебхуков отправляются одновременно на `/gateway/sol`.
* **THEN**: Bloom Filter пропускает только 1-й запрос, отправляя его в RabbitMQ, а остальные 9 запросов отсекает как дубликаты на уровне кэша, снижая нагрузку на сеть.

---

## 2. Интеграция Testcontainers-python в тестовый контур

Для запуска интеграционных тестов в изолированной среде без необходимости вручную разворачивать базы данных и брокеры, мы настраиваем `pytest` с использованием библиотеки `testcontainers`.

### 2.1. Конфигурация fixtures (`tests/conftest.py`)
```python
import pytest
import os
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMQContainer
from testcontainers.redis import RedisContainer
import asyncpg
import pika
import redis

@pytest.fixture(scope="session")
def postgres_container():
    # Используем официальный образ TimescaleDB
    with PostgresContainer("timescale/timescaledb:latest-pg15") as postgres:
        os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = postgres.get_exposed_port(5432)
        os.environ["POSTGRES_USER"] = postgres.username
        os.environ["POSTGRES_PASSWORD"] = postgres.password
        os.environ["POSTGRES_DB"] = postgres.dbname
        yield postgres

@pytest.fixture(scope="session")
def rabbitmq_container():
    with RabbitMQContainer("rabbitmq:3-management") as rabbitmq:
        os.environ["RABBITMQ_HOST"] = rabbitmq.get_container_host_ip()
        os.environ["RABBITMQ_PORT"] = rabbitmq.get_exposed_port(5672)
        yield rabbitmq

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:alpine") as redis_cont:
        os.environ["REDIS_HOST"] = redis_cont.get_container_host_ip()
        os.environ["REDIS_PORT"] = redis_cont.get_exposed_port(6379)
        yield redis_cont

@pytest.fixture(scope="session")
def init_test_db(postgres_container):
    # Логика создания схем таблиц и применения init_db.sql (гипертаблиц TimescaleDB)
    # перед запуском интеграционных тестов
    pass
```

---

## 3. Интеграция в CI/CD Pipeline (GitHub Actions)

Тесты на базе `Testcontainers` требуют наличия запущенного Docker-демона на раннере. Стандартные Ubuntu-раннеры в GitHub Actions поддерживают Docker из коробки.

### Конфигурация `.github/workflows/test.yml`
```yaml
name: Integration & Chaos Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      # Нам не нужно разворачивать Postgres/RabbitMQ как сервисы GitHub Actions,
      # так как Testcontainers запустит их внутри Docker самостоятельно.
      # Но сам Docker-демон должен быть активен на хосте.

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio testcontainers

    - name: Run Pytest Suite with Testcontainers
      run: |
        PYTHONPATH=. pytest -v
      env:
        # Указываем тестовые переменные окружения
        API_SECRET_KEY: "ci_test_secret_key"
        ENV: "testing"
```

---

## 4. Метрики Качества и Ворота Доверия (Quality Gates)

Перед тем как код будет допущен в ветку `main`, он должен пройти следующие проверки:
1. **Покрытие тестами (Coverage):** Общее покрытие бизнес-логики (парсеры, шлюз, валидаторы) должно быть не менее **85%**.
2. **Сценарии сбоев:** Интеграционные тесты сбоев RabbitMQ/Redis (Chaos Scenarios) должны проходить на 100%.
3. **Безопасность:** Отсутствие уязвимостей в зависимостях (проверка через `safety check` или `pip-audit`).
