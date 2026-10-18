import os
import json
import time
import urllib.request
import urllib.error

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def fetch_live_github_bounties():
    queries = [
        "solana+label:bounty+state:open",
        "solana+good-first-issue+state:open"
    ]
    headers = {"User-Agent": "Hermes-Agent"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    collected = []
    for q in queries:
        url = f"https://api.github.com/search/issues?q={q}&sort=created&order=desc&per_page=3"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("items", []):
                    title = item.get("title", "").strip()
                    html_url = item.get("html_url", "")
                    body = (item.get("body") or "")[:250].replace("\n", " ").strip()
                    collected.append(f"- {title} ({html_url}): {body}")
        except Exception as e:
            print(f"Помилка парсингу GitHub ({q}): {e}")
        time.sleep(1)

    return "\n".join(collected[:4]) if collected else "Реальні баунті тимчасово недоступні."

def call_gemini(system_role, prompt, max_retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"SYSTEM ROLE: {system_role}\n\nTASK: {prompt}"}
                ]
            }
        ]
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                time.sleep(attempt * 4)
                continue
            raise
        except Exception:
            if attempt < max_retries:
                time.sleep(attempt * 4)
                continue
            raise

def send_telegram(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram keys missing. Output:\n" + str(message))
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

    # Розбиваємо на частини по 3900 символів, щоб гарантовано проходило ліміти
    chunks = []
    text = str(message)
    while text:
        if len(text) <= 3900:
            chunks.append(text)
            break
        split_idx = text.rfind("\n", 0, 3900)
        if split_idx == -1:
            split_idx = 3900
        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()

    for idx, chunk in enumerate(chunks, 1):
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": True
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"Telegram chunk {idx}/{len(chunks)} sent: {resp.status}")
        except Exception as e:
            print(f"Telegram chunk {idx} failed: {e}")
        time.sleep(0.5)

def run_hermes_autonomous_cycle():
    print("[0] Ingest: Отримання живих даних із GitHub...")
    live_context = fetch_live_github_bounties()
    print("Знайдені завдання:\n", live_context)

    print("[1] Scout: Аналіз реальних баунті та вибір цілі...")
    task_prompt = (
        f"Ось актуальні відкриті завдання/баунті з GitHub за сьогодні:\n{live_context}\n\n"
        "Обери 1 найперспективніше конкретне завдання з переліку (або сформуй точне мікро-рішення під ці проблеми). "
        "Поясни: що це, пряме посилання на задачу, чому воно перспективне і орієнтовна винагорода/цінність."
    )
    task = call_gemini("Ти провідний аналітик Web3 та скаут GitHub баунті.", task_prompt)
    time.sleep(2)

    print("[2] Worker: Розробка технічного рішення...")
    worker_role = "Ти Senior Web3 Engineer. Напиши лаконічне технічне рішення, алгоритм або архітектуру коду."
    draft = call_gemini(worker_role, f"Завдання:\n{task}\n\nСтвори технічний опис або готовий код/патч для вирішення.")
    time.sleep(2)

    print("[3] Critic: Аудит та перевірка слабких місць...")
    critic_role = "Ти суворий QA-лідер та аудит смарт-контрактів/коду. Вкажи на 2 критичні недоліки або ризики цього рішення."
    critique = call_gemini(critic_role, f"Рішення:\n{draft}\n\nЗроби критичний аудит.")
    time.sleep(2)

    print("[4] Worker: Фінальний варіант...")
    final_solution = call_gemini(worker_role, f"Ось початкове рішення:\n{draft}\n\nОсь зауваження аудитора:\n{critique}\n\nСформуй фінальне, виправлене резюме рішення з чіткими інструкціями.")

    report = (
        "🚀 Hermes Scout 2.0: Живі баунті Web3\n\n"
        f"🎯 Обране реальне завдання:\n{task}\n\n"
        f"🔍 Аудит (Critic):\n{critique}\n\n"
        f"✅ Готове рішення (Worker):\n{final_solution}"
    )
    send_telegram(report)
    print("Цикл 2.0 успішно завершено.")

if __name__ == "__main__":
    run_hermes_autonomous_cycle()
