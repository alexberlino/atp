FROM ubuntu:latest

# Install system dependencies
RUN apt-get update --fix-missing && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    fonts-liberation \
    xvfb \
    python3 \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN apt-get update && \
    apt-get install -y wget curl && \
    wget -q -O /usr/share/keyrings/google-chrome-keyring.gpg https://dl.google.com/linux/linux_signing_key.pub && \
    echo "deb [signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] https://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver (auto-matching Chrome version)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) && \
    echo "Detected Chrome version: $CHROME_VERSION (Major: $CHROME_MAJOR_VERSION)" && \
    CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    wget -q -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set start command
CMD ["xvfb-run", "-a", "python3", "ranking_railway.py"]
