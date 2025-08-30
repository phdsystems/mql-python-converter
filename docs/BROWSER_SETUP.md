# Browser Installation and Configuration Guide

## Table of Contents
1. [Overview](#overview)
2. [Browser Options](#browser-options)
3. [Installation Instructions](#installation-instructions)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Headless Browser Setup](#headless-browser-setup)
7. [Browser Automation](#browser-automation)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)

## Overview

This guide covers installing and configuring various web browsers in Linux environments, particularly for Docker containers and headless servers. Browsers are essential for accessing web-based interfaces, testing web applications, and automation tasks.

### Use Cases
- Accessing NoVNC web interfaces
- Web application testing
- Screenshot generation
- Web scraping and automation
- Accessing trading platforms web interfaces
- Development and debugging

## Browser Options

### GUI Browsers

| Browser | Type | Resource Usage | Best For | Package Size |
|---------|------|---------------|----------|--------------|
| **Google Chrome** | Full GUI | High | Full features, development | ~400MB |
| **Firefox** | Full GUI | Medium-High | Privacy, extensions | ~350MB |
| **Chromium** | Full GUI | Medium-High | Open-source Chrome | ~380MB |
| **Firefox ESR** | Full GUI | Medium | Stability, enterprise | ~340MB |

### Text-Based Browsers

| Browser | Type | Resource Usage | Best For | Package Size |
|---------|------|---------------|----------|--------------|
| **Lynx** | Text-only | Very Low | Quick access, scripts | ~2MB |
| **W3M** | Text+Images | Low | Terminal browsing | ~3MB |
| **Links2** | Text+Graphics | Low | Lightweight GUI | ~5MB |
| **ELinks** | Text-only | Very Low | Advanced features | ~2MB |

### Headless Browsers

| Browser | Type | Resource Usage | Best For | Package Size |
|---------|------|---------------|----------|--------------|
| **Headless Chrome** | Headless | Medium | Automation, testing | ~400MB |
| **Headless Firefox** | Headless | Medium | Automation, testing | ~350MB |
| **PhantomJS** | Headless | Low | Legacy automation | ~50MB |
| **Puppeteer** | Chrome API | Medium | Node.js automation | ~170MB |

## Installation Instructions

### Prerequisites

```bash
# Update package lists
sudo apt update

# Install basic dependencies
sudo apt install -y \
    wget \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    software-properties-common
```

### Google Chrome

#### Method 1: Direct Installation
```bash
# Add Google's signing key
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# Add Chrome repository
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | \
    sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update and install
sudo apt update
sudo apt install -y google-chrome-stable

# Verify installation
google-chrome --version
```

#### Method 2: Manual Download
```bash
# Download latest stable version
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Install package
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Fix dependencies if needed
sudo apt-get install -f -y
```

### Firefox

#### Standard Firefox
```bash
# Install from repository
sudo apt install -y firefox

# Or use snap (if available)
sudo snap install firefox

# Verify installation
firefox --version
```

#### Firefox ESR (Extended Support Release)
```bash
# Add Mozilla repository
sudo add-apt-repository ppa:mozillateam/ppa

# Update and install
sudo apt update
sudo apt install -y firefox-esr

# Verify installation
firefox-esr --version
```

### Chromium

```bash
# Install from repository
sudo apt install -y chromium-browser

# Or use snap
sudo snap install chromium

# Verify installation
chromium-browser --version
```

### Text-Based Browsers

```bash
# Install all text browsers
sudo apt install -y lynx w3m links2 elinks

# Individual installations
sudo apt install -y lynx      # Most basic
sudo apt install -y w3m        # Supports images in terminal
sudo apt install -y links2     # Graphical mode available
sudo apt install -y elinks     # Advanced features

# Verify installations
lynx --version
w3m -version
links2 -version
elinks -version
```

## Configuration

### Chrome/Chromium Configuration

#### Command-Line Flags
```bash
# Basic flags for containers/headless
google-chrome \
    --no-sandbox \              # Required in Docker
    --disable-dev-shm-usage \   # Overcome limited shared memory
    --disable-gpu \             # Disable GPU hardware acceleration
    --disable-software-rasterizer \
    --disable-extensions \      # Disable extensions
    --disable-web-security \    # Disable CORS (development only)
    --user-data-dir=/tmp/chrome-profile \  # Custom profile location
    --window-size=1920,1080 \   # Set window size
    --start-maximized           # Start maximized
```

#### Preferences File
```json
// ~/.config/google-chrome/Default/Preferences
{
  "download": {
    "default_directory": "/home/user/downloads",
    "prompt_for_download": false
  },
  "plugins": {
    "always_open_pdf_externally": true
  },
  "profile": {
    "default_content_settings": {
      "popups": 0
    }
  }
}
```

### Firefox Configuration

#### Profile Management
```bash
# Create new profile
firefox -CreateProfile "automation /home/user/.mozilla/firefox/automation"

# Use specific profile
firefox -P automation

# Run with preferences
firefox \
    -width 1920 \
    -height 1080 \
    -private \              # Private browsing
    -safe-mode \            # Safe mode
    -no-remote              # New instance
```

#### User Preferences (user.js)
```javascript
// ~/.mozilla/firefox/profile/user.js
user_pref("browser.download.folderList", 2);
user_pref("browser.download.dir", "/home/user/downloads");
user_pref("browser.helperApps.neverAsk.saveToDisk", "application/pdf");
user_pref("pdfjs.disabled", true);
user_pref("browser.tabs.remote.autostart", false);
```

### Text Browser Configuration

#### Lynx Configuration
```bash
# ~/.lynxrc or /etc/lynx/lynx.cfg
accept_all_cookies:TRUE
cookie_file:~/.lynx_cookies
default_editor:/usr/bin/vim
file_sorting_method:BY_TYPE
user_mode:ADVANCED
vi_keys:TRUE
```

#### W3M Configuration
```bash
# ~/.w3m/config
accept_language en
color 1
confirm_qq no
cookie_accept_domains .google.com,.github.com
display_image 1
editor /usr/bin/vim
use_mouse 1
```

## Usage Examples

### GUI Browser Examples

#### Chrome - Accessing NoVNC
```bash
# Basic usage
google-chrome http://localhost:8080/vnc.html

# With virtual display
DISPLAY=:99 google-chrome http://localhost:8080/vnc.html

# In Docker container
google-chrome --no-sandbox --disable-dev-shm-usage http://localhost:8080/vnc.html
```

#### Firefox - Development Mode
```bash
# Open with developer tools
firefox -devtools http://localhost:8080

# Multiple tabs
firefox -new-tab http://localhost:8080 -new-tab http://localhost:3000

# Screenshot mode
firefox --screenshot output.png http://localhost:8080
```

### Text Browser Examples

#### Lynx - Quick Access
```bash
# View webpage
lynx http://localhost:8080

# Dump page content
lynx -dump http://localhost:8080 > page.txt

# Accept cookies automatically
lynx -accept_all_cookies http://localhost:8080
```

#### W3M - Terminal Browsing
```bash
# Browse with images (if supported)
w3m http://localhost:8080

# Save page as HTML
w3m -dump_source http://localhost:8080 > page.html

# Tabbed browsing
w3m -N http://localhost:8080  # Opens in new tab
```

#### Links2 - Graphical Mode
```bash
# Text mode
links2 http://localhost:8080

# Graphical mode (requires X11)
links2 -g http://localhost:8080

# Download file
links2 -download http://example.com/file.pdf
```

## Headless Browser Setup

### Headless Chrome

```bash
# Basic headless mode
google-chrome --headless --disable-gpu --dump-dom http://localhost:8080

# Take screenshot
google-chrome --headless --disable-gpu \
    --screenshot=screenshot.png \
    --window-size=1920,1080 \
    http://localhost:8080

# Generate PDF
google-chrome --headless --disable-gpu \
    --print-to-pdf=output.pdf \
    http://localhost:8080

# With debugging port
google-chrome --headless --disable-gpu \
    --remote-debugging-port=9222 \
    http://localhost:8080
```

### Headless Firefox

```bash
# Basic headless mode
firefox --headless http://localhost:8080

# Take screenshot
firefox --headless --screenshot=output.png http://localhost:8080

# Set window size
firefox --headless --window-size=1920,1080 http://localhost:8080

# With debugging
firefox --headless --start-debugger-server 6000 http://localhost:8080
```

### Xvfb (Virtual Display)

```bash
# Install Xvfb
sudo apt install -y xvfb

# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Run browser with virtual display
google-chrome http://localhost:8080

# Using xvfb-run wrapper
xvfb-run -a -s "-screen 0 1920x1080x24" google-chrome http://localhost:8080
```

## Browser Automation

### Using Selenium

```python
# install: pip install selenium webdriver-manager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

# Initialize driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate and interact
driver.get("http://localhost:8080/vnc.html")
driver.save_screenshot("screenshot.png")
driver.quit()
```

### Using Puppeteer (Node.js)

```javascript
// install: npm install puppeteer

const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto('http://localhost:8080/vnc.html');
  await page.screenshot({ path: 'screenshot.png' });
  await browser.close();
})();
```

### Using Playwright

```python
# install: pip install playwright
# playwright install chromium

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    page = browser.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto("http://localhost:8080/vnc.html")
    page.screenshot(path="screenshot.png")
    browser.close()
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Chrome Crashes in Docker
```bash
# Problem: Chrome crashes with "Failed to move to new namespace"
# Solution: Add required flags
google-chrome \
    --no-sandbox \
    --disable-setuid-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --single-process  # For very limited environments
```

#### 2. Shared Memory Issues
```bash
# Problem: "FATAL:memory.cc Out of memory"
# Solution 1: Increase Docker shared memory
docker run --shm-size=2g your-image

# Solution 2: Use disk for shared memory
google-chrome --disable-dev-shm-usage

# Solution 3: Mount tmpfs
docker run -v /dev/shm:/dev/shm your-image
```

#### 3. Display Not Found
```bash
# Problem: "Cannot open display"
# Solution: Set up virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &

# Or use xvfb-run
xvfb-run -a google-chrome http://localhost:8080
```

#### 4. Font Issues
```bash
# Problem: Missing or broken fonts
# Solution: Install font packages
sudo apt install -y \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst
```

#### 5. SSL Certificate Errors
```bash
# Problem: SSL certificate verification failed
# Solution 1: Ignore certificate errors (development only)
google-chrome --ignore-certificate-errors

# Solution 2: Add certificate to system
sudo cp certificate.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### Debug Mode

```bash
# Enable Chrome logging
google-chrome \
    --enable-logging \
    --v=1 \
    --dump-dom \
    http://localhost:8080 2>&1 | tee chrome.log

# Firefox verbose mode
firefox -jsconsole -purgecaches http://localhost:8080

# Check browser processes
ps aux | grep -E "(chrome|firefox|chromium)"

# Check network connectivity
curl -I http://localhost:8080
netstat -tulpn | grep 8080
```

## Performance Optimization

### Memory Optimization

```bash
# Limit Chrome memory usage
google-chrome \
    --max_old_space_size=512 \
    --memory-pressure-off \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    --disable-backgrounding-occluded-windows

# Firefox memory settings
# about:config
# browser.cache.memory.capacity: 65536
# browser.sessionhistory.max_entries: 10
```

### CPU Optimization

```bash
# Disable unnecessary Chrome features
google-chrome \
    --disable-features=TranslateUI \
    --disable-features=BlinkGenPropertyTrees \
    --disable-background-networking \
    --disable-sync \
    --disable-translate \
    --metrics-recording-only

# Limit process count
google-chrome --renderer-process-limit=2
```

### Disk I/O Optimization

```bash
# Use memory for cache
google-chrome --disk-cache-dir=/dev/null --disk-cache-size=1

# Firefox RAM cache
# about:config
# browser.cache.disk.enable: false
# browser.cache.memory.enable: true
```

### Network Optimization

```bash
# Disable prefetching
google-chrome \
    --disable-background-networking \
    --disable-default-apps \
    --disable-sync \
    --disable-translate

# Use proxy
google-chrome --proxy-server="http://proxy:8080"
```

## Docker Integration

### Dockerfile Example

```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/LATEST_RELEASE/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Set display
ENV DISPLAY=:99

# Start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  browser:
    image: selenium/standalone-chrome:latest
    ports:
      - "4444:4444"
      - "7900:7900"
    shm_size: 2g
    environment:
      - SE_NODE_MAX_SESSIONS=5
      - SE_NODE_SESSION_TIMEOUT=300
      - SE_VNC_PASSWORD=secret
    volumes:
      - /dev/shm:/dev/shm
```

## Security Considerations

### Sandboxing

```bash
# Run with limited privileges
google-chrome \
    --no-sandbox \  # Required in Docker
    --disable-setuid-sandbox \
    --disable-gpu-sandbox

# Use AppArmor profile
sudo aa-enforce /etc/apparmor.d/usr.bin.chromium-browser
```

### Privacy Settings

```bash
# Privacy-focused Chrome flags
google-chrome \
    --incognito \
    --disable-background-networking \
    --disable-web-resources \
    --disable-client-side-phishing-detection \
    --disable-sync \
    --disable-translate \
    --disable-features=ChromeWhatsNewUI \
    --disable-extensions \
    --no-first-run \
    --no-default-browser-check
```

### Content Security

```bash
# Block dangerous content
google-chrome \
    --disable-plugins \
    --disable-java \
    --disable-flash \
    --disable-images \  # Text only
    --disable-javascript  # No JS execution
```

## Conclusion

Browser installation and configuration in Linux environments requires careful consideration of use case, resources, and security requirements. This guide provides comprehensive coverage of various browser options and their configurations for different scenarios.

### Quick Start Commands

```bash
# Install browsers
sudo apt install -y google-chrome-stable firefox lynx w3m

# Test GUI browser with virtual display
xvfb-run -a google-chrome --no-sandbox http://localhost:8080

# Test text browser
lynx http://localhost:8080

# Take screenshot
google-chrome --headless --screenshot=test.png http://localhost:8080
```

### Additional Resources
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Firefox Command Line Options](https://developer.mozilla.org/en-US/docs/Mozilla/Command_Line_Options)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Puppeteer Documentation](https://pptr.dev/)
- [Playwright Documentation](https://playwright.dev/)