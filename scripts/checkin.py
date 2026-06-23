import os, sys, asyncio, aiohttp, json, re, urllib.parse
from typing import List, Optional, Dict
from aiohttp_socks import ProxyConnector
from colorama import init, Fore, Style

init(autoreset=True)

BORDER_WIDTH = 80
API_BASE = "https://app.gomine.social"

CONFIG = {"RETRY_ATTEMPTS": 3, "RETRY_DELAY": 2, "TIMEOUT": 60, "MAX_CONCURRENT": 10}

LANG = {
    'vi': {
        'title': 'GOMINE SOCIAL - CHECKIN BOT',
        'found_accounts': 'Tìm thấy {count} tài khoản',
        'found_proxies': 'Tìm thấy {count} proxy',
        'no_proxies': 'Không có proxy, chạy trực tiếp',
        'no_accounts': 'Không tìm thấy accounts.txt',
        'processing': 'ĐANG CHECKIN {count} TÀI KHOẢN',
        'completed': 'HOÀN THÀNH: {ok}/{total} TÀI KHOẢN',
        'proxy_line': 'Proxy: [{proxy}] | IP: [{ip}]',
        'account_label': 'Tài khoản {i}: @{u}',
        'init_user': 'Đang khởi tạo người dùng...',
        'init_ok': 'Khởi tạo thành công! ID: {id} | Tier: {tier}',
        'init_fail': 'Khởi tạo thất bại',
        'checking_in': 'Đang checkin...',
        'checkin_ok': 'Checkin thành công! Sparks: +{sparks} | Streak: {streak}d | Multiplier: {multi}x',
        'checkin_already': 'Hôm nay đã checkin! (Last: {last})',
        'checkin_fail': 'Checkin thất bại',
        'fetching_me': 'Đang lấy thông tin tài khoản...',
        'me_ok': 'Sparks: {s} | Streak: {d}d | Last checkin: {last}',
        'me_fail': 'Lấy thông tin thất bại',
        'summary_header': 'Tóm tắt:',
        'summary_user': 'User:       {v}',
        'summary_points': 'Points:     {v}',
        'summary_sparks': 'Sparks:     {v}',
        'summary_streak': 'Streak:     {v}d',
        'summary_checkin': 'Checkin:    {v}',
        'success_line': 'Thành công | @{u} (+{sparks} sparks)',
        'err_runtime': 'Lỗi: {e}',
        'retry': 'Retry {cur}/{max}...',
    },
    'en': {
        'title': 'GOMINE SOCIAL - CHECKIN BOT',
        'found_accounts': 'Found {count} accounts',
        'found_proxies': 'Found {count} proxies',
        'no_proxies': 'No proxies, running direct',
        'no_accounts': 'accounts.txt not found',
        'processing': 'CHECKING IN {count} ACCOUNTS',
        'completed': 'COMPLETED: {ok}/{total} ACCOUNTS',
        'proxy_line': 'Proxy: [{proxy}] | IP: [{ip}]',
        'account_label': 'Account {i}: @{u}',
        'init_user': 'Initializing user...',
        'init_ok': 'Initialized! ID: {id} | Tier: {tier}',
        'init_fail': 'Init failed',
        'checking_in': 'Checking in...',
        'checkin_ok': 'Checkin done! Sparks: +{sparks} | Streak: {streak}d | Multiplier: {multi}x',
        'checkin_already': 'Already checked in today! (Last: {last})',
        'checkin_fail': 'Checkin failed',
        'fetching_me': 'Fetching account info...',
        'me_ok': 'Sparks: {s} | Streak: {d}d | Last checkin: {last}',
        'me_fail': 'Failed to fetch info',
        'summary_header': 'Summary:',
        'summary_user': 'User:       {v}',
        'summary_points': 'Points:     {v}',
        'summary_sparks': 'Sparks:     {v}',
        'summary_streak': 'Streak:     {v}d',
        'summary_checkin': 'Checkin:    {v}',
        'success_line': 'Success | @{u} (+{sparks} sparks)',
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

async def checkin(session, init_data):
    h = _headers(init_data)
    h["content-type"] = "application/json"
    try:
        async with session.post(f"{API_BASE}/api/users/checkin", json={}, headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def get_me(session, init_data):
    h = _headers(init_data)
    try:
        async with session.get(f"{API_BASE}/api/users/me", headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def process_account(init_data, proxy, lang_dict, index, total, semaphore):
    async with semaphore:
        return await _process_account(init_data, proxy, lang_dict, index, total)

async def _process_account(init_data, proxy, lang_dict, index, total):
    username, first_name, ref = parse_init_data(init_data)
    result = {
        'label': f'Account {index + 1}',
        'success': False,
        'username': username,
        'error': None,
        'sparks': 0,
    }

    connector = ProxyConnector.from_url(normalize_proxy_url(proxy)) if proxy else aiohttp.TCPConnector()

    try:
        async with aiohttp.ClientSession(connector=connector,
                timeout=aiohttp.ClientTimeout(total=CONFIG['TIMEOUT']),
                cookie_jar=aiohttp.CookieJar()) as session:

            print()
            print_border(lang_dict['account_label'].format(i=index + 1, u=username), Fore.YELLOW)
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
            sparks_before = user.get('sparks', 0)
            p("✓", lang_dict['init_ok'].format(id=uid, tier=tier), Fore.GREEN)
            p("ℹ", f"Points: {pts} | Sparks: {sparks_before}", Fore.CYAN)

            p(">", lang_dict['checking_in'], Fore.YELLOW)
            ck = None
            for a in range(CONFIG['RETRY_ATTEMPTS']):
                ck = await checkin(session, init_data)
                if ck: break
                if a < CONFIG['RETRY_ATTEMPTS'] - 1:
                    p("↻", lang_dict['retry'].format(cur=a + 1, max=CONFIG['RETRY_ATTEMPTS']), Fore.YELLOW)
                    await asyncio.sleep(CONFIG['RETRY_DELAY'])

            awarded = 0
            if ck and ck.get('success'):
                awarded = ck.get('sparks_awarded', 0)
                streak = ck.get('streak_days', 0)
                multi = ck.get('streak_multiplier', 1.0)
                p("✓", lang_dict['checkin_ok'].format(sparks=awarded, streak=streak, multi=multi), Fore.GREEN)
                result['sparks'] = awarded
            elif ck and not ck.get('success'):
                p("✖", lang_dict['checkin_fail'], Fore.RED)
            else:
                # Could already be checked in today — check /api/users/me
                p("ℹ", lang_dict['checkin_already'].format(last='today'), Fore.YELLOW)
            print()

            p(">", lang_dict['fetching_me'], Fore.YELLOW)
            me = await get_me(session, init_data)
            if me:
                sp = me.get('sparks', sparks_before)
                sd = me.get('streak_days', 0)
                lc = me.get('last_checkin', 'N/A')
                p("✓", lang_dict['me_ok'].format(s=sp, d=sd, last=lc), Fore.GREEN)
                sparks_after = sp
            else:
                p("✖", lang_dict['me_fail'], Fore.RED)
                sparks_after = sparks_before + awarded
            print()

            result['success'] = True

            print(f"{Fore.CYAN}  {'─' * 50}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {lang_dict['summary_header']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}     {lang_dict['summary_user'].format(v=f'{Fore.YELLOW}@{username}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}     {lang_dict['summary_points'].format(v=f'{Fore.YELLOW}{pts}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}     {lang_dict['summary_sparks'].format(v=f'{Fore.YELLOW}{sparks_before} -> {sparks_after}{Style.RESET_ALL}')}")
            if me:
                print(f"{Fore.CYAN}     {lang_dict['summary_streak'].format(v=f'{Fore.YELLOW}{me.get("streak_days", 0)}{Style.RESET_ALL}')}")
                ci_status = Fore.GREEN if awarded > 0 else Fore.YELLOW
                ci_txt = f'+{awarded} sparks' if awarded > 0 else 'Already checked in'
                print(f"{Fore.CYAN}     {lang_dict['summary_checkin'].format(v=f'{ci_status}{ci_txt}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}  {'─' * 50}{Style.RESET_ALL}")
            print()
            p("✅", lang_dict['success_line'].format(u=username, sparks=result['sparks'] or 0), Fore.GREEN)
            print()

    except Exception as e:
        p("✖", lang_dict['err_runtime'].format(e=str(e)), Fore.RED)
        import traceback
        print(f"{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
        result['error'] = str(e)

    return result

async def run_checkin(language='vi'):
    lang = language or get_language()
    lang_dict = LANG[lang]
    print(); print_border(lang_dict['title'], Fore.CYAN); print()

    accounts = load_accounts()
    if not accounts:
        p("❌", lang_dict['no_accounts'], Fore.RED)
        print(f"{Fore.YELLOW}  Mỗi dòng: init-data từ Telegram{Style.RESET_ALL}")
        return
    p("ℹ", lang_dict['found_accounts'].format(count=len(accounts)), Fore.GREEN)

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
        proxy = proxies[i % len(proxies)] if proxies else None
        tasks.append(process_account(acc, proxy, lang_dict, i, len(accounts), semaphore))
    results = await asyncio.gather(*tasks)

    print(); print_separator()
    ok_count = sum(1 for r in results if r['success'])
    total_sparks = sum(r.get('sparks', 0) for r in results)
    summary = f"✅ {lang_dict['completed'].format(ok=ok_count, total=len(results))}"
    if total_sparks > 0:
        summary += f" | Total sparks: +{total_sparks}"
    print_border(summary, Fore.GREEN)
    print_separator(); print()

if __name__ == "__main__":
    asyncio.run(run_checkin('vi'))
