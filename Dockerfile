FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip && pip install .
EXPOSE 3001
CMD ["uvicorn", "hpd_cli.api.main:app", "--host", "0.0.0.0", "--port", "3001", "--reload"]
