# Gradio_11Labs_Enhanced_with_Proxy.py
# ============================================================================
# 2025-07-09 – *Proxy + Full Voice Manager + UX Tweaks + Privacy Protection*
# ---------------------------------------------------------------------------
#  ✦ Proxy Tab: bulk add/test, auto/manual assign (≤3 keys/proxy), delete bad
#  ✦ Batch Tab: refresh-all, live token count, total credit, verify key-proxy
#                – "🌀 Tạo giọng nói" sits *above* textbox
#                – auto-pick checkbox at bottom
#  ✦ API-Key Tab: shows proxy **host** only (no creds/port)
#  ✦ Voice Tab: restored original full manager (add/edit/delete/reset/export)
#  ✦ Privacy: Hide sensitive info (API keys, proxy credentials, voice IDs)
#  ✦ Session: Use gr.State for per-browser isolation, auto-clear after session ends
# ---------------------------------------------------------------------------

import gradio as gr
import os, json, time, urllib.parse, requests, random
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import tempfile
import uuid
from functools import wraps

def log_exception(e, context=""):
    import traceback
    tb = traceback.format_exc()
    msg = f"❌ Lỗi ở {context}: {str(e)}\n{tb}"
    print(msg)
    return msg

# === .env ===
load_dotenv()
DEFAULT_MODEL = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
DEFAULT_FORMAT = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100")

# === Default Data ===
def load_default_voices():
    """Load default voices from voices.json"""
    try:
        with open("voices.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def load_default_proxies():
    """Load default proxies from proxies.json"""
    try:
        with open("proxies.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

DEFAULT_VOICE_SETTINGS = {
    "speed": 1.0,
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style_exaggeration": 0.0,
    "use_speaker_boost": True,
}

MODELS = ["eleven_monolingual_v1", "eleven_multilingual_v1", "eleven_multilingual_v2"]

# === Session Management ===
def session_wrapper(func):
    """Decorator to ensure session data access"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# === Privacy helpers ===
def mask_api_key(key):
    """Mask API key: show first 4 and last 4 chars"""
    if not key or len(key) < 8:
        return key
    return f"{key[:4]}...{key[-4:]}"

def mask_voice_id(voice_id):
    """Mask Voice ID: show first 3 and last 3 chars"""
    if not voice_id or len(voice_id) < 6:
        return voice_id
    return f"{voice_id[:3]}...{voice_id[-3:]}"

def mask_proxy_url(url):
    """Mask credentials in proxy URL"""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.username and parsed.password:
            masked_netloc = f"***:***@{parsed.hostname}"
            if parsed.port:
                masked_netloc += f":{parsed.port}"
            return urllib.parse.urlunparse((
                parsed.scheme, masked_netloc, parsed.path,
                parsed.params, parsed.query, parsed.fragment
            ))
        return url
    except:
        return url

def create_key_display_map(api_keys):
    """Create mapping between real API key and display name"""
    display_map = {}
    reverse_map = {}
    for i, key in enumerate(api_keys.keys(), 1):
        display_name = f"Key-{i:02d} ({mask_api_key(key)})"
        display_map[key] = display_name
        reverse_map[display_name] = key
    return display_map, reverse_map

def get_key_choices_for_display(api_keys):
    """Get list of masked API keys for display"""
    display_map, _ = create_key_display_map(api_keys)
    return list(display_map.values())

def get_real_key_from_display(display_name, api_keys):
    """Get real API key from display name"""
    _, reverse_map = create_key_display_map(api_keys)
    return reverse_map.get(display_name, display_name)

def create_proxy_display_map(proxies):
    """Create mapping between real proxy URL and display name"""
    display_map = {}
    reverse_map = {}
    for i, url in enumerate(proxies.keys(), 1):
        display_name = f"Proxy-{i:02d} ({mask_proxy_url(url)})"
        display_map[url] = display_name
        reverse_map[display_name] = url
    return display_map, reverse_map

def get_proxy_choices_for_display(proxies):
    """Get list of masked proxies for display"""
    display_map, _ = create_proxy_display_map(proxies)
    return list(display_map.values())

def get_real_proxy_from_display(display_name, proxies):
    """Get real proxy URL from display name"""
    _, reverse_map = create_proxy_display_map(proxies)
    return reverse_map.get(display_name, display_name)

# === Generic helpers ===
def safe_get_default(choices, default_func):
    """Safely get default value that exists in choices"""
    if not choices:
        return None
    default = default_func()
    return default if default in choices else choices[0]

# === ElevenLabs ===
def get_client(api_key):
    return ElevenLabs(api_key=api_key)

@session_wrapper
def get_api_usage(api_key, bypass_proxy=False, proxies=None):
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    proxy_url = None if bypass_proxy else get_proxy_of_key(api_key, proxies)
    proxies_dict = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": api_key},
            proxies=proxies_dict,
            timeout=4,
            verify=False if proxy_url else True
        )
        if r.status_code == 200:
            d = r.json()
            return {
                "status": "✅ OK",
                "used": d.get("character_count", 0),
                "limit": d.get("character_limit", 0),
                "tier": d.get("tier", ""),
                "remaining": d.get("character_limit", 0) - d.get("character_count", 0),
            }
        return {"status": f"❌ {r.status_code}"}
    except Exception as e:
        return {"status": f"⚠️ {str(e).split(' ')[0]}"}

def total_credit(api_keys):
    return sum(v.get("remaining", 0) for v in api_keys.values())

# === Proxy helpers ===
@session_wrapper
def proxy_host(url: str):
    try:
        return urllib.parse.urlsplit(url).hostname or ""
    except:
        return ""

@session_wrapper
def format_proxy_table(proxies):
    rows = []
    for url, info in proxies.items():
        masked_url = mask_proxy_url(url)
        masked_keys = [mask_api_key(k) for k in info.get("assigned_keys", [])]
        sample_keys = ", ".join(masked_keys[:3]) + ("…" if len(masked_keys) > 3 else "")
        rows.append([
            masked_url,
            info.get("status", "-"),
            info.get("latency", "-"),
            len(info.get("assigned_keys", [])),
            sample_keys,
            info.get("last_checked", "-"),
        ])
    return pd.DataFrame(rows, columns=["Proxy", "Status", "Latency (ms)", "#Keys", "Sample Keys", "Last check"])

@session_wrapper
def test_proxy_once(url: str, timeout=3):    # giảm timeout từ 6 -> 3
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    proxies = {"http": url, "https": url}
    t0 = time.time()
    try:
        r = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=timeout, verify=False)
        if r.status_code == 200:
            return {"status": "✅ OK", "latency": int((time.time()-t0)*1000)}
    except Exception as e:
        return {"status": f"⚠️ {str(e).split(' ')[0]}", "latency": None}
    return {"status": "❌ Failed", "latency": None}

@session_wrapper
def add_and_test_proxies(text, proxies_state):
    try:
        proxies = proxies_state.copy()
        added = 0
        for line in text.strip().splitlines():
            p = line.strip()
            if not p: continue
            if p not in proxies:
                proxies[p] = {"assigned_keys": []}
                added += 1
            proxies[p].update(test_proxy_once(p))
            proxies[p]["last_checked"] = datetime.utcnow().isoformat(timespec="seconds")
        return format_proxy_table(proxies), f"✅ Đã thêm/kiểm tra {added} proxy.", proxies
    except Exception as e:
        msg = log_exception(e, "add_and_test_proxies")
        return None, msg, proxies_state

@session_wrapper
def refresh_proxy_status(proxies_state):
    proxies = proxies_state.copy()
    for url in proxies:
        proxies[url].update(test_proxy_once(url))
        proxies[url]["last_checked"] = datetime.utcnow().isoformat(timespec="seconds")
    return format_proxy_table(proxies), "🔄 Đã refresh proxy.", proxies

@session_wrapper
def get_proxy_of_key(key, proxies):
    for url, info in proxies.items():
        if key in info.get("assigned_keys", []):
            return url
    return ""

@session_wrapper
def assign_proxy_to_key(proxy_display, api_key_display, proxies_state, api_keys_state):
    proxy_url = get_real_proxy_from_display(proxy_display, proxies_state)
    api_key = get_real_key_from_display(api_key_display, api_keys_state)
    proxies = proxies_state.copy()
    keys = api_keys_state.copy()
    if proxy_url not in proxies:
        return format_proxy_table(proxies), "❌ Proxy không tồn tại!", proxies, keys
    status = proxies[proxy_url].get("status", "")
    if not (status.startswith("✅") or "HTTPSConnectionPool" in status):
        return format_proxy_table(proxies), "❌ Proxy không hoạt động!", proxies, keys
    if api_key not in keys:
        return format_proxy_table(proxies), "❌ API Key không tồn tại!", proxies, keys
    for info in proxies.values():
        if api_key in info.get("assigned_keys", []):
            info["assigned_keys"].remove(api_key)
    proxies[proxy_url].setdefault("assigned_keys", []).append(api_key)
    return format_proxy_table(proxies), "✅ Đã gắn key.", proxies, keys

@session_wrapper
def smart_proxy_assignment(proxies_state, api_keys_state):
    proxies = proxies_state.copy()
    keys = api_keys_state.copy()
    active_proxies = []
    for url, info in proxies.items():
        status = info.get("status", "")
        if status.startswith("✅") or "HTTPSConnectionPool" in status:
            active_proxies.append((url, info))
    if not active_proxies:
        return [], list(keys.keys()), "⚠️ Không gắn proxy – Đang dùng IP thật (Vẫn ổn nếu xài dưới 3 Key/ngày).", proxies
    for url, info in proxies.items():
        info["assigned_keys"] = []
    key_list = list(keys.keys())
    random.shuffle(key_list)
    random.shuffle(active_proxies)
    num_keys = len(key_list)
    num_proxies = len(active_proxies)
    assigned_keys = []
    unassigned_keys = []
    if num_proxies >= num_keys:
        for i, key in enumerate(key_list):
            active_proxies[i][1]["assigned_keys"].append(key)
            assigned_keys.append(key)
        message = f"✅ Gắn 1:1, {len(assigned_keys)} key được gắn với {len(assigned_keys)} proxy, dư {num_proxies - num_keys} proxy."
    elif num_keys < 3 * num_proxies:
        keys_per_proxy_base = num_keys // num_proxies
        extra_keys = num_keys % num_proxies
        key_index = 0
        proxies_with_extra = 0
        proxies_normal = 0
        for i, (url, info) in enumerate(active_proxies):
            keys_for_this_proxy = keys_per_proxy_base + (1 if i < extra_keys else 0)
            for _ in range(keys_for_this_proxy):
                if key_index < len(key_list):
                    info["assigned_keys"].append(key_list[key_index])
                    assigned_keys.append(key_list[key_index])
                    key_index += 1
            if keys_for_this_proxy > keys_per_proxy_base:
                proxies_with_extra += 1
            else:
                proxies_normal += 1
        if extra_keys > 0:
            message = f"✅ Phân bổ hợp lý: {proxies_with_extra} proxy nhận {keys_per_proxy_base + 1} key, {proxies_normal} proxy nhận {keys_per_proxy_base} key."
        else:
            message = f"✅ Phân bổ đều: mỗi proxy nhận {keys_per_proxy_base} key."
    else:
        max_assignable = 3 * num_proxies
        keys_to_assign = key_list[:max_assignable]
        unassigned_keys = key_list[max_assignable:]
        key_index = 0
        for url, info in active_proxies:
            for _ in range(3):
                if key_index < len(keys_to_assign):
                    info["assigned_keys"].append(keys_to_assign[key_index])
                    assigned_keys.append(keys_to_assign[key_index])
                    key_index += 1
        message = f"✅ Mỗi proxy gắn 3 key, {len(assigned_keys)}/{num_keys} key được gắn."
        if unassigned_keys:
            message += f" ⚠️ {len(unassigned_keys)} key chưa gắn: {', '.join([mask_api_key(k) for k in unassigned_keys[:3]])}{'...' if len(unassigned_keys) > 3 else ''}"
    return assigned_keys, unassigned_keys, message, proxies

@session_wrapper
def auto_assign(proxies_state, api_keys_state):
    proxy_table, _, proxies = refresh_proxy_status(proxies_state)
    assigned_keys, unassigned_keys, message, proxies = smart_proxy_assignment(proxies, api_keys_state)
    return proxy_table, message, proxies

@session_wrapper
def delete_bad(proxies_state):
    proxies = proxies_state.copy()
    rem = []
    for u, i in list(proxies.items()):
        bad = i.get("status", "").startswith(("❌", "⚠️"))
        if bad:
            rem.append(u)
            proxies.pop(u)
    return format_proxy_table(proxies), f"🗑️ Đã xoá {len(rem)} proxy lỗi.", proxies

@session_wrapper
def filter_bad_proxies(proxies_state):
    proxies = proxies_state.copy()
    bad_proxies = {}
    for url, info in proxies.items():
        is_bad = info.get("status", "").startswith(("❌", "⚠️"))
        if is_bad:
            bad_proxies[url] = info
    return format_proxy_table(bad_proxies)

# === Voice helpers ===
@session_wrapper
def get_voice_list(voices_state):
    return list(voices_state.keys())

@session_wrapper
def get_default_voice(voices_state):
    lst = get_voice_list(voices_state)
    return lst[0] if lst else None

@session_wrapper
def save_voice(name, voice_id, current_voice, voices_state):
    try:
        if not name or not voice_id:
            return "❌ Cần nhập tên và ID!", get_voice_list(voices_state), get_voice_list(voices_state), current_voice, voices_state
        voices = voices_state.copy()
        for n, v in voices.items():
            if v.get("voice_id") == voice_id and n != name:
                return f"❌ Voice ID đã tồn tại ở '{n}'.", get_voice_list(voices), get_voice_list(voices), current_voice, voices
        voices[name] = {"voice_id": voice_id, "settings": DEFAULT_VOICE_SETTINGS.copy()}
        vl = get_voice_list(voices)
        return f"✅ Đã lưu '{name}'", vl, vl, name, voices
    except Exception as e:
        msg = log_exception(e, "save_voice")
        return msg, get_voice_list(voices_state), get_voice_list(voices_state), current_voice, voices_state

@session_wrapper
def load_voice_for_edit(name, voices_state):
    voices = voices_state.copy()
    v = voices.get(name, {})
    cfg = v.get("settings", DEFAULT_VOICE_SETTINGS.copy())
    if not name:
        return "", "", *DEFAULT_VOICE_SETTINGS.values()
    voice_id = v.get("voice_id", "")
    masked_voice_id = mask_voice_id(voice_id)
    return name, masked_voice_id, cfg["speed"], cfg["stability"], cfg["similarity_boost"], cfg["style_exaggeration"], cfg["use_speaker_boost"]

@session_wrapper
def delete_voice(name, confirm, cur, voices_state):
    if not name:
        return "❌ Chọn voice!", get_voice_list(voices_state), get_voice_list(voices_state), cur, voices_state
    if not confirm:
        return "⚠️ Hãy tick vào ô xác nhận xoá!", get_voice_list(voices_state), get_voice_list(voices_state), cur, voices_state
    voices = voices_state.copy()
    protected_voice_ids = {
        "TxGEqnHWrfWFTfGW9XjX", "TX3LPaxmHKxFdv7VOQHJ", "ErXwobaYiN019PkySvjV",
        "iP95p4xoKVk53GoZ742B", "VR6AewLTigWG4xSOukaG", "pNInz6obpgDQGcFmaJgB",
        "nPczCjzI2devNBz1zQrb", "CwhRBWXzGAHq8TQ4Fs17", "5Q0t7uMcjvnagumLfvZi",
        "29vD33N1CtxCmqQRPOHJ", "flq6f7yk4E4fJM5XTYuZ", "t0jbNlBVZ17f02VDIeMI",
        "pqHfZKP75CvOlQylNhV4", "LcfcDJNUP1GQjkzn1xUU", "z9fAnlkpzviPz146aGWa",
        "pMsXgVXv3BLzUgSXRplE", "XrExE9yKIg1WjnnlVkGX", "SAz9YHcvj6GT2YYXdXww",
        "N2lVS1w4EtoT3dr4eOWO", "2EiwWnXFnvU5JabPnv8n", "p28fY1cl6tovhD2M4WEH",
        "eC5XQ2bYx6LQHFG29bNv"
    }
    voice_info = voices.get(name)
    if voice_info and voice_info.get("voice_id") in protected_voice_ids:
        return "❌ Không được xoá voice mặc định!", get_voice_list(voices), get_voice_list(voices), cur, voices
    if name in voices:
        voices.pop(name)
        lst = get_voice_list(voices)
        new = lst[0] if lst else None
        return f"🗑️ Đã xoá '{name}'", lst, lst, new, voices
    return "❌ Không tìm thấy voice!", get_voice_list(voices), get_voice_list(voices), cur, voices

@session_wrapper
def reset_voice(name, confirm, cur, voices_state):
    if not name:
        return "❌ Chọn voice!", get_voice_list(voices_state), get_voice_list(voices_state), cur, voices_state
    if not confirm:
        return "⚠️ Hãy tick vào ô xác nhận reset!", get_voice_list(voices_state), get_voice_list(voices_state), cur, voices_state
    voices = voices_state.copy()
    if name in voices:
        voices[name]["settings"] = DEFAULT_VOICE_SETTINGS.copy()
        return f"✅ Đã reset '{name}'", get_voice_list(voices), get_voice_list(voices), name, voices
    return "❌ Không tìm thấy voice!", get_voice_list(voices), get_voice_list(voices), cur, voices

@session_wrapper
def update_voice_cfg(name, speed, stab, sim, exag, boost, cur, voices_state):
    if not name:
        return "❌ Chọn voice!", get_voice_list(voices_state), get_voice_list(voices_state), cur, voices_state
    voices = voices_state.copy()
    voices.setdefault(name, {"voice_id": "", "settings": DEFAULT_VOICE_SETTINGS.copy()})
    voices[name]["settings"] = {
        "speed": speed,
        "stability": stab,
        "similarity_boost": sim,
        "style_exaggeration": exag,
        "use_speaker_boost": boost
    }
    return f"✅ Đã cập nhật '{name}'", get_voice_list(voices), get_voice_list(voices), name, voices

@session_wrapper
def voice_table(voices_state):
    voices = voices_state.copy()
    data = [[n, mask_voice_id(v.get("voice_id", "")), "✅" if v.get("settings") else "❌"] for n, v in voices.items()]
    return pd.DataFrame(data, columns=["Tên Voice", "Voice ID", "Đã cấu hình"])

# === API-Key helpers ===
@session_wrapper
def dataframe_with_keys(api_keys_state, proxies_state):
    keys = api_keys_state.copy()
    proxies = proxies_state.copy()
    rows = []
    for k, v in keys.items():
        masked_key = mask_api_key(k)
        rows.append([masked_key, v.get("status", ""), v.get("used", 0), v.get("limit", 0), v.get("tier", ""), v.get("remaining", 0), proxy_host(get_proxy_of_key(k, proxies))])
    df = pd.DataFrame(rows, columns=["API Key", "Status", "Used", "Limit", "Tier", "Remaining", "Proxy Host"])
    df = df.sort_values("Remaining", ascending=True)
    return df

@session_wrapper
def get_sorted_keys_by_credit(api_keys_state):
    keys = api_keys_state.copy()
    if not keys:
        return []
    sorted_keys = sorted(keys.items(), key=lambda x: x[1].get("remaining", 0))
    return [k for k, v in sorted_keys]

@session_wrapper
def lowest_key(api_keys_state):
    keys = api_keys_state.copy()
    if not keys:
        return None
    return sorted(keys.items(), key=lambda x: x[1].get("remaining", float("inf")))[0][0]

@session_wrapper
def save_and_show_keys(text, api_keys_state, proxies_state):
    # --- Copy state hiện tại ---
    keys = api_keys_state.copy()
    proxies = proxies_state.copy()

    # --- Đọc input, thu list new_keys ---
    new_keys = []
    for line in text.strip().splitlines():
        k = line.strip()
        if k and k not in keys:
            new_keys.append(k)

    # --- Nhánh 1: nếu không có key mới ---
    if not new_keys:
        df = dataframe_with_keys(keys, proxies)
        message = "ℹ️ Không có key mới nào."
        choices = get_key_choices_for_display(keys)
        lowest = choices[0] if choices else None

        return (
            # Tab 2 outputs: key_df, key_dd, key_del_dd, key_sel, status_out, api_keys_state, total_credit_txt
            df,
            gr.update(choices=choices, value=lowest),  # dropdown “Chọn API Key”
            gr.update(choices=choices, value=None),    # dropdown “Chọn API Key để xoá”
            gr.update(choices=choices, value=None),    # dropdown “API Key”
            message,
            keys,
            f"Tổng credit: {total_credit(keys):,}"
        )

    # --- Nhánh 2: có new_keys -> thêm vào state ---
    added = len(new_keys)
    for k in new_keys:
        keys[k] = {"status": "⏳ Chưa kiểm tra", "remaining": 0}

    # Gán proxy và kiểm tra usage cho các key mới
    assigned_keys, unassigned_keys, assign_message, proxies = smart_proxy_assignment(proxies, keys)
    checked = 0
    for k in new_keys:
        if k in assigned_keys:
            keys[k] = get_api_usage(k, proxies=proxies)
            checked += 1
        else:
            if not proxies:
                keys[k] = get_api_usage(k, bypass_proxy=True, proxies=proxies)
                checked += 1
            else:
                keys[k]["status"] = "⚠️ Chưa gắn proxy"
    
    active_proxies = [
        p for p in proxies.values()
        if p.get("status", "").startswith("✅") or "HTTPSConnectionPool" in p.get("status", "")
    ]
    if not active_proxies:
        assign_message += " ⚠️ Không có proxy – Đang dùng IP thật (Vẫn ổn nếu xài dưới 3 key/ngày)"

    # Build kết quả
    df = dataframe_with_keys(keys, proxies)
    if not active_proxies:
        assign_message = "⚠️ Không gắn proxy – Đang dùng IP thật (Vẫn ổn nếu xài dưới 3 Key/ngày)"
    message = f"✅ Thêm {added} key mới, kiểm tra {checked} key. {assign_message}"
    choices = get_key_choices_for_display(keys)
    lowest = choices[0] if choices else None

    return (
        # Tab 2 outputs: key_df, key_dd, key_del_dd, key_sel, status_out, api_keys_state, total_credit_txt
        df,
        gr.update(choices=choices, value=lowest),  # dropdown “Chọn API Key”
        gr.update(choices=choices, value=None),    # dropdown “Chọn API Key để xoá”
        gr.update(choices=choices, value=None),    # dropdown “API Key”
        message,
        keys,
        f"Tổng credit: {total_credit(keys):,}"
    )

@session_wrapper
def refresh_keys(api_keys_state, proxies_state):
    keys = api_keys_state.copy()
    for k in keys:
        keys[k] = get_api_usage(k, proxies=proxies_state)
    df = dataframe_with_keys(keys, proxies_state)
    choices = get_key_choices_for_display(keys)
    lowest = choices[0] if choices else None
    return (
      df,
      gr.update(choices=choices, value=lowest),  # an toàn ngay cả khi choices = []
      f"Tổng credit: {total_credit(keys):,}",
      gr.update(choices=choices, value=None),
      keys
    )
@session_wrapper
def filter_api_keys_by_credit(threshold, api_keys_state, proxies_state):
    keys = api_keys_state.copy()
    filtered = {k: v for k, v in keys.items() if v.get("remaining", 0) < threshold}
    rows = []
    for k, v in filtered.items():
        masked_key = mask_api_key(k)
        rows.append([masked_key, v.get("status", ""), v.get("used", 0), v.get("limit", 0), v.get("tier", ""), v.get("remaining", 0), proxy_host(get_proxy_of_key(k, proxies_state))])
    df = pd.DataFrame(rows, columns=["API Key", "Status", "Used", "Limit", "Tier", "Remaining", "Proxy Host"])
    return df

def remove_insufficient_keys(threshold, api_keys_state, proxies_state):
    keys = api_keys_state.copy()
    filtered = {k: v for k, v in keys.items() if v.get("remaining", 0) >= threshold}
    choices = get_key_choices_for_display(filtered)
    lowest = choices[0] if choices else None
    return (
        dataframe_with_keys(filtered, proxies_state),
        gr.update(choices=choices, value=lowest),
        gr.update(choices=choices, value=None),
        gr.update(choices=choices, value=None),
        filtered
    )
@session_wrapper
def key_has_proxy(k, proxies_state):
    return bool(get_proxy_of_key(k, proxies_state))

@session_wrapper
def tts_from_text(text, voice, model, fmt, key_display, auto, bypass_proxy, voices_state, api_keys_state, proxies_state):
    if not text.strip():
        return None, "Nội dung trống!", "", api_keys_state
    keys = api_keys_state.copy()
    proxies = proxies_state.copy()
    voices = voices_state.copy()
    tokens = len(text)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    if auto:
        if bypass_proxy:
            c = [(k, v["remaining"]) for k, v in keys.items() if v.get("remaining", 0) >= tokens]
        else:
            c = [(k, v["remaining"]) for k, v in keys.items() if v.get("remaining", 0) >= tokens and key_has_proxy(k, proxies)]
            if not c:
                c = [(k, v["remaining"]) for k, v in keys.items() if v.get("remaining", 0) >= tokens]
                bypass_proxy = True  # chuyển sang dùng IP thật
        if not c:
            return None, "❌ Không có key đủ credit", "", keys
        api_key = sorted(c, key=lambda x: x[1])[0][0]
    else:
        if not key_display:
            return None, "❌ Chưa chọn key", "", keys
        api_key = get_real_key_from_display(key_display, keys)
        if not bypass_proxy and not key_has_proxy(api_key, proxies):
            return None, "❌ Key chưa gắn proxy", "", keys
    proxy_url = None if bypass_proxy else get_proxy_of_key(api_key, proxies)
    try:
        info = voices.get(voice, {})
        if not info:
            return None, "❌ Voice không tồn tại", "", keys
        payload = {
            "text": text,
            "voice_settings": info.get("settings", DEFAULT_VOICE_SETTINGS),
            "model_id": model
        }
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{info.get('voice_id')}"
        proxies_dict = None
        if not bypass_proxy and proxy_url:
            proxies_dict = {"http": proxy_url, "https": proxy_url}
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            proxies=proxies_dict,
            timeout=30,
            verify=False if proxies_dict else True
        )
        if response.status_code != 200:
            error_detail = response.text
            if response.status_code == 401 and "detected_unusual_activity" in error_detail:
                return None, f"❌ Key {mask_api_key(api_key)} bị chặn 'unusual activity'.", "", keys
            else:
                return None, f"❌ API Error {response.status_code}: {error_detail[:100]}", "", keys
        ext = fmt.split('_')[0] if '_' in fmt else fmt
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        filename = f"tts_{timestamp}_{unique_id}.{ext}"
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        if not os.path.exists(file_path):
            return None, "❌ Không thể tạo file audio", "", keys
        keys[api_key] = get_api_usage(api_key, bypass_proxy, proxies)
        proxy_status = "🔓 Direct" if bypass_proxy or not proxy_url else f"🛡️ Proxy"
        success_msg = f"✅ Tạo {tokens} ký tự bằng key {mask_api_key(api_key)} ({proxy_status})"
        credit_msg = f"Tổng credit: {total_credit(keys):,}"
        return file_path, success_msg, credit_msg, keys
    except Exception as e:
        error_msg = str(e)
        if "ProxyError" in error_msg or "ConnectError" in error_msg:
            return None, f"❌ Lỗi kết nối proxy: {mask_proxy_url(proxy_url)}", "", keys
        else:
            return None, f"❌ Lỗi: {error_msg[:100]}", "", keys

@session_wrapper
def verify_key_proxy(key_display, api_keys_state, proxies_state):
    api_key = get_real_key_from_display(key_display, api_keys_state)
    proxy = get_proxy_of_key(api_key, proxies_state)
    if not proxy:
        return "🔴 Key chưa gắn proxy!"
    proxies = {"http": proxy, "https": proxy}
    try:
        r = requests.get("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": api_key}, proxies=proxies, timeout=8)
        ip = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=6).json().get("ip", "-")
        return f"{'✅' if r.status_code == 200 else '❌'} ElevenLabs {r.status_code} | IP via proxy: {ip}"
    except Exception as e:
        return f"❌ Lỗi: {str(e).split(' ')[0]}"

# === Refresh-all ===
@session_wrapper
def refresh_all(voices_state, api_keys_state, proxies_state):
    voices = voices_state.copy()
    keys = api_keys_state.copy()
    proxies = proxies_state.copy()
    voice_list = get_voice_list(voices)
    key_df     = dataframe_with_keys(keys, proxies)
    proxy_df   = format_proxy_table(proxies)
    sorted_keys = get_key_choices_for_display(keys)
    proxy_list  = get_proxy_choices_for_display(proxies)
    total_credit_msg = f"Tổng credit: {total_credit(keys):,}"
    lowest = sorted_keys[0] if sorted_keys else None
    return (
        voice_list,
        voice_list,
        gr.update(choices=sorted_keys, value=lowest),
        gr.update(choices=sorted_keys, value=None),
        gr.update(choices=sorted_keys, value=None),
        proxy_list,
        total_credit_msg,
        key_df,
        proxy_df,
        voices,
        keys,
        proxies,
    )
@session_wrapper
def refresh_keys_complete(api_keys_state, proxies_state):
    keys = api_keys_state.copy()
    for k in keys:
        keys[k] = get_api_usage(k, proxies=proxies_state)
    key_df = dataframe_with_keys(keys, proxies_state)
    sorted_keys = get_key_choices_for_display(keys)
    total_credit_msg = f"Tổng credit: {total_credit(keys):,}"
    lowest = sorted_keys[0] if sorted_keys else None
    return (
        key_df,
        gr.update(choices=sorted_keys, value=lowest),  # “Chọn API Key”
        gr.update(choices=sorted_keys, value=None),    # “Chọn API Key để xoá”
        gr.update(choices=sorted_keys, value=None),    # “API Key”
        total_credit_msg,
        lowest,
        keys
    )
@session_wrapper
def refresh_proxies_complete(proxies_state, api_keys_state):
    proxies = proxies_state.copy()
    for url in proxies:
        proxies[url].update(test_proxy_once(url))
        proxies[url]["last_checked"] = datetime.utcnow().isoformat(timespec="seconds")
    keys = api_keys_state.copy()
    key_df = dataframe_with_keys(keys, proxies)
    proxy_df = format_proxy_table(proxies)
    proxy_list = get_proxy_choices_for_display(proxies)
    return proxy_df, "🔄 Đã refresh proxy.", proxy_list, key_df, proxies

@session_wrapper
def refresh_voices_complete(voices_state):
    voices = voices_state.copy()
    voice_list = get_voice_list(voices)
    voice_df = voice_table(voices)
    return voice_list, voice_list, voice_df, voices

# === UI ===
with gr.Blocks() as demo:
    voices_state = gr.State(load_default_voices())
    api_keys_state = gr.State({})
    proxies_state = gr.State(load_default_proxies())

    gr.Markdown("""
    > 🟢 **Công cụ này hoàn toàn MIỄN PHÍ cho tất cả mọi người.**  
    > ❌ Vui lòng KHÔNG rao bán, đổi tên hay thương mại hoá công cụ.  
    > 🛡️ Mọi dữ liệu (API key, proxy) chỉ lưu tạm trong phiên, tự xóa khi đóng trình duyệt.
    """)
    gr.Markdown("# 🎙️ ElevenLabs TTS + Proxy Manager")
    with gr.Tabs():
        with gr.Tab("1. Xử lý Batch"):
            with gr.Row():
                voice_dd = gr.Dropdown(choices=get_voice_list(voices_state.value), value=get_default_voice(voices_state.value), label="Chọn Voice", allow_custom_value=True)
                model_dd = gr.Dropdown(choices=MODELS, value=DEFAULT_MODEL, label="Model")
                fmt_dd = gr.Dropdown(choices=["mp3_44100", "wav"], value=DEFAULT_FORMAT, label="Output")
            with gr.Row():
                key_dd = gr.Dropdown(choices=get_key_choices_for_display(api_keys_state.value), value=None, label="Chọn API Key", allow_custom_value=True)
                key_credit = gr.Text(label="Credit hiện còn", interactive=False)
                total_credit_txt = gr.Text(label="Tổng Credit", interactive=False)
            def update_key_credit(display_key, api_keys_state):
                if not display_key:
                    return "-"
                if isinstance(display_key, list):
                    display_key = display_key[0] if display_key else ""
                real_key = get_real_key_from_display(display_key, api_keys_state)
                remaining = api_keys_state.get(real_key, {}).get('remaining', '-')
                if isinstance(remaining, (int, float)):
                    return f"{remaining:,}"
                return str(remaining)
            key_dd.change(update_key_credit, [key_dd, api_keys_state], key_credit)
            refresh_all_btn = gr.Button("🔄 Refresh All")
            verify_btn = gr.Button("⚡ Kiểm tra Proxy của API Key")
            status_out = gr.Text(label="Trạng thái")
            input_txt = gr.Textbox(lines=6, label="Nội dung")
            token_info = gr.Text(label="Tổng ký tự")
            input_txt.change(lambda t: f"{len(t)} ký tự", input_txt, token_info)
            auto_cb = gr.Checkbox(value=True, label="Tự động chọn API Key có gắn proxy")
            bypass_proxy_cb = gr.Checkbox(value=False, label="🔓 Tạm thời không dùng proxy (bypass)")
            generate_btn = gr.Button("🌀 Tạo giọng nói")
            audio_out = gr.Audio(label="Kết quả", type="filepath")
        with gr.Tab("2. Quản lý API Key"):
            api_in = gr.Textbox(lines=4, label="Nhập API Key (mỗi dòng)")
            save_key_btn = gr.Button("📅 Lưu & Kiểm tra")
            refresh_key_btn = gr.Button("🔄 Refresh danh sách")
            key_df = gr.Dataframe(label="Danh sách API Key", interactive=False)
            gr.Markdown("### Xoá API Key thủ công")
            key_del_dd = gr.Dropdown(choices=get_key_choices_for_display(api_keys_state.value), value=None, label="Chọn API Key để xoá", allow_custom_value=True)
            key_del_btn = gr.Button("🗑️ Xoá API Key đã chọn")
            gr.Markdown("### Lọc API Key theo Credit")
            filter_input = gr.Number(label="Lọc các API Key có số credit dưới", value=100)
            filter_btn = gr.Button("🔍 Lọc API Key")
            remove_low_btn = gr.Button("❌ Xoá các key không đủ credit")
        with gr.Tab("3. Quản lý Voice ID"):
            with gr.Row():
                v_name = gr.Textbox(label="Tên Voice")
                v_id = gr.Textbox(label="Voice ID")
                v_select = gr.Dropdown(choices=get_voice_list(voices_state.value), value=get_default_voice(voices_state.value), label="Chọn Voice để sửa", allow_custom_value=True)
            voice_status = gr.Textbox(label="Trạng thái", interactive=False)
            with gr.Row():
                save_voice_btn = gr.Button("💾 Lưu Voice mới")
            with gr.Row():
                del_voice_btn = gr.Button("🗑️ Xoá Voice đang chọn")
            with gr.Row():
                speed_sl = gr.Slider(0.70, 1.20, DEFAULT_VOICE_SETTINGS["speed"], step=0.01, label="Speed")
                stab_sl = gr.Slider(0, 1, DEFAULT_VOICE_SETTINGS["stability"], step=0.05, label="Stability")
                sim_sl = gr.Slider(0, 1, DEFAULT_VOICE_SETTINGS["similarity_boost"], step=0.05, label="Similarity")
                ex_sl = gr.Slider(0, 1, DEFAULT_VOICE_SETTINGS["style_exaggeration"], step=0.05, label="Exaggeration")
                boost_cb = gr.Checkbox(value=True, label="Speaker Boost")
            upd_cfg_btn = gr.Button("💾 Lưu cấu hình Voice")
            reset_cfg_btn = gr.Button("↻ Reset cấu hình Voice")
            refresh_v_btn = gr.Button("🔄 Làm mới danh sách Voice")
            with gr.Row():
                reset_confirm_cb = gr.Checkbox(value=False, label="Đồng ý reset về mặc định")
                gr.HTML("")
                delete_confirm_cb = gr.Checkbox(value=False, label="Đồng ý xoá voice")
            voice_df = gr.Dataframe(label="Danh sách Voice", interactive=False)
        with gr.Tab("4. Quản lý Proxy"):
            proxy_in = gr.Textbox(lines=4, label="Nhập proxy (mỗi dòng | http://user:pass@host:port)")
            add_p_btn = gr.Button("💾 Lưu & Kiểm tra")
            refresh_p_btn = gr.Button("🔄 Refresh trạng thái")
            proxy_df = gr.Dataframe(label="Danh sách Proxy", interactive=False)
            p_status = gr.Text(label="Trạng thái")
            gr.Markdown("### Xoá Proxy thủ công")
            proxy_del_dd = gr.Dropdown(choices=get_proxy_choices_for_display(proxies_state.value), value=None, label="Chọn Proxy để xoá", allow_custom_value=True)
            proxy_del_btn = gr.Button("🗑️ Xoá Proxy đã chọn")
            gr.Markdown("### Gắn Proxy với API Key")
            with gr.Row():
                proxy_sel = gr.Dropdown(choices=get_proxy_choices_for_display(proxies_state.value), value=None, label="Proxy", allow_custom_value=True)
                key_sel = gr.Dropdown(choices=get_key_choices_for_display(api_keys_state.value), value=None, label="API Key", allow_custom_value=True)
            assign_btn = gr.Button("↔️ Gắn thủ công")
            auto_btn = gr.Button("🤖 Gắn tự động thông minh")
            filter_bad_btn = gr.Button("🔍 Lọc Proxy lỗi")
            del_bad_btn = gr.Button("🗑️ Xoá Proxy lỗi")

    # Events setup
    @session_wrapper
    def delete_api_key_manual(display_key, api_keys_state, proxies_state):
        if not display_key:
            return dataframe_with_keys(api_keys_state, proxies_state), get_key_choices_for_display(api_keys_state), get_key_choices_for_display(api_keys_state), get_key_choices_for_display(api_keys_state), "❌ Chọn API Key để xoá!", api_keys_state
        real_key = get_real_key_from_display(display_key, api_keys_state)
        keys = api_keys_state.copy()
        if real_key in keys:
            del keys[real_key]
        key_list = get_key_choices_for_display(keys)
        return (
          dataframe_with_keys(keys, proxies_state),
          gr.update(choices=key_list, value=key_list[0]),  # key_dd
          gr.update(choices=key_list, value=None),         # key_del_dd
          gr.update(choices=key_list, value=None),         # key_sel
          f"🗑️ Đã xoá key: {display_key}",
          keys
        )

    @session_wrapper
    def delete_proxy_manual(display_proxy, proxies_state):
        if not display_proxy:
            return format_proxy_table(proxies_state), get_proxy_choices_for_display(proxies_state), "❌ Chọn Proxy để xoá!", proxies_state
        real_proxy = get_real_proxy_from_display(display_proxy, proxies_state)
        proxies = proxies_state.copy()
        if real_proxy in proxies:
            del proxies[real_proxy]
        proxy_list = get_proxy_choices_for_display(proxies)
        return format_proxy_table(proxies), proxy_list, f"🗑️ Đã xoá proxy: {display_proxy}", proxies

    @session_wrapper
    def update_proxy_and_sync(text, proxies_state):
        proxy_table, message, proxies = add_and_test_proxies(text, proxies_state)
        proxy_choices = get_proxy_choices_for_display(proxies)
        return proxy_table, message, proxy_choices, proxies

    @session_wrapper
    def auto_assign_and_sync(proxies_state, api_keys_state):
        proxy_df_result, message, proxies = auto_assign(proxies_state, api_keys_state)
        proxies_choices = get_proxy_choices_for_display(proxies)
        sorted_keys = get_key_choices_for_display(api_keys_state)
        api_key_df = dataframe_with_keys(api_keys_state, proxies)
        return proxy_df_result, message, proxies_choices, sorted_keys, api_key_df, proxies

    @session_wrapper
    def assign_manual_and_sync(proxy_display, key_display, proxies_state, api_keys_state):
        proxy_df_result, message, proxies, keys = assign_proxy_to_key(proxy_display, key_display, proxies_state, api_keys_state)
        api_key_df = dataframe_with_keys(keys, proxies)
        return proxy_df_result, message, api_key_df, proxies, keys

    @session_wrapper
    def delete_bad_and_sync(proxies_state):
        proxy_table, message, proxies = delete_bad(proxies_state)
        proxies_choices = get_proxy_choices_for_display(proxies)
        return proxy_table, message, proxies_choices, proxies

    # Gắn sự kiện
    key_del_btn.click(
        delete_api_key_manual,
        [key_del_dd, api_keys_state, proxies_state],
        [key_df, key_dd, key_del_dd, key_sel, status_out, api_keys_state]
    )
    proxy_del_btn.click(
        delete_proxy_manual,
        [proxy_del_dd, proxies_state],
        [proxy_df, proxy_del_dd, p_status, proxies_state]
    )
    save_key_btn.click(
        fn=save_and_show_keys,
        inputs=[api_in, api_keys_state, proxies_state],
        outputs=[key_df, key_dd, key_del_dd, key_sel, status_out, api_keys_state, total_credit_txt]
    )
    refresh_key_btn.click(
        refresh_keys,
        [api_keys_state, proxies_state],
        [key_df, key_dd, total_credit_txt, key_sel, api_keys_state]
    )
    filter_btn.click(
        filter_api_keys_by_credit,
        [filter_input, api_keys_state, proxies_state],
        key_df
    )
    remove_low_btn.click(
        remove_insufficient_keys,
        [filter_input, api_keys_state, proxies_state],
        [key_df, key_dd, key_del_dd, key_sel, api_keys_state]
    )
    refresh_all_btn.click(
        refresh_all,
        [voices_state, api_keys_state, proxies_state],
        [voice_dd, v_select, key_dd, key_del_dd, key_sel, proxy_sel, total_credit_txt, key_df, proxy_df, voices_state, api_keys_state, proxies_state]
    )
    verify_btn.click(
        verify_key_proxy,
        [key_dd, api_keys_state, proxies_state],
        status_out
    )
    generate_btn.click(
        tts_from_text,
        [input_txt, voice_dd, model_dd, fmt_dd, key_dd, auto_cb, bypass_proxy_cb, voices_state, api_keys_state, proxies_state],
        [audio_out, status_out, total_credit_txt, api_keys_state]
    )
    def save_voice_and_refresh(name, voice_id, current_voice, voices_state):
        status, v_select_choices, voice_dd_choices, selected_voice, new_voices_state = save_voice(
            name, voice_id, current_voice, voices_state
        )
        voice_df_data = voice_table(new_voices_state)
        voice_dd_update = gr.update(choices=get_voice_list(new_voices_state), value=get_default_voice(new_voices_state))
        return status, v_select_choices, voice_dd_update, selected_voice, new_voices_state, voice_df_data
    save_voice_btn.click(
        save_voice_and_refresh,
        [v_name, v_id, v_select, voices_state],
        [voice_status, v_select, voice_dd, v_select, voices_state, voice_df]
    )
    v_select.change(
        load_voice_for_edit,
        [v_select, voices_state],
        [v_name, v_id, speed_sl, stab_sl, sim_sl, ex_sl, boost_cb]
    )
    def update_voice_cfg_and_refresh(name, speed, stab, sim, exag, boost, cur, voices_state):
        status, v_select_choices, voice_dd_choices, selected_voice, new_voices_state = update_voice_cfg(
            name, speed, stab, sim, exag, boost, cur, voices_state
        )
        voice_df_data = voice_table(new_voices_state)
        return status, v_select_choices, voice_dd_choices, selected_voice, new_voices_state, voice_df_data
    upd_cfg_btn.click(
        update_voice_cfg_and_refresh,
        [v_select, speed_sl, stab_sl, sim_sl, ex_sl, boost_cb, v_select, voices_state],
        [voice_status, v_select, voice_dd, v_select, voices_state, voice_df]
    )
    def reset_voice_and_refresh(name, confirm, cur, voices_state):
        status, v_select_choices, voice_dd_choices, selected_voice, new_voices_state = reset_voice(
            name, confirm, cur, voices_state
        )
        voice_df_data = voice_table(new_voices_state)
        voice_dd_update = gr.update(choices=get_voice_list(new_voices_state), value=get_default_voice(new_voices_state))
        return status, v_select_choices, voice_dd_update, selected_voice, new_voices_state, voice_df_data
    reset_cfg_btn.click(
        reset_voice_and_refresh,
        [v_select, reset_confirm_cb, v_select, voices_state],
        [voice_status, v_select, voice_dd, v_select, voices_state, voice_df]
    )
    refresh_v_btn.click(
        refresh_voices_complete,
        voices_state,
        [v_select, voice_dd, voice_df, voices_state]
    )
    def del_voice_and_refresh(name, confirm, cur, voices_state):
        status, v_select_choices, voice_dd_choices, selected_voice, new_voices_state = delete_voice(
            name, confirm, cur, voices_state
        )
        voice_df_data = voice_table(new_voices_state)
        voice_dd_update = gr.update(choices=get_voice_list(new_voices_state), value=get_default_voice(new_voices_state))
        return status, v_select_choices, voice_dd_update, selected_voice, new_voices_state, voice_df_data
    del_voice_btn.click(
        del_voice_and_refresh,
        [v_select, delete_confirm_cb, v_select, voices_state],
        [voice_status, v_select, voice_dd, v_select, voices_state, voice_df]
    )
    def add_proxy_and_refresh(text, proxies_state):
        proxy_table, message, new_proxies_state = add_and_test_proxies(text, proxies_state)
        proxy_sel_update = gr.update(choices=get_proxy_choices_for_display(new_proxies_state), value=None)
        proxy_del_dd_update = gr.update(choices=get_proxy_choices_for_display(new_proxies_state), value=None)
        return proxy_table, message, proxy_sel_update, new_proxies_state, proxy_del_dd_update
    add_p_btn.click(
        add_proxy_and_refresh,
        [proxy_in, proxies_state],
        [proxy_df, p_status, proxy_sel, proxies_state, proxy_del_dd]
    )
    refresh_p_btn.click(
        refresh_proxies_complete,
        [proxies_state, api_keys_state],
        [proxy_df, p_status, proxy_sel, key_df, proxies_state]
    )
    assign_btn.click(
        assign_manual_and_sync,
        [proxy_sel, key_sel, proxies_state, api_keys_state],
        [proxy_df, p_status, key_df, proxies_state, api_keys_state]
    )
    auto_btn.click(
        auto_assign_and_sync,
        [proxies_state, api_keys_state],
        [proxy_df, p_status, proxy_sel, key_sel, key_df, proxies_state]
    )
    filter_bad_btn.click(
        filter_bad_proxies,
        proxies_state,
        proxy_df
    )
    del_bad_btn.click(
        delete_bad_and_sync,
        proxies_state,
        [proxy_df, p_status, proxy_sel, proxies_state]
    )
    demo.load(
        voice_table,
        voices_state,
        voice_df
    )
    demo.load(
        dataframe_with_keys,
        [api_keys_state, proxies_state],
        key_df
    )
    demo.load(
        format_proxy_table,
        proxies_state,
        proxy_df
    )
    demo.load(
        lambda api_keys: f"Tổng credit: {total_credit(api_keys):,}",
        api_keys_state,
        total_credit_txt
    )

demo.launch(ssr_mode=False)