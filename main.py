import discord
import os
from discord.ui import Button, View
from collections import defaultdict

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

allowed_channels = set()
active_games = {}
scores = defaultdict(int)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def red_embed(desc: str) -> discord.Embed:
    return discord.Embed(description=desc, color=0xff0000)

class HintView(View):
    def __init__(self, starter_id: int, hints: list, *, timeout=300):
        super().__init__(timeout=timeout)
        self.starter_id = starter_id
        self.hints = hints

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.starter_id:
            await interaction.response.defer()
            return False
        return True

    @discord.ui.button(label="接近了", style=discord.ButtonStyle.blurple)
    async def close_enough(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("接近了"))

    @discord.ui.button(label="沒有關係", style=discord.ButtonStyle.red)
    async def not_related(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("沒有關係～"))

    @discord.ui.button(label="再猜猜", style=discord.ButtonStyle.green)
    async def guess_again(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("再猜猜！"))

    @discord.ui.button(label="提示一", style=discord.ButtonStyle.grey)
    async def hint1(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed(f"提示係 {self.hints[0]}"))

    @discord.ui.button(label="提示二", style=discord.ButtonStyle.grey)
    async def hint2(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed(f"提示係 {self.hints[1]}"))

    @discord.ui.button(label="提示三", style=discord.ButtonStyle.grey)
    async def hint3(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed(f"提示係 {self.hints[2]}"))

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 已上線！")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = message.channel.id
    content = message.content.strip()

    # === 喚醒指令（公開）===
    if content == "@射你老母":
        allowed_channels.add(channel_id)
        await message.channel.send(embed=red_embed("🧟 Bot 已喚醒！喺呢個頻道可以開始遊戲啦～"))
        return

    if channel_id not in allowed_channels:
        return

    # === 查分（公開紅色）===
    if content == "@mark":
        pts = scores[message.author.id]
        await message.channel.send(embed=red_embed(f"你有 {pts} 分。"))
        return

    # === 出題指令（隱藏原始訊息）===
    if content.startswith("@ANS "):
        parts = content[5:].split(",", 4)
        if len(parts) == 5:
            answer, domain, h1, h2, h3 = [p.strip() for p in parts]
            if not all([answer, domain, h1, h2, h3]):
                await message.author.send(embed=red_embed("⚠️ 每部分都唔可以留空！"))
                return

            # 檢查是否已在進行遊戲
            if channel_id in active_games:
                await message.author.send(embed=red_embed("⚠️ 呢個頻道有遊戲進行中，請等完先！"))
                return

            active_games[channel_id] = {
                "answer": answer,
                "starter_id": message.author.id,
                "domain": domain,
                "hints": [h1, h2, h3]
            }

            # 隱藏確認（只有出題者見）
            await message.author.send(embed=red_embed(f"✅ 謎題已設定！答案：{answer}"))

            # 公開謎題（所有人見）
            view = HintView(starter_id=message.author.id, hints=[h1, h2, h3])
            await message.channel.send(
                embed=red_embed(f"🧠 關於「{domain}」的謎題已開始！大家快猜答案～"),
                view=view
            )
        else:
            await message.author.send(
                embed=red_embed(
                    "⚠️ 格式錯誤！請用：\n"
                    "`@ANS 答案,相關領域,提示一,提示二,提示三`\n"
                    "（用英文逗號分隔，共 5 個部分，無需引號）"
                )
            )
        return

    # === 答對判定（公開）===
    if channel_id in active_games:
        game = active_games[channel_id]
        if content == game["answer"]:
            scores[message.author.id] += 1
            await message.channel.send(
                embed=red_embed(f"🎉 恭喜 {message.author.mention} 答對！答案係 **{game['answer']}**！")
            )
            del active_games[channel_id]

# === 啟動 ===
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ 請設定 DISCORD_BOT_TOKEN")
    else:
        bot.run(DISCORD_TOKEN)
