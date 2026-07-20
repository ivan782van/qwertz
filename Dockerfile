FROM registry.access.redhat.com/ubi9/python-312-minimal:9.8-1784139779
COPY certs/company-ca.crt /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chmod=775 app app
COPY --chmod=775 config config
COPY --chmod=775 inventory inventory

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
