import discord
from discord.ext import commands
import random
import os
import requests

# ✅ 從環境變數取得敏感資料（見下面設定方法）
GROQ_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 香港題庫
answers = [
    {"name": "絲襪奶茶", "clues": ["飲品", "奶", "茶", "街頭"]},
    {"name": "咖喱魚蛋", "clues": ["小食", "魚蛋", "咖喱", "街頭"]},
    {"name": "維多利亞港", "clues": ["港口", "夜景", "燈光秀", "海"]},
    {"name": "太平山頂", "clues": ["山頂", "纜車", "景點", "夜景"]},
    {"name": "蛋撻", "clues": ["甜品", "葡撻", "蛋", "烘焙"]},
    {"name": "腸粉", "clues": ["小食", "米", "粉", "早餐"]},
    {"name": "雞蛋仔", "clues": ["小食", "蛋", "街頭", "脆"]},
    {"name": "天星小輪", "clues": ["船", "渡輪", "維港", "交通"]},
    {"name": "叮叮車", "clues": ["電車", "綠色", "港島", "雙層"]},
    {"name": "菠蘿油", "clues": ["麵包", "牛油", "早餐", "菠蘿"]},
    {"name": "周星馳", "clues": ["演員", "導演", "喜劇", "星爺"]},
    {"name": "成龍", "clues": ["演員", "動作", "功夫", "好萊塢"]},
    {"name": "海洋公園", "clues": ["主題公園", "動物", "纜車", "海"]},
    {"name": "尖沙咀鐘樓", "clues": ["鐘樓", "地標", "火車站", "維港"]},
    {"name": "雙層巴士", "clues": ["巴士", "雙層", "紅色", "交通"]},
    {"name": "牛雜", "clues": ["小食", "牛", "雜", "湯"]},
    {"name": "鳳爪", "clues": ["小食", "雞", "爪", "茶樓"]},
    {"name": "車仔麵", "clues": ["麵", "車仔", "即食", "街頭"]},
    {"name": "波鞋街", "clues": ["街", "鞋", "旺角", "波鞋"]},
    {"name": "蘭桂坊", "clues": ["酒吧", "街", "中環", "夜生活"]},
]

# 設定 Bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
games = {}  # channel_id: game state

def groq_ask(secret, question):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{
            "role": "user",
            "content": f"秘密答案：{secret}\n玩家問：{question}\n你係NPC桃小小，只答「是」、「否」或「唔知」。唔好講答案或多餘野。"
        }],
        "max_tokens": 10
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        else:
            return "唔知（API error）"
    except Exception as e:
        return "唔知（網絡問題）"

@bot.slash_command(name="start", description="開始新一局射覆遊戲！")
async def start_game(ctx):
    secret_item = random.choice(answers)
    secret = secret_item["name"]
    clues = "、".join(secret_item["clues"][:3])
    maxq = 30
    games[ctx.channel.id] = {
        "secret": secret,
        "qcount": 0,
        "hints": 0,
        "maxq": maxq
    }
    await ctx.respond(f"🧞‍♂️ **射覆開始！**\n初始提示：{clues}\n限 {maxq} 條問題，用 `/ask` 問啦！")

@bot.slash_command(name="ask", description="問一條是非問題")
async def ask(ctx, question: str):
    if ctx.channel.id not in games:
        await ctx.respond("⚠️ 都未開始遊戲！打 `/start` 先啦～")
        return
    game = games[ctx.channel.id]
    if game["qcount"] >= game["maxq"]:
        await ctx.respond(f"💥 超過 {game['maxq']} 問！答案係 **{game['secret']}** 😅\n想再玩？打 `/start`！")
        del games[ctx.channel.id]
        return
    ans = groq_ask(game["secret"], question)
    game["qcount"] += 1
    await ctx.respond(f"**Q{game['qcount']}: {question}** → {ans}\n剩 {game['maxq'] - game['qcount']} 問")

@bot.slash_command(name="hint", description="要額外提示（最多3次）")
async def hint(ctx):
    if ctx.channel.id not in games:
        await ctx.respond("⚠️ 都未開始遊戲！打 `/start` 先啦～")
        return
    game = games[ctx.channel.id]
    if game["hints"] >= 3:
        await ctx.respond("💡 Hint 用晒啦！快啲 `/guess` 猜答案啦😂")
        return
    item = next((a for a in answers if a["name"] == game["secret"]), None)
    extra_clue = item["clues"][3] if item and len(item["clues"]) > 3 else "香港地道"
    game["hints"] += 1
    await ctx.respond(f"💡 **Hint {game['hints']}: {extra_clue}**")

@bot.slash_command(name="guess", description="直接猜答案")
async def guess(ctx, answer: str):
    if ctx.channel.id not in games:
        await ctx.respond("冇遊戲進行中！打 `/start` 開局啦～")
        return
    game = games[ctx.channel.id]
    if answer.strip() == game["secret"]:
        await ctx.respond(f"🎉 **正解！** 答案係 **{game['secret']}**！總共問咗 {game['qcount']} 條問題。\n再玩一局？打 `/start`！")
        del games[ctx.channel.id]
    else:
        await ctx.respond("❌ 錯咗！繼續問 `/ask` 或再 `/guess` 試下！")

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 成功上線！")
    print(f"🔗 邀請連結：https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=2048&scope=bot+applications.commands")

# 啟動 Bot
if __name__ == "__main__":
    if not GROQ_KEY or not DISCORD_TOKEN:
        print("❌ 請設定環境變數：GROQ_API_KEY 同 DISCORD_BOT_TOKEN")
    else:
        bot.run(DISCORD_TOKEN)
