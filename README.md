# 🚀 KuriBot

Modern, fast, and asynchronous Telegram **KuriBot** built with **Kurigram**.

## ✨ Features
- **Fast:** Powered by Kurigram and TgCrypto.
- **Dockerized:** Easy deployment with Docker Compose.
- **Modular:** Simple module system for adding new features.
- **Interactive:** Terminal-based login session.

## 🛠 Setup

1. **Variables:**
   - Copy `.env.example` to `.env`.
   - Get your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org/apps).
   - Paste them into `.env`.

2. **Run with Docker:**
   ```bash
   docker-compose run kuribot
   ```
   *Note: Use `run` instead of `up` for the first time to handle the interactive terminal login.*

3. **Login:**
   - Follow the prompts in your terminal: enter your phone number and the verification code from Telegram.
   - Once logged in, your session will be saved in `kuribot.session`.

4. **Background Run:**
   After the first successful login, you can run it in the background:
   ```bash
   docker-compose up -d
   ```

## 📜 Commands
The default prefix is `.`
- `.ping` - Check latency.
- `.help` - Show help menu.
- `.whois` - Get information about a user.
- `.purge` - Delete messages in bulk.
- `.del` - Delete a specific message.
- `.eval` - Execute Python code.

## 📂 Structure
- `main.py`: Entry point.
- `core/`: Client initialization.
- `modules/`: Command handlers.
- `Dockerfile`: Deployment instructions.
