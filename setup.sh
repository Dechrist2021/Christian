#!/bin/bash
# Install Chrome and Chromedriver for Streamlit Cloud
sudo apt-get update -qq
sudo apt-get install -yqq \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    chromium-chromedriver

# Install Google Chrome (latest stable)
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -yqq ./google-chrome-stable_current_amd64.deb
rm -f google-chrome-stable_current_amd64.deb  # Clean up

# Verify installations
google-chrome --version
chromedriver --version
