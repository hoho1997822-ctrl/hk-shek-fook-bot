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

    # === 新增：是 / 否 按鈕 ===
    @discord.ui.button(label="是", style=discord.ButtonStyle.green)
    async def yes_btn(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("是"))

    @discord.ui.button(label="否", style=discord.ButtonStyle.red)
    async def no_btn(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("否"))

    # === 原有按鈕 ===
    @discord.ui.button(label="接近了", style=discord.ButtonStyle.blurple)
    async def close_enough(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("接近了"))

    @discord.ui.button(label="沒有關係", style=discord.ButtonStyle.grey)
    async def not_related(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("沒有關係～"))

    @discord.ui.button(label="再猜猜", style=discord.ButtonStyle.grey)
    async def guess_again(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("再猜猜！"))

    @discord.ui.button(label="提示一", style=discord.ButtonStyle.grey)
    async def hint1(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed(f"提示係 {self.hints[0]}"))

    @discord.ui.button(label="提示二", style=discord.ButtonStyle.grey)
    async def hint2(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed(f"提示係 {self.hints[1]}"))

    @discord.ui.button(label="提示三", style=discord.ButtonStyle.grey)
    async def hint3(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed(f"提示係 {self.hints[2]}"))

# =============== 以下為完整主邏輯（與之前相同）===============
@bot.event
async def on_ready():
    print(f"✅ {bot.user} 已上線！")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()

    # === 1. 在文字頻道中 ===
    if isinstance(message.channel, discord.TextChannel):
        if content == "@射你老母":
            allowed_channels.add(message.channel.id)
            await message.channel.send(embed=red_embed("🧟 Bot 已喚醒！可用 DM 出題或在此頻道出題。"))
            return

        if message.channel.id not in allowed_channels:
            return

        if content == "@mark":
            pts = scores[message.author.id]
            await message.channel.send(embed=red_embed(f"你有 {pts} 分。"))
            return

        if content.startswith("@ANS "):
            parts = content[5:].split(",", 4)
            if len(parts) == 5:
                answer, domain, h1, h2, h3 = [p.strip() for p in parts]
                if all([answer, domain, h1, h2, h3]):
                    if message.channel.id in active_games:
                        await message.author.send(embed=red_embed("⚠️ 該頻道已有遊戲進行中！"))
                        return
                    active_games[message.channel.id] = {
                        "answer": answer,
                        "starter_id": message.author.id,
                        "domain": domain,
                        "hints": [h1, h2, h3]  # hints[0]=h1, hints[1]=h2, hints[2]=h3
                    }
                    await message.author.send(embed=red_embed(f"✅ 謎題已設定！答案：{answer}"))
                    view = HintView(starter_id=message.author.id, hints=[h1, h2, h3])
                    await message.channel.send(
                        embed=red_embed(f"🧠 關於「{domain}」的謎題已開始！大家快猜～"),
                        view=view
                    )
                else:
                    await message.author.send(embed=red_embed("⚠️ 每部分都唔可以留空！"))
            else:
                await message.author.send(
                    embed=red_embed("⚠️ 格式錯誤！請用：\n`@ANS 答案,相關領域,提示一,提示二,提示三`")
                )
            return

        if message.channel.id in active_games:
            game = active_games[message.channel.id]
            if content == game["answer"]:
                scores[message.author.id] += 1
                await message.channel.send(
                    embed=red_embed(f"🎉 恭喜 {message.author.mention} 答對！答案係 **{game['answer']}**！")
                )
                del active_games[message.channel.id]
            return

    # === 2. 在私訊（DM）中出題 ===
    if isinstance(message.channel, discord.DMChannel):
        if content.startswith("@ANS "):
            parts = content[5:].split(",", 5)
            if len(parts) == 6:
                try:
                    channel_id = int(parts[0].strip())
                    answer, domain, h1, h2, h3 = [p.strip() for p in parts[1:]]
                except ValueError:
                    await message.author.send(embed=red_embed("⚠️ 頻道 ID 必須係數字！"))
                    return

                if channel_id not in allowed_channels:
                    await message.author.send(embed=red_embed("⚠️ 該頻道未被喚醒！請先在頻道打 `@射你老母`。"))
                    return

                if not all([answer, domain, h1, h2, h3]):
                    await message.author.send(embed=red_embed("⚠️ 每部分都唔可以留空！"))
                    return

                if channel_id in active_games:
                    await message.author.send(embed=red_embed("⚠️ 該頻道已有遊戲進行中！"))
                    return

                active_games[channel_id] = {
                    "answer": answer,
                    "starter_id": message.author.id,
                    "domain": domain,
                    "hints": [h1, h2, h3]
                }

                channel = bot.get_channel(channel_id)
                if channel:
                    view = HintView(starter_id=message.author.id, hints=[h1, h2, h3])
                    await channel.send(
                        embed=red_embed(f"🧠 關於「{domain}」的謎題已開始！大家快猜～"),
                        view=view
                    )
                    await message.author.send(embed=red_embed(f"✅ 謎題已發佈到頻道！答案：{answer}"))
                else:
                    await message.author.send(embed=red_embed("❌ 找唔到指定頻道！請檢查 ID。"))
            else:
                await message.author.send(
                    embed=red_embed(
                        "💡 DM 出題格式：\n"
                        "`@ANS 頻道ID,答案,相關領域,提示一,提示二,提示三`"
                    )
                )
        else:
            await message.author.send(embed=red_embed("❌ 私訊只支援出題指令 `@ANS ...`"))

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ 請設定 DISCORD_BOT_TOKEN")
    else:
        bot.run(DISCORD_TOKEN)
