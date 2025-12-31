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
    def __init__(self, starter_id: int, hints: list, *, timeout=600):
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

    # === 喚醒指令 ===
    if content == "@射你老母":
        allowed_channels.add(channel_id)
        await message.channel.send(embed=red_embed("🧟 Bot 已喚醒！請在本頻道出題。"))
        return

    if channel_id not in allowed_channels:
        return

    # === 強制結束遊戲 ===
    if content == "@stop":
        if channel_id in active_games:
            game = active_games[channel_id]
            ans = game["answer"]
            del active_games[channel_id]
            await message.channel.send(embed=red_embed(f"⏹️ 遊戲已被強制結束！答案係 **{ans}**。"))
        else:
            await message.channel.send(embed=red_embed("❌ 無進行中遊戲。"))
        return

    # === 查分 ===
    if content == "@mark":
        pts = scores[message.author.id]
        await message.channel.send(embed=red_embed(f"你有 {pts} 分。"))
        return

    # === 出題 ===
    if content.startswith("@ANS "):
        # 刪除原始訊息（需權限）
        try:
            await message.delete()
        except discord.Forbidden:
            # 若無「管理訊息」權限，則不刪除（但會提示）
            pass

        parts = content[5:].split(",", 4)
        if len(parts) == 5:
            answer, domain, h1, h2, h3 = [p.strip() for p in parts]
            if all([answer, domain, h1, h2, h3]):
                if channel_id in active_games:
                    await message.author.send(embed=red_embed("⚠️ 該頻道已有遊戲進行中！"))
                    return

                active_games[channel_id] = {
                    "answer": answer,
                    "starter_id": message.author.id,
                    "domain": domain,
                    "hints": [h1, h2, h3]
                }

                # DM 出題者確認
                try:
                    await message.author.send(embed=red_embed(f"✅ 題目提案成功！\n答案：{answer}\n領域：{domain}"))
                except discord.Forbidden:
                    # 若用戶關閉 DM，忽略
                    pass

                # 公開發謎題
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

    # === 答題判定 ===
    if channel_id in active_games:
        game = active_games[channel_id]
        if content == game["answer"]:
            scores[message.author.id] += 1
            await message.channel.send(
                embed=red_embed(f"🎉 恭喜 {message.author.mention} 答對！答案係 **{game['answer']}**！")
            )
            del active_games[channel_id]
        return

# === 啟動 ===
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ 請設定 DISCORD_BOT_TOKEN")
    else:
        bot.run(DISCORD_TOKEN)
