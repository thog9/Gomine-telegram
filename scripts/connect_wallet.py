import os, sys, asyncio, aiohttp, json, re, urllib.parse
from typing import List, Optional, Dict
from aiohttp_socks import ProxyConnector
from colorama import init, Fore, Style

init(autoreset=True)

BORDER_WIDTH = 80
API_BASE = "https://app.gomine.social"
TGA_AUTH_TOKEN = "eyJhcHBfbmFtZSI6ImdvbWluZSIsImFwcF91cmwiOiJodHRwczovL3QubWUvR29NaW5lQXBwQm90IiwiYXBwX2RvbWFpbiI6Imh0dHBzOi8vYXBwLmdvbWluZS5zb2NpYWwifQ==!Ue5lTHOWBCnM2pyjQH5rO5J+vNjR6DRJh7ajxcnPnE4="

CONFIG = {"RETRY_ATTEMPTS": 3, "RETRY_DELAY": 2, "TIMEOUT": 60, "MAX_CONCURRENT": 10}

LANG = {
    'vi': {
        'title': 'GOMINE SOCIAL - WALLET BOT',
        'found_accounts': 'Tìm thấy {count} tài khoản',
        'found_wallets': 'Tìm thấy {count} địa chỉ ví',
        'found_proxies': 'Tìm thấy {count} proxy',
        'no_proxies': 'Không có proxy, chạy trực tiếp',
        'no_accounts': 'Không tìm thấy accounts.txt',
        'no_wallets': 'Không tìm thấy address-ton.txt',
        'mismatch': 'Số lượng tài khoản ({a}) khác số lượng ví ({w})',
        'processing': 'ĐANG KẾT NỐI VÍ CHO {count} TÀI KHOẢN',
        'completed': 'HOÀN THÀNH: {ok}/{total} TÀI KHOẢN',
        'proxy_line': 'Proxy: [{proxy}] | IP: [{ip}]',
        'account_label': 'Tài khoản {i}: @{u}',
        'wallet_label': 'Ví: {w}',
        'init_user': 'Đang khởi tạo người dùng...',
        'init_ok': 'Khởi tạo thành công! ID: {id} | Tier: {tier}',
        'init_fail': 'Khởi tạo thất bại',
        'connecting_wallet': 'Đang kết nối ví...',
        'wallet_ok': 'Kết nối ví thành công!',
        'wallet_fail': 'Kết nối ví thất bại',
        'wallet_exists': 'Ví đã tồn tại: {w}',
        'fetching_me': 'Đang lấy thông tin tài khoản...',
        'me_ok': 'Lấy thông tin thành công',
        'me_fail': 'Lấy thông tin thất bại',
        'withdraw_quote': 'Phí rút: {fee} | Lần đầu: {first} | Min rút: {min}',
        'fetching_quote': 'Đang lấy thông tin rút tiền...',
        'summary_header': 'Tóm tắt:',
        'summary_user': 'User:       {v}',
        'summary_points': 'Points:     {v}',
        'summary_sparks': 'Sparks:     {v}',
        'summary_wallet': 'Wallet:     {v}',
        'summary_twitter': 'Twitter:    {v}',
        'success_line': 'Thành công | @{u} -> {w}',
        'err_runtime': 'Lỗi: {e}',
        'retry': 'Retry {cur}/{max}...',
    },
    'en': {
        'title': 'GOMINE SOCIAL - WALLET BOT',
        'found_accounts': 'Found {count} accounts',
        'found_wallets': 'Found {count} wallet addresses',
        'found_proxies': 'Found {count} proxies',
        'no_proxies': 'No proxies, running direct',
        'no_accounts': 'accounts.txt not found',
        'no_wallets': 'address-ton.txt not found',
        'mismatch': 'Account count ({a}) != wallet count ({w})',
        'processing': 'CONNECTING WALLETS FOR {count} ACCOUNTS',
        'completed': 'COMPLETED: {ok}/{total} ACCOUNTS',
        'proxy_line': 'Proxy: [{proxy}] | IP: [{ip}]',
        'account_label': 'Account {i}: @{u}',
        'wallet_label': 'Wallet: {w}',
        'init_user': 'Initializing user...',
        'init_ok': 'Initialized! ID: {id} | Tier: {tier}',
        'init_fail': 'Init failed',
        'connecting_wallet': 'Connecting wallet...',
        'wallet_ok': 'Wallet connected!',
        'wallet_fail': 'Wallet connection failed',
        'wallet_exists': 'Wallet already set: {w}',
        'fetching_me': 'Fetching account info...',
        'me_ok': 'Account info fetched',
        'me_fail': 'Failed to fetch account info',
        'withdraw_quote': 'Fee: {fee} | First time: {first} | Min: {min}',
        'fetching_quote': 'Fetching withdrawal info...',
        'summary_header': 'Summary:',
        'summary_user': 'User:       {v}',
        'summary_points': 'Points:     {v}',
        'summary_sparks': 'Sparks:     {v}',
        'summary_wallet': 'Wallet:     {v}',
        'summary_twitter': 'Twitter:    {v}',
        'success_line': 'Success | @{u} -> {w}',
        'err_runtime': 'Error: {e}',
        'retry': 'Retry {cur}/{max}...',
    }
}

def get_language():
    lang = os.getenv('LANG', 'en').lower()
    return 'vi' if 'vi' in lang or 'vn' in lang else 'en'

def print_border(text, color=Fore.CYAN, width=BORDER_WIDTH):
    text = text.strip()
    if len(text) > width - 4:
        text = text[:width - 7] + "..."
    padded = f" {text} ".center(width - 2)
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│{padded}│{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

def print_separator(color=Fore.MAGENTA):
    print(f"{color}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

def p(icon, text, color=Fore.CYAN):
    print(f"{color}  {icon} {text}{Style.RESET_ALL}")

def load_accounts(filepath="accounts.txt"):
    if not os.path.exists(filepath): return []
    accounts = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                accounts.append(line)
    return accounts

def load_wallets(filepath="address-ton.txt"):
    if not os.path.exists(filepath): return []
    wallets = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                wallets.append(line)
    return wallets

def load_proxies(filepath="proxies.txt"):
    if not os.path.exists(filepath): return []
    proxies = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    return proxies

def normalize_proxy_url(proxy):
    if re.match(r'^(https?|socks[45])://', proxy):
        return proxy
    parts = proxy.rsplit(':', 3)
    if len(parts) == 4:
        return f'socks5://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
    return f'socks5://{proxy}'

def parse_init_data(init_data):
    parsed = urllib.parse.parse_qs(init_data)
    user_raw = parsed.get('user', [None])[0]
    user_info = json.loads(urllib.parse.unquote(user_raw)) if user_raw else {}
    username = user_info.get('username', 'unknown')
    first_name = user_info.get('first_name', '')
    start_param = parsed.get('start_param', [None])[0]
    ref = start_param.split('_', 1)[1] if start_param and '_' in start_param else '921415493'
    return username, first_name, ref

async def get_ip(session):
    try:
        async with session.get('https://api.ipify.org?format=json', timeout=10) as resp:
            return (await resp.json()).get('ip', 'Unknown')
    except:
        return 'Unknown'

def _headers(init_data=None):
    h = {
        "accept": "application/json, text/plain, */*",
        "origin": "https://app.gomine.social",
        "referer": "https://app.gomine.social/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    if init_data:
        h["x-init-data"] = init_data
    return h

def _tga_headers():
    return {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://app.gomine.social",
        "referer": "https://app.gomine.social/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "tga-auth-token": TGA_AUTH_TOKEN,
    }

async def init_user(session, init_data, username, first_name, ref):
    payload = {"username": username, "first_name": first_name}
    if ref:
        payload["ref"] = ref
    h = _headers(init_data)
    h["content-type"] = "application/json"
    try:
        async with session.post(f"{API_BASE}/api/users/init", json=payload, headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def connect_wallet(session, init_data, wallet_address):
    h = _headers(init_data)
    h["content-type"] = "application/json"
    h["referer"] = "https://app.gomine.social/wallet"
    try:
        async with session.post(f"{API_BASE}/api/users/wallet", json={"wallet_address": wallet_address}, headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def get_me(session, init_data):
    h = _headers(init_data)
    h["referer"] = "https://app.gomine.social/wallet"
    try:
        async with session.get(f"{API_BASE}/api/users/me", headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def get_withdraw_quote(session, init_data):
    h = _headers(init_data)
    h["referer"] = "https://app.gomine.social/wallet"
    try:
        async with session.get(f"{API_BASE}/api/users/withdraw/quote", headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def send_tga_event(session, event_data):
    h = _tga_headers()
    try:
        async with session.post("https://tganalytics.xyz/events", json=[event_data], headers=h) as resp:
            return resp.status in (200, 202)
    except:
        return False

def make_tga_event(event_name, wallet_address, session_id, user_id, trace_id=None):
    raw_addr = wallet_address
    if raw_addr.startswith('UQ') or raw_addr.startswith('EQ') or raw_addr.startswith('0:'):
        pass
    hex_addr = ""
    if raw_addr.startswith('UQ') or raw_addr.startswith('EQ'):
        try:
            import base64
            b = base64.urlsafe_b64decode(raw_addr + '=' * (8 - len(raw_addr) % 8))
            hex_addr = "0:" + b[1:33].hex()
        except:
            hex_addr = raw_addr
    elif raw_addr.startswith('0:'):
        hex_addr = raw_addr
    else:
        hex_addr = raw_addr

    event = {
        "event_name": event_name,
        "is_success": True,
        "trace_id": trace_id,
        "wallet_address": hex_addr or raw_addr,
        "wallet_state_init": "",
        "wallet_type": "Tonkeeper",
        "wallet_version": "26.06.1",
        "auth_type": "ton_addr",
        "custom_data": {
            "client_id": "51384351a383d99bd600fe5e47a5d80632d3abd463e581fb638beab659269c3d",
            "wallet_id": "e03dfdd4121abfb3675e9bacfb7177675cc25415538fb56db605eb7b4906de0d",
            "chain_id": "-239",
            "provider": "http",
            "ton_connect_sdk_lib": "3.4.1",
            "ton_connect_ui_lib": "2.4.4",
        },
        "session_id": session_id,
        "user_id": user_id,
        "app_name": "gomine",
        "is_premium": False,
        "platform": "web",
        "locale": "vi",
        "start_param": "ref_8717833474",
        "client_timestamp": str(int(asyncio.get_event_loop().time() * 1000)),
    }
    return event

async def process_account(init_data, wallet_address, proxy, lang_dict, index, total, semaphore):
    async with semaphore:
        return await _process_account(init_data, wallet_address, proxy, lang_dict, index, total)

async def _process_account(init_data, wallet_address, proxy, lang_dict, index, total):
    username, first_name, ref = parse_init_data(init_data)
    result = {
        'label': f'Account {index + 1}',
        'success': False,
        'username': username,
        'error': None,
    }

    connector = ProxyConnector.from_url(normalize_proxy_url(proxy)) if proxy else aiohttp.TCPConnector()

    try:
        async with aiohttp.ClientSession(connector=connector,
                timeout=aiohttp.ClientTimeout(total=CONFIG['TIMEOUT']),
                cookie_jar=aiohttp.CookieJar()) as session:

            print()
            print_border(lang_dict['account_label'].format(i=index + 1, u=username), Fore.YELLOW)
            print(f"{Fore.CYAN}  {lang_dict['wallet_label'].format(w=wallet_address)}{Style.RESET_ALL}")
            if proxy:
                real_ip = await get_ip(session)
                print(f"{Fore.CYAN}  {lang_dict['proxy_line'].format(proxy=proxy, ip=real_ip)}{Style.RESET_ALL}")
            print()

            p(">", lang_dict['init_user'], Fore.YELLOW)
            user = None
            for a in range(CONFIG['RETRY_ATTEMPTS']):
                user = await init_user(session, init_data, username, first_name, ref)
                if user: break
                if a < CONFIG['RETRY_ATTEMPTS'] - 1:
                    p("↻", lang_dict['retry'].format(cur=a + 1, max=CONFIG['RETRY_ATTEMPTS']), Fore.YELLOW)
                    await asyncio.sleep(CONFIG['RETRY_DELAY'])
            if not user:
                p("✖", lang_dict['init_fail'], Fore.RED)
                result['error'] = 'Init failed'
                return result
            uid = user.get('id', '?')
            tier = user.get('access_tier_name', '?')
            pts = user.get('points', 0)
            sparks = user.get('sparks', 0)
            existing_wallet = user.get('wallet_address')
            tw_username = user.get('twitter_username')
            user_id = user.get('telegram_id', 921415493)
            p("✓", lang_dict['init_ok'].format(id=uid, tier=tier), Fore.GREEN)
            p("ℹ", f"Points: {pts} | Sparks: {sparks} | Streak: {user.get('streak_days', 0)}d", Fore.CYAN)

            if existing_wallet:
                p("ℹ", lang_dict['wallet_exists'].format(w=existing_wallet), Fore.GREEN)
            else:
                p(">", lang_dict['connecting_wallet'], Fore.YELLOW)
                wal_result = None
                for a in range(CONFIG['RETRY_ATTEMPTS']):
                    wal_result = await connect_wallet(session, init_data, wallet_address)
                    if wal_result: break
                    if a < CONFIG['RETRY_ATTEMPTS'] - 1:
                        p("↻", lang_dict['retry'].format(cur=a + 1, max=CONFIG['RETRY_ATTEMPTS']), Fore.YELLOW)
                        await asyncio.sleep(CONFIG['RETRY_DELAY'])
                if wal_result and wal_result.get('success'):
                    p("✓", lang_dict['wallet_ok'], Fore.GREEN)
                else:
                    p("✖", lang_dict['wallet_fail'], Fore.RED)
                    result['success'] = True
                    return result
            print()

            p(">", lang_dict['fetching_me'], Fore.YELLOW)
            me = await get_me(session, init_data)
            if me:
                p("✓", lang_dict['me_ok'], Fore.GREEN)
                wallet_addr = me.get('wallet_address', wallet_address)
                pts = me.get('points', pts)
                sparks = me.get('sparks', sparks)
                tw_username = me.get('twitter_username', tw_username)
            else:
                p("✖", lang_dict['me_fail'], Fore.RED)
                wallet_addr = wallet_address
            print()

            p(">", lang_dict['fetching_quote'], Fore.YELLOW)
            quote = await get_withdraw_quote(session, init_data)
            if quote:
                fee = f"{quote.get('fee_gomine', 0):,}"
                first_time = 'Yes' if quote.get('first_time') else 'No'
                min_wd = f"{quote.get('min_withdrawal', 0):,}"
                p("ℹ", lang_dict['withdraw_quote'].format(fee=fee, first=first_time, min=min_wd), Fore.CYAN)
            print()

            session_id = None
            try:
                import uuid
                session_id = str(uuid.uuid4())
            except:
                session_id = f"{index}-{username}-{int(asyncio.get_event_loop().time())}"

            trace_id = str(uuid.uuid4()) if 'uuid' in dir() else None

            start_event = make_tga_event("connection-started", wallet_addr, session_id, user_id)
            await send_tga_event(session, start_event)
            await asyncio.sleep(0.5)
            complete_event = make_tga_event("connection-completed", wallet_addr, session_id, user_id, trace_id)
            await send_tga_event(session, complete_event)

            result['success'] = True

            print(f"{Fore.CYAN}  {'─' * 50}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {lang_dict['summary_header']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}     {lang_dict['summary_user'].format(v=f'{Fore.YELLOW}@{username}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}     {lang_dict['summary_points'].format(v=f'{Fore.YELLOW}{pts}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}     {lang_dict['summary_sparks'].format(v=f'{Fore.YELLOW}{sparks}{Style.RESET_ALL}')}")
            wal_st = wallet_addr[:8] + '...' if len(wallet_addr) > 8 else wallet_addr
            print(f"{Fore.CYAN}     {lang_dict['summary_wallet'].format(v=f'{Fore.GREEN}{wal_st}{Style.RESET_ALL}')}")
            tw_st = f'@{tw_username}' if tw_username else 'Not linked'
            tw_clr = Fore.GREEN if tw_username else Fore.RED
            print(f"{Fore.CYAN}     {lang_dict['summary_twitter'].format(v=f'{tw_clr}{tw_st}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}  {'─' * 50}{Style.RESET_ALL}")
            print()
            p("✅", lang_dict['success_line'].format(u=username, w=wallet_address[:12] + '...' if len(wallet_address) > 12 else wallet_address), Fore.GREEN)
            print()

    except Exception as e:
        p("✖", lang_dict['err_runtime'].format(e=str(e)), Fore.RED)
        import traceback
        print(f"{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
        result['error'] = str(e)

    return result

async def run_connect_wallet(language='vi'):
    lang = language or get_language()
    lang_dict = LANG[lang]
    print(); print_border(lang_dict['title'], Fore.CYAN); print()

    accounts = load_accounts()
    wallets = load_wallets()

    if not accounts:
        p("❌", lang_dict['no_accounts'], Fore.RED)
        print(f"{Fore.YELLOW}  Mỗi dòng: init-data từ Telegram{Style.RESET_ALL}")
        return
    if not wallets:
        p("❌", lang_dict['no_wallets'], Fore.RED)
        print(f"{Fore.YELLOW}  Mỗi dòng: địa chỉ ví TON (UQ... hoặc EQ...){Style.RESET_ALL}")
        return
    if len(accounts) != len(wallets):
        p("⚠", lang_dict['mismatch'].format(a=len(accounts), w=len(wallets)), Fore.YELLOW)

    p("ℹ", lang_dict['found_accounts'].format(count=len(accounts)), Fore.GREEN)
    p("ℹ", lang_dict['found_wallets'].format(count=len(wallets)), Fore.GREEN)

    proxies = load_proxies()
    if proxies:
        p("ℹ", lang_dict['found_proxies'].format(count=len(proxies)), Fore.GREEN)
    else:
        p("ℹ", lang_dict['no_proxies'], Fore.YELLOW)

    print(); print_separator()
    print_border(f"⚙ {lang_dict['processing'].format(count=len(accounts))}", Fore.MAGENTA)
    print_separator(); print()

    semaphore = asyncio.Semaphore(CONFIG['MAX_CONCURRENT'])
    tasks = []
    for i, acc in enumerate(accounts):
        wal = wallets[i % len(wallets)]
        proxy = proxies[i % len(proxies)] if proxies else None
        tasks.append(process_account(acc, wal, proxy, lang_dict, i, len(accounts), semaphore))
    results = await asyncio.gather(*tasks)

    print(); print_separator()
    ok_count = sum(1 for r in results if r['success'])
    print_border(f"✅ {lang_dict['completed'].format(ok=ok_count, total=len(results))}", Fore.GREEN)
    print_separator(); print()

if __name__ == "__main__":
    asyncio.run(run_connect_wallet('vi'))
