import discord
import os
import re
from discord.ui import Button, View

# === 設定 ===
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 活動遊戲：channel_id → { "answer": str, "starter_id": int, "hints": [str, str, str], "domain": str }
active_games = {}

# === Bot 設定 ===
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

class HintView(View):
    def __init__(self, starter_id: int, hints: list, *, timeout=300):
        super().__init__(timeout=timeout)
        self.starter_id = starter_id
        self.hints = hints

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # 只允許出題者點按鈕
        if interaction.user.id != self.starter_id:
            await interaction.response.send_message("❌ 嘸係你出題，唔可以用呢啲按鈕！", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="接近了", style=discord.ButtonStyle.blurple)
    async def close_enough(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message("接近了！", delete_after=10)

    @discord.ui.button(label="沒有關係", style=discord.ButtonStyle.red)
    async def not_related(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message("沒有關係～", delete_after=10)

    @discord.ui.button(label="再猜猜", style=discord.ButtonStyle.green)
    async def guess_again(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message("再猜猜！", delete_after=10)

    @discord.ui.button(label="提示一", style=discord.ButtonStyle.grey)
    async def hint1(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message(f"💡 **提示一**：{self.hints[0]}", delete_after=30)

    @discord.ui.button(label="提示二", style=discord.ButtonStyle.grey)
    async def hint2(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message(f"💡 **提示二**：{self.hints[1]}", delete_after=30)

    @discord.ui.button(label="提示三", style=discord.ButtonStyle.grey)
    async def hint3(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_message(f"💡 **提示三**：{self.hints[2]}", delete_after=30)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 已上線！")
    print(f"🔗 邀請連結：https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=2048&scope=bot")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()

    # 檢查是否符合 @ANS 格式
    # 支援：@ANS "答案", "領域", "提示1", "提示2", "提示3"
    if content.startswith("@ANS "):
        rest = content[5:].strip()
        # 使用正則拆分引號內容（支援中英文引號）
        matches = re.findall(r'["“”](.*?)["“”]', rest)
        if len(matches) == 5:
            answer, domain, h1, h2, h3 = matches
            active_games[message.channel.id] = {
                "answer": answer,
                "starter_id": message.author.id,
                "domain": domain,
                "hints": [h1, h2, h3]
            }

            view = HintView(starter_id=message.author.id, hints=[h1, h2, h3])
            await message.channel.send(
                f"🧠 關於「{domain}」的謎題已開始！大家快猜答案～",
                view=view
            )
        else:
            await message.channel.send(
                "⚠️ 格式錯誤！請用：\n"
                "`@ANS \"答案\", \"相關領域\", \"提示一\", \"提示二\", \"提示三\"`\n"
                "例如：`@ANS \"港珠澳大橋\", \"基建\", \"連接三地\", \"世界最長跨海橋\", \"2018年通車\"`"
            )
        return

    # 檢查是否有人答對
    channel_id = message.channel.id
    if channel_id in active_games:
        game = active_games[channel_id]
        if message.content.strip() == game["answer"]:
            # 答對！
            await message.channel.send(
                f"🎉 恭喜 {message.author.mention} 答對！答案係 **{game['answer']}**！"
            )
            # 移除遊戲（按鈕自動失效）
            del active_games[channel_id]
        # （可選）答錯不回應，避免刷屏

# === 啟動 ===
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ 請設定環境變數 DISCORD_BOT_TOKEN")
    else:
        bot.run(DISCORD_TOKEN)
