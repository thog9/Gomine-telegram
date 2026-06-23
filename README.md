# GoMine Social Bot Scripts 🚀

This collection of Python scripts automates task completion on the GoMine Social platform — a Telegram-based Web3 mining ecosystem where users earn points by completing daily check-ins, watching ads, connecting Twitter/X accounts, and linking TON wallets.

🔗 **Website**: [GoMine Social](https://t.me/GoMineAppBot/app?startapp=ref_921415493)

---

## ✨ Features Overview

### General Features

- **Multi-Account Support**: Reads Telegram init_data from `accounts.txt` to process multiple accounts in parallel.
- **Central Menu System**: Interactive menu for easy script selection via `main.py`.
- **Colorful CLI**: Uses `colorama` for visually appealing output with box-drawing borders and colored icons.
- **Asynchronous Execution**: Built with `asyncio` for efficient concurrent task processing.
- **Error Handling**: Comprehensive error catching with retry logic for API failures.
- **Bilingual Support**: Supports both English and Vietnamese output.
- **Proxy Support**: Supports SOCKS5 proxies via `proxies.txt`.

---

### Included Scripts

✨ **Daily Check-In** (`checkin.py`)

- ✅ Automatic daily check-in with streak tracking
- ✅ Points balance display (before/after)
- ✅ Multi-account parallel execution
- ✅ Proxy support

✨ **Ad Boosting** (`boost.py`)

- ✅ Auto-watch rewarded ads for bonus points
- ✅ Impression tracking & resolve polling (e8ys.com)
- ✅ Smart retry with configurable delays
- ✅ Multi-account support

✨ **Connect Twitter** (`connectX.py`)

- ✅ X (Twitter) account linking via OAuth2 PKCE
- ✅ Automated browser-based auth flow
- ✅ Session validation
- ✅ Proxy support

✨ **Connect Wallet** (`connect_wallet.py`)

- ✅ TON wallet connection via Ton Connect protocol
- ✅ Uses Telegram Web App (TGA) events for client_id/wallet_id
- ✅ Signature verification
- ✅ Proxy support

---

## 🛠️ Prerequisites

Before running the scripts, ensure you have the following installed:

- **Python 3.8+**
- **pip** (Python package manager)
- **Dependencies**: Install via `pip install -r requirements.txt`
- **accounts.txt**: Add Telegram init_data (one per line)
- **proxies.txt** (optional): Add SOCKS5 proxy addresses

---

## 📦 Installation

1. **Clone or download this repository:**
   ```sh
   git clone https://github.com/thog9/Gomine-telegram.git
   cd Gomine-telegram
   ```

2. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Prepare Input Files:**

   Create `accounts.txt` in the root directory with Telegram init_data (one per line):
   ```
   query_id=AAE5...
   user=%7B%22id%22%3A...
   ```

   Create `proxies.txt` (optional) — one proxy per line:
   ```
   socks5://user:pass@ip:port
   ```

4. **Run:**
   ```sh
   python main.py
   ```
   - Choose a language (Vietnamese / English).
   - Select the script you want to run.

**Language Selection:**
- Choose between Vietnamese (Tiếng Việt) and English.
- All scripts support bilingual output.

---

## 📁 Project Structure

```
Gomine-telegram/
├── main.py                 # Central menu system
├── accounts.txt            # Telegram init_data
├── proxies.txt             # SOCKS5 proxies (optional)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── bot.py                  # Bot description
└── scripts/                # Individual scripts
    ├── checkin.py          # Daily check-in
    ├── boost.py            # Ad boosting
    ├── connectX.py         # Twitter OAuth connection
    └── connect_wallet.py   # TON wallet connection

```

---

## 📨 Contact

Connect with us for support or updates:

- **Telegram**: [thog099](https://t.me/thog099)
- **Channel**: [CHANNEL](https://t.me/thogairdrops)
- **Group**: [GROUP CHAT](https://t.me/thogchats)
- **X**: [Thog](https://x.com/thog099)

---

## ☕ Support Us

Love these scripts? Fuel our work with a coffee!

🔗 BUYMECAFE: [BUY ME CAFE](https://buymecafe.vercel.app/)

🔗 WEBSITE: [BUY SCRIPTS](https://thogtoolhub.com/)
