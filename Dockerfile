FROM ubuntu:latest

# Install system dependencies
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

# Install Chrome for Testing (version 134.0.6998.0)
RUN wget -q -O /tmp/chrome-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.0/linux64/chrome-linux64.zip && \
    unzip /tmp/chrome-linux64.zip -d /tmp && \
    rm /tmp/chrome-linux64.zip && \
    mv /tmp/chrome-linux64/chrome /usr/local/bin/chrome && \
    chmod +x /usr/local/bin/chrome

# Install ChromeDriver for Testing (version 134.0.6998.0)
RUN wget -q -O /tmp/chromedriver-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.0/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver-linux64.zip -d /tmp && \
    rm /tmp/chromedriver-linux64.zip && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set start command (using your Railway-optimized script)
CMD ["xvfb-run", "-a", "python3", "ranking_railway.py"]
