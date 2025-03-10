# Use an official Python image as the base
FROM python:3.9

# Set the working directory
WORKDIR /app

# Install system dependencies for Chrome and ChromeDriver
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gnupg curl unzip && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    xvfb \
    google-chrome-stable && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver matching the installed Chrome version
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") && \
    wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Copy all files from the current directory to the container
COPY . /app

# Install required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command to run your script
CMD ["python", "your_script.py"]
