FROM mysuni-registry.mysuni.cloudzcp.net/mysuni-carr-prd/career-playwright:base-1

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER appuser

COPY . .

# Set entrypoint
ENV BROWSER_HEADLESS=true
ENTRYPOINT ["python", "main.py"]