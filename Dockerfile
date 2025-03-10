FROM ubuntu:latest

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    xvfb \
    curl \
    python3 \
    python3-pip

# Add Google Chrome repository and install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    if [ -z "$CHROME_VERSION" ]; then \
    echo "Error: Could not determine Chrome version." && exit 8; \
    fi && \
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") && \
    if [ -z "$CHROMEDRIVER_VERSION" ]; then \
    echo "Error: Could not retrieve ChromeDriver version." && exit 8; \
    fi && \
    wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" && \
    if [ ! -f /tmp/chromedriver.zip ]; then \
    echo "Error: Failed to download ChromeDriver." && exit 8; \
    fi && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    if [ ! -f /usr/local/bin/chromedriver ]; then \
    echo "Error: Failed to unzip ChromeDriver." && exit 8; \
    fi && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set start command
CMD ["xvfb-run", "-a", "python3", "ranking.py"]