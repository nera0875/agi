FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in logical groups to reduce memory pressure
# and improve layer caching.
RUN pip install --no-cache-dir --upgrade pip

# Group 1: Core Framework
RUN pip install --no-cache-dir "fastapi==0.109.0" "uvicorn[standard]==0.27.0" "python-multipart==0.0.6"

# Group 2: Database & Redis
RUN pip install --no-cache-dir "asyncpg==0.29.0" "psycopg2-binary==2.9.9" "pgvector==0.2.4" "sqlalchemy==2.0.25" "alembic==1.13.1" "redis==5.0.1"

# Group 3: LangChain Ecosystem (Granular Install)
RUN pip install --no-cache-dir "langchain-core==0.1.16"
RUN pip install --no-cache-dir "langchain-community==0.0.17"
RUN pip install --no-cache-dir "langsmith==0.0.83"
RUN pip install --no-cache-dir "langgraph==0.0.20"
RUN pip install --no-cache-dir "langchain==0.1.4"
RUN pip install --no-cache-dir "langchain-anthropic==0.1.1" "langchain-cohere==0.1.0" "langchain-voyageai==0.1.0" "langchain-postgres==0.0.7"

# Group 4: Heavy ML/Vector Libraries (Granular Install)
RUN pip install --no-cache-dir "numpy==1.24.3"
RUN pip install --no-cache-dir "scikit-learn==1.4.0"
RUN pip install --no-cache-dir "cohere==4.47" "voyageai==0.2.1"
RUN pip install --no-cache-dir "faiss-cpu==1.7.4"
RUN pip install --no-cache-dir "sentence-transformers==2.3.1"

# Group 5: Other Tools & Utilities
RUN pip install --no-cache-dir "strawberry-graphql[fastapi]==0.219.1" "sentry-sdk[fastapi]==1.39.2" "prometheus-client==0.19.0" "pydantic==2.5.3" "pydantic-settings==2.1.0" "python-dotenv==1.0.0" "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" "tenacity==8.2.3" "httpx==0.26.0" "pyjwt==2.8.1"

# Group 6: Testing
RUN pip install --no-cache-dir "pytest==7.4.4" "pytest-asyncio==0.23.3" "pytest-cov==4.1.0"

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p .cache && chmod 777 .cache

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
