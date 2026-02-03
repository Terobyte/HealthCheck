# HealthCheck - System Monitoring Application

A modern cross-platform system monitoring application with AI-powered diagnostics, built with Flet framework.

## Features

- 🖥️ **System Health Monitoring**: Real-time CPU, RAM, and disk usage tracking
- 🌐 **Network Analysis**: Network interface detection, gateway status, and speed testing
- 🤖 **AI-Powered Diagnostics**: Google Gemini AI analyzes system health and provides recommendations
- 📱 **Telegram Integration**: Automatic report delivery to your Telegram bot
- 💾 **Offline Support**: Saves reports locally when internet is unavailable
- ✨ **Modern Glassmorphism UI**: Beautiful glass-effect design with blue tint
- 🔄 **Cross-Platform**: Works on Windows and macOS

## Screenshots

The application features:
- Glassmorphism design with 90% opacity and blue tint overlay
- Rounded corners (20px border radius)
- Animated status messages during scanning
- Clean, modern interface with "Health Check" title
- "Run diagnostics" button to trigger system analysis

## Requirements

- Python 3.8 or higher
- Windows 10/11 or macOS 10.15+

## Installation

### 1. Clone or Download the Project

```bash
cd HealthCheck
```

### 2. Create Virtual Environment (Recommended)

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file in the project root directory (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` file and add your API keys:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Getting API Keys

**Telegram Bot Token:**
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token

**Telegram Chat ID:**
1. Send a message to your bot
2. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your `chat_id` in the response

**Gemini API Key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key

## Usage

### Running the Application

```bash
python main.py
```

The application window will open with:
- "Health Check" title displayed prominently
- "Run diagnostics" button to start system analysis
- Status area showing scanning progress
- Output area displaying diagnostic results

### How It Works

1. Click "Run diagnostics" button
2. Application collects system data:
   - System information (hostname, OS, uptime)
   - Disk usage (total, used, percentage)
   - RAM usage (total, used, percentage)
   - Network status (IP, interface, gateway)
   - Public IP and location (if online)
   - Internet speed test (if online)
3. If online:
   - Sends data to Google Gemini AI for analysis
   - Receives English-language recommendations
   - Sends report to Telegram bot with AI analysis
4. If offline:
   - Saves report to desktop as text file

## 📥 Download Windows Executable

Pre-built Windows executables are available on the [Releases page](../../releases).

### Build from Source

If you want to build the executable yourself:

1. Install PyInstaller: `pip install pyinstaller`
2. Run: `pyinstaller --onefile --windowed --name HealthCheck main.py`
3. Find the executable in `dist/HealthCheck.exe`

### GitHub Actions Build

The project uses GitHub Actions to automatically build Windows executables on each release:
- Push a tag: `git tag v1.0.0 && git push --tags`
- GitHub Actions will build and create a release with the executable
- Download `HealthCheck-Windows.zip` from the release

### Manual Build with PyInstaller

```bash
# Single file executable (recommended)
pyinstaller --onefile --windowed --name HealthCheck main.py

# Or use the spec file
pyinstaller HealthCheck.spec
```

## Project Structure

```
HealthCheck/
├── main.py                 # Main Flet application entry point
├── monitor_sys.py          # System monitoring logic
├── network_sender.py       # AI and Telegram integration
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Dependencies

- `flet>=0.21.0` - Modern GUI framework
- `psutil>=5.9.0` - System monitoring
- `requests>=2.31.0` - HTTP requests
- `google-genai>=0.3.0` - Google Gemini AI SDK
- `python-dotenv>=1.0.0` - Environment variable management

## Troubleshooting

### Application Won't Start

**Problem:** Import errors or missing dependencies
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Telegram Not Receiving Messages

**Problem:** Incorrect API keys
- Verify `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` file
- Ensure bot has permission to send messages to you
- Try sending a message to your bot first to activate the chat

### Gemini API Errors

**Problem:** API key issues or quota exceeded
- Verify `GEMINI_API_KEY` is correct in `.env` file
- Check if API key has available quota
- Ensure API key is enabled for Gemini API

### Network Speed Test Fails

**Problem:** Cloudflare blocking or network issues
- The app automatically tries a backup server if Cloudflare fails
- Check your internet connection
- Firewall may be blocking the requests

### Disk Permission Issues (Windows)

**Problem:** Cannot access disk information
- Run application as Administrator
- Check Windows Firewall settings
- Ensure antivirus software isn't blocking the application

### Glass Effect Not Working

**Problem:** UI appears plain
- Glass effect is simulated using opacity and shadows
- Some platforms may not render transparency perfectly
- Try updating Flet: `pip install --upgrade flet`

## Development

### Code Structure

- **main.py**: Flet GUI implementation with glassmorphism design
- **monitor_sys.py**: System monitoring functions (CPU, RAM, disk, network)
- **network_sender.py**: AI integration and Telegram bot communication

### Key Features Implementation

**Glassmorphism Design:**
- Semi-transparent background (90% opacity)
- Blue tint overlay (5% blue)
- Rounded corners (20px border radius)
- Shadow effects for depth

**Threading:**
- Non-blocking UI during diagnostics
- Animated status messages
- Separate thread for network operations

**Cross-Platform:**
- Windows: Uses `C://` for disk, `ipconfig` for network
- macOS: Uses `/` or `/System/Volumes/Data` for disk, `route` for network
- Automatic platform detection

## Migration from Tkinter

This project has been migrated from Tkinter to Flet with:
- Modern glassmorphism design
- Full English localization (comments, UI, AI prompts, responses)
- Cross-platform Windows support
- Improved threading and performance

The old `main_gui.py` (Tkinter version) is kept for reference.

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions:
1. Check the Troubleshooting section above
2. Verify all API keys are correctly configured
3. Ensure all dependencies are installed
4. Check Python version (3.8+ required)

## Acknowledgments

- **Flet** - Modern Python GUI framework
- **Google Gemini AI** - AI-powered system analysis
- **Telegram** - Bot API for report delivery
- **psutil** - System monitoring library