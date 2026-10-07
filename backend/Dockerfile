FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt ./
ARG HARDWARE_IBM=false
ARG HARDWARE_BRAKET=false
RUN pip install --no-cache-dir -r requirements.txt
RUN if [ "$HARDWARE_IBM" = "true" ]; then pip install --no-cache-dir -r requirements-hardware-ibm.txt; fi
RUN if [ "$HARDWARE_BRAKET" = "true" ]; then pip install --no-cache-dir -r requirements-hardware-braket.txt; fi
COPY app ./app
COPY migrations ./migrations
COPY data ./data
RUN useradd --create-home iqlrs && mkdir -p /app/.cache && chown -R iqlrs:iqlrs /app
USER iqlrs
EXPOSE 8000
CMD ["sh", "-c", "python -m app.migrate && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log"]
