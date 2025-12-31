# ===== 禁用 Discord 語音模組（解決 audioop 錯誤）=====
import sys
sys.modules['discord.voice_client'] = type(sys)('discord.voice_client')
sys.modules['discord.player'] = type(sys)('discord.player')
# ===== 禁用完成 =====

# 建立假的 voice_client 模組
fake_voice_client = ModuleType('discord.voice_client')
fake_voice_client.VoiceClient = None
fake_voice_client.VoiceProtocol = None
sys.modules['discord.voice_client'] = fake_voice_client

# 建立假的 player 模組（可選，但建議）
fake_player = ModuleType('discord.player')
sys.modules['discord.player'] = fake_player
# ===== 禁用完成 =====

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
    def __init__(self, starter_id: int, hints: list, *, timeout=1800):
        super().__init__(timeout=timeout)
        self.starter_id = starter_id
        self.hints = hints

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.starter_id:
            await interaction.response.defer()
            return False
        return True

    @discord.ui.button(label="是", style=discord.ButtonStyle.green)
    async def yes_btn(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("是"))

    @discord.ui.button(label="否", style=discord.ButtonStyle.red)
    async def no_btn(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        await interaction.channel.send(embed=red_embed("否"))

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

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 已上線！")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = message.channel.id
    content = message.content.strip()

    # === 喚醒頻道 ===
    if content == "@射你老母":
        allowed_channels.add(channel_id)
        await message.channel.send(embed=red_embed("🧟 Bot 已喚醒！請在本頻道出題。"))
        return

    if channel_id not in allowed_channels:
        return

    # === @stop 強制結束 ===
    if content == "@stop":
        if channel_id in active_games:
            ans = active_games[channel_id]["answer"]
            del active_games[channel_id]
            await message.channel.send(embed=red_embed(f"⏹️ 遊戲已結束！答案係 **{ans}**。"))
        else:
            await message.channel.send(embed=red_embed("❌ 無進行中遊戲。"))
        return

    # === @mark 查分 ===
    if content == "@mark":
        pts = scores[message.author.id]
        await message.channel.send(embed=red_embed(f"你有 {pts} 分。"))
        return

    # === 出題 ===
    if content.startswith("@ANS "):
        try:
            await message.delete()
        except:
            pass

        parts = content[5:].split(",", 4)
        if len(parts) == 5:
            answer, domain, h1, h2, h3 = [p.strip() for p in parts]
            if all([answer, domain, h1, h2, h3]):
                if channel_id in active_games:
                    try:
                        await message.author.send(embed=red_embed("⚠️ 該頻道已有遊戲進行中！"))
                    except:
                        pass
                    return

                active_games[channel_id] = {
                    "answer": answer,
                    "starter_id": message.author.id,
                    "domain": domain,
                    "hints": [h1, h2, h3],
                    "message_count": 0,
                    "resend_threshold": 10
                }

                try:
                    await message.author.send(embed=red_embed(f"✅ 題目已設定！答案：{answer}"))
                except:
                    pass

                view = HintView(starter_id=message.author.id, hints=[h1, h2, h3])
                await message.channel.send(
                    embed=red_embed(f"🧠 關於「{domain}」的謎題已開始！大家快猜～"),
                    view=view
                )
            else:
                try:
                    await message.author.send(embed=red_embed("⚠️ 每部分都唔可以留空！"))
                except:
                    pass
        else:
            try:
                await message.author.send(embed=red_embed("⚠️ 格式錯誤！請用：@ANS 答案,領域,提1,提2,提3"))
            except:
                pass
        return

    # === 答題 & 自動重發 ===
    if channel_id in active_games:
        game = active_games[channel_id]
        if content == game["answer"]:
            scores[message.author.id] += 1
            await message.channel.send(
                embed=red_embed(f"🎉 恭喜 {message.author.mention} 答對！答案係 **{game['answer']}**！")
            )
            del active_games[channel_id]
            return

        # 每 10 條訊息重發
        game["message_count"] += 1
        if game["message_count"] >= game["resend_threshold"]:
            game["message_count"] = 0
            view = HintView(starter_id=game["starter_id"], hints=game["hints"])
            await message.channel.send(
                embed=red_embed(f"🔁 謎題重發（每 {game['resend_threshold']} 訊息）\n🧠 關於「{game['domain']}」的謎題！大家繼續猜～"),
                view=view
            )
        return

# === 啟動 Bot ===
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ 請設定 Render 的 Environment Variables: DISCORD_BOT_TOKEN")
        exit(1)
    else:
        print("🚀 正在連接 Discord...")
        bot.run(DISCORD_TOKEN)
