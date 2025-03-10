# Use an official Python image as the base
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy all files from the current directory to the container
COPY . /app

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command to run your script
CMD ["python", "your_script.py"]

RUN sudo apt-get update && \
    sudo apt-get install -y --no-install-recommends wget gnupg && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add - && \
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    sudo apt-get update && \
    sudo apt-get install -y --no-install-recommends \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    xvfb \
    google-chrome-stable && \
    sudo apt-get clean && \
    sudo rm -rf /var/lib/apt/lists/*