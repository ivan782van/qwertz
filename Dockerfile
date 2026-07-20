FROM registry.redhat.io/ubi9/python-311:latest
COPY certs/company-ca.crt /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chmod=775 app app
COPY --chmod=775 config config
COPY --chmod=775 inventory inventory

CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]