import os
import json
import urllib.request

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

def call_gemini(system_role, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"SYSTEM ROLE: {system_role}

TASK: {prompt}"}
                ]
            }
        ]
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"]

def send_telegram(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram keys missing. Output:
" + message)
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message[:4000]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            print("Telegram sent successfully:", resp.status)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"Telegram HTTPError {e.code}: {err_body}")
        print("Report content:
" + message)
    except Exception as e:
        print(f"Telegram send error: {e}")
        print("Report content:
" + message)

def run_hermes_autonomous_cycle():
    print("[1] Scout: Пошук Web3/AI можливостей...")
    task_prompt = "Сформулюй 1 актуальну ідею мікро-рішення чи баунті для Solana/Web3 на цьому тижні, яку можна швидко реалізувати. Коротко: суть і цінність."
    task = call_gemini("Ти аналітик Web3 та скаут грантів.", task_prompt)

    print("[2] Worker: Розробка рішення...")
    worker_role = "Ти Senior Web3 Engineer. Напиши лаконічне технічне рішення або архітектурний план."
    draft = call_gemini(worker_role, f"Ідея: {task}
Створи технічний опис або прототип.")

    print("[3] Critic: Аудит та перевірка слабких місць...")
    critic_role = "Ти суворий QA-лідер та аудитор. Вкажи на 2 критичні недоліки рішення."
    critique = call_gemini(critic_role, f"Рішення:
{draft}
Зроби короткий аудит.")

    print("[4] Worker: Фінальний варіант...")
    final_solution = call_gemini(worker_role, f"Ось початкове рішення:
{draft}

Ось зауваження аудитора:
{critique}

Сформуй фінальне, виправлене резюме.")

    report = (
        "🚀 *Hermes Autonomous Agent: Звіт циклу*

"
        f"🎯 *Напрямок:*
{task}

"
        f"🔍 *Аудит (Critic):*
{critique}

"
        f"✅ *Фінальний вердикт:*
{final_solution}"
    )
    send_telegram(report)
    print("Цикл успішно завершено.")

if __name__ == "__main__":
    run_hermes_autonomous_cycle()
