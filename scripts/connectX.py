import os, sys, asyncio, aiohttp, json, re, urllib.parse
from typing import List, Optional, Dict
from urllib.parse import parse_qs, urlparse, quote
from aiohttp_socks import ProxyConnector
from colorama import init, Fore, Style

init(autoreset=True)

BORDER_WIDTH = 80
API_BASE = "https://app.gomine.social"
TWITTER_API_BASE = "https://x.com"
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

CONFIG = {"RETRY_ATTEMPTS": 3, "RETRY_DELAY": 2, "TIMEOUT": 60, "MAX_CONCURRENT": 10}

LANG = {
    'vi': {
        'title': 'GOMINE SOCIAL - BOT',
        'found_accounts': 'Tìm thấy {count} tài khoản',
        'found_proxies': 'Tìm thấy {count} proxy',
        'no_proxies': 'Không có proxy, chạy trực tiếp',
        'no_accounts': 'Không tìm thấy accounts.txt',
        'processing': 'ĐANG XỬ LÝ {count} TÀI KHOẢN',
        'completed': 'HOÀN THÀNH: {ok}/{total} TÀI KHOẢN',
        'proxy_line': 'Proxy: [{proxy}] | IP: [{ip}]',
        'account_label': 'Tài khoản {i}: @{u}',
        'establishing_session': 'Đang thiết lập phiên...',
        'session_established': 'Phiên đã được thiết lập',
        'init_user': 'Đang khởi tạo người dùng...',
        'init_ok': 'Khởi tạo thành công! ID: {id} | Tier: {tier}',
        'init_fail': 'Khởi tạo thất bại',
        'fetching_info': 'Đang lấy thông tin...',
        'onboarding': 'Onboarding: {v}/{total} | X: {x} | Wallet: {w} | Task: {t}',
        'burns': 'GoMine: {g} | Burns: {b} | Last: {tx}',
        'fetching_twitter_url': 'Đang lấy link xác thực Twitter...',
        'twitter_url_ok': 'Lấy link Twitter thành công',
        'twitter_url_fail': 'Lấy link Twitter thất bại',
        'twitter_auto_auth': 'Đang tự động xác thực Twitter...',
        'twitter_auto_auth_ok': 'Xác thực Twitter thành công!',
        'twitter_auto_auth_fail': 'Xác thực Twitter thất bại',
        'twitter_linking': 'Đang liên kết Twitter với GoMine...',
        'twitter_linked': 'Liên kết Twitter thành công!',
        'twitter_link_fail': 'Liên kết Twitter thất bại',
        'summary_header': 'Tóm tắt:',
        'summary_user': 'User:       {v}',
        'summary_points': 'Points:     {v}',
        'summary_sparks': 'Sparks:     {v}',
        'summary_twitter': 'Twitter:    {v}',
        'summary_onboarding': 'Onboard:    {v}/{total}',
        'success_line': 'Thành công | @{u}',
        'err_runtime': 'Lỗi: {e}',
        'retry': 'Retry {cur}/{max}...',
    },
    'en': {
        'title': 'GOMINE SOCIAL - BOT',
        'found_accounts': 'Found {count} accounts',
        'found_proxies': 'Found {count} proxies',
        'no_proxies': 'No proxies, running direct',
        'no_accounts': 'accounts.txt not found',
        'processing': 'PROCESSING {count} ACCOUNTS',
        'completed': 'COMPLETED: {ok}/{total} ACCOUNTS',
        'proxy_line': 'Proxy: [{proxy}] | IP: [{ip}]',
        'account_label': 'Account {i}: @{u}',
        'establishing_session': 'Establishing session...',
        'session_established': 'Session established',
        'init_user': 'Initializing user...',
        'init_ok': 'Initialized! ID: {id} | Tier: {tier}',
        'init_fail': 'Init failed',
        'fetching_info': 'Fetching info...',
        'onboarding': 'Onboarding: {v}/{total} | X: {x} | Wallet: {w} | Task: {t}',
        'burns': 'GoMine: {g} | Burns: {b} | Last: {tx}',
        'fetching_twitter_url': 'Fetching Twitter auth URL...',
        'twitter_url_ok': 'Twitter URL obtained',
        'twitter_url_fail': 'Twitter URL failed',
        'twitter_auto_auth': 'Auto-authenticating Twitter...',
        'twitter_auto_auth_ok': 'Twitter auth successful!',
        'twitter_auto_auth_fail': 'Twitter auth failed',
        'twitter_linking': 'Linking Twitter to GoMine...',
        'twitter_linked': 'Twitter linked successfully!',
        'twitter_link_fail': 'Twitter link failed',
        'summary_header': 'Summary:',
        'summary_user': 'User:       {v}',
        'summary_points': 'Points:     {v}',
        'summary_sparks': 'Sparks:     {v}',
        'summary_twitter': 'Twitter:    {v}',
        'summary_onboarding': 'Onboard:    {v}/{total}',
        'success_line': 'Success | @{u}',
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

async def get_onboarding(session, init_data):
    h = _headers(init_data)
    try:
        async with session.get(f"{API_BASE}/api/users/onboarding", headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def get_burns(session, init_data):
    h = _headers(init_data)
    try:
        async with session.get(f"{API_BASE}/api/users/burns", headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def get_twitter_auth_url(session, init_data):
    h = _headers(init_data)
    try:
        async with session.get(f"{API_BASE}/api/twitter/auth/url", headers=h) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def link_twitter_callback(session, init_data, code, state):
    url = f"{API_BASE}/api/twitter/callback?code={code}&state={state}"
    h = _headers(init_data)
    h["accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    try:
        async with session.get(url, headers=h, allow_redirects=True) as resp:
            return resp.status in (200, 302, 301, 307)
    except:
        pass
    return False

class TwitterOAuth:
    def __init__(self, auth_token, ct0, session):
        self.auth_token = auth_token
        self.ct0 = ct0
        self.session = session

    def _get_headers(self, referer=None):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
            "X-Csrf-Token": self.ct0, "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session", "x-twitter-client-language": "en",
            "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
        }
        if referer: headers["Referer"] = referer
        return headers

    def _get_cookies(self):
        return {"auth_token": self.auth_token, "ct0": self.ct0}

    async def get_authorization_code(self, state, challenge, client_id, redirect_uri, scope):
        auth_url = f"{TWITTER_API_BASE}/i/api/2/oauth2/authorize"
        params = {"client_id": client_id, "code_challenge": challenge, "code_challenge_method": "S256",
                  "redirect_uri": redirect_uri, "response_type": "code", "scope": scope, "state": state}
        referer = (f"{TWITTER_API_BASE}/i/oauth2/authorize?response_type=code"
                   f"&client_id={client_id}&redirect_uri={quote(redirect_uri, safe='')}"
                   f"&scope={scope.replace(' ', '%20')}&state={state}"
                   f"&code_challenge={challenge}&code_challenge_method=S256")
        try:
            async with self.session.get(auth_url, params=params, headers=self._get_headers(referer),
                    cookies=self._get_cookies(), timeout=aiohttp.ClientTimeout(total=CONFIG['TIMEOUT'])) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                auth_code = data.get("auth_code")
                if not auth_code: return None
                return await self._approve(auth_code, state, challenge, client_id, redirect_uri, scope, referer)
        except:
            return None

    async def _approve(self, auth_code, state, challenge, client_id, redirect_uri, scope, referer):
        headers = self._get_headers(referer)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            async with self.session.post(f"{TWITTER_API_BASE}/i/api/2/oauth2/authorize",
                headers=headers, cookies=self._get_cookies(), data=f"approval=true&code={auth_code}",
                timeout=aiohttp.ClientTimeout(total=CONFIG['TIMEOUT'])) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    redirect = result.get("redirect_uri", "")
                    if redirect:
                        qp = parse_qs(urlparse(redirect).query)
                        if 'code' in qp:
                            return qp['code'][0]
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
    }

    connector = ProxyConnector.from_url(normalize_proxy_url(proxy)) if proxy else aiohttp.TCPConnector(limit=0, force_close=False)

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
            user = await init_user(session, init_data, username, first_name, ref)
            if not user:
                p("✖", lang_dict['init_fail'], Fore.RED)
                result['error'] = 'Init failed'
                return result
            uid = user.get('id', '?')
            tier = user.get('access_tier_name', '?')
            pts = user.get('points', 0)
            sparks = user.get('sparks', 0)
            tw_username = user.get('twitter_username')
            p("✓", lang_dict['init_ok'].format(id=uid, tier=tier), Fore.GREEN)
            p("ℹ", f"Points: {pts} | Sparks: {sparks} | Streak: {user.get('streak_days', 0)}d", Fore.CYAN)

            p(">", lang_dict['fetching_info'], Fore.YELLOW)
            onboard = await get_onboarding(session, init_data)
            if onboard:
                done = onboard.get('done', 0)
                total_onboard = onboard.get('total', 5)
                linked_x = onboard.get('linked_x', False)
                has_wallet = onboard.get('has_wallet', False)
                did_task = onboard.get('did_task', False)
                p("✓", lang_dict['onboarding'].format(v=done, total=total_onboard,
                    x='Yes' if linked_x else 'No', w='Yes' if has_wallet else 'No',
                    t='Yes' if did_task else 'No'), Fore.GREEN)

            burns = await get_burns(session, init_data)
            if burns:
                total_g = burns.get('total_gomine', 0)
                b_count = burns.get('burns', 0)
                last_tx = burns.get('last_tx', '')[:12] + '...' if burns.get('last_tx') else 'N/A'
                p("ℹ", lang_dict['burns'].format(g=f"{total_g:,.2f}", b=b_count, tx=last_tx), Fore.CYAN)
            print()

            if not tw_username and not (onboard and onboard.get('linked_x')):
                p(">", lang_dict['fetching_twitter_url'], Fore.YELLOW)
                auth_data = None
                for a in range(CONFIG['RETRY_ATTEMPTS']):
                    auth_data = await get_twitter_auth_url(session, init_data)
                    if auth_data:
                        p("✓", lang_dict['twitter_url_ok'], Fore.GREEN)
                        break
                    if a < CONFIG['RETRY_ATTEMPTS'] - 1:
                        p("↻", lang_dict['retry'].format(cur=a + 1, max=CONFIG['RETRY_ATTEMPTS']), Fore.YELLOW)
                        await asyncio.sleep(CONFIG['RETRY_DELAY'])
                else:
                    p("✖", lang_dict['twitter_url_fail'], Fore.RED)
                    result['success'] = True
                    return result

                oauth_url = auth_data.get('url', '')
                parsed = urlparse(oauth_url)
                qp = parse_qs(parsed.query)
                oauth_state = qp.get('state', [None])[0]
                code_challenge = qp.get('code_challenge', [None])[0]
                oauth_client_id = qp.get('client_id', [None])[0]
                oauth_redirect_uri = qp.get('redirect_uri', [None])[0]
                oauth_scope = qp.get('scope', [None])[0]

                if not all([oauth_state, code_challenge, oauth_client_id, oauth_redirect_uri, oauth_scope]):
                    p("✖", "Không thể phân tích tham số OAuth", Fore.RED)
                    result['success'] = True
                    return result

                p(">", lang_dict['twitter_auto_auth'], Fore.CYAN)
                tw = TwitterOAuth(None, None, session)
                tw_token = None
                tw_tokens = load_twitter_tokens()
                if tw_tokens:
                    tw_token = tw_tokens[index % len(tw_tokens)]

                if tw_token:
                    tw = TwitterOAuth(tw_token['auth_token'], tw_token['ct0'], session)
                    oauth_code = await tw.get_authorization_code(oauth_state, code_challenge, oauth_client_id, oauth_redirect_uri, oauth_scope)
                    if not oauth_code:
                        p("✖", lang_dict['twitter_auto_auth_fail'], Fore.RED)
                    else:
                        p("✓", lang_dict['twitter_auto_auth_ok'], Fore.GREEN)
                        p(">", lang_dict['twitter_linking'], Fore.YELLOW)
                        if await link_twitter_callback(session, init_data, oauth_code, oauth_state):
                            p("✓", lang_dict['twitter_linked'], Fore.GREEN)
                            tw_username = 'linked'
                        else:
                            p("✖", lang_dict['twitter_link_fail'], Fore.RED)
                else:
                    p("ℹ", "Không có token Twitter để tự động xác thực.", Fore.YELLOW)
            else:
                p("ℹ", f"Twitter đã kết nối: @{tw_username}", Fore.GREEN)

            result['success'] = True

            print(f"{Fore.CYAN}  {'─' * 50}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {lang_dict['summary_header']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}     {lang_dict['summary_user'].format(v=f'{Fore.YELLOW}@{username}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}     {lang_dict['summary_points'].format(v=f'{Fore.YELLOW}{pts}{Style.RESET_ALL}')}")
            print(f"{Fore.CYAN}     {lang_dict['summary_sparks'].format(v=f'{Fore.YELLOW}{sparks}{Style.RESET_ALL}')}")
            tw_st = f'@{tw_username}' if tw_username else 'Not linked'
            tw_clr = Fore.GREEN if tw_username else Fore.RED
            print(f"{Fore.CYAN}     {lang_dict['summary_twitter'].format(v=f'{tw_clr}{tw_st}{Style.RESET_ALL}')}")
            if onboard:
                print(f"{Fore.CYAN}     {lang_dict['summary_onboarding'].format(v=done, total=total_onboard)}")
            print(f"{Fore.CYAN}  {'─' * 50}{Style.RESET_ALL}")
            print()
            if result['success']:
                p("✅", lang_dict['success_line'].format(u=username), Fore.GREEN)
            print()

    except Exception as e:
        p("✖", lang_dict['err_runtime'].format(e=str(e)), Fore.RED)
        import traceback
        print(f"{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
        result['error'] = str(e)

    return result

def load_twitter_tokens(filepath="tokenX.txt"):
    if not os.path.exists(filepath): return []
    tokens = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            delim = '|' if '|' in line else ':'
            parts = line.split(delim)
            if len(parts) >= 2:
                tokens.append({"auth_token": parts[0].strip(), "ct0": parts[1].strip()})
    return tokens

async def run_connectX(language='vi'):
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
    print_border(f"✅ {lang_dict['completed'].format(ok=ok_count, total=len(results))}", Fore.GREEN)
    print_separator(); print()

if __name__ == "__main__":
    asyncio.run(run_connectX('vi'))
