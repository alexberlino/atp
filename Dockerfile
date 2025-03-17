FROM ubuntu:latest

# Install dependencies
RUN apt-get update --fix-missing && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    wget \
    curl \
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

# Install Chrome from "Chrome for Testing"
RUN wget -q -O /tmp/chrome-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/134.0.6325.0/linux64/chrome-linux64.zip && \
    unzip /tmp/chrome-linux64.zip -d /usr/local/bin/ && \
    rm /tmp/chrome-linux64.zip && \
    chmod +x /usr/local/bin/chrome-linux64/chrome

# Install ChromeDriver that matches the Chrome version
RUN wget -q -O /tmp/chromedriver-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/134.0.6325.0/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver-linux64.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver-linux64.zip && \
    chmod +x /usr/local/bin/chromedriver-linux64/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set start command
CMD ["xvfb-run", "-a", "python3", "ranking_railway.py"]