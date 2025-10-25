import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# ---------- Flask ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Discord Bot is running on Render"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ---------- Discord Bot Setup ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# -------------------- CONFIG --------------------
STAFF_ROLE_NAME = "･ﾟ✧พนักงานลูกไก่ ☆"
TICKET_CATEGORY = "🎫 ตั๋วงาน"
ORDER_CHANNEL_NAME = "❃🪬･˚⁺สั่งสินค้า"
# ------------------------------------------------

class TicketModal(Modal, title='เปิดตั๋วงาน'):
    scale = TextInput(
        label='สเกลที่ต้องการ',
        placeholder='ระบุสเกล: 128 / 512 / 1024',
        required=True,
        max_length=100
    )
    reference = TextInput(
        label='Reference',
        placeholder='ใส่ reference ของคุณ',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    image_url = TextInput(
        label='รูปภาพ (URL)',
        placeholder='ใส่ URL ของรูปภาพ',
        required=False,
        max_length=500
    )
    convert_addon = TextInput(
        label='แปลงแอดออนหรือไม่',
        placeholder='ตอบ: ใช่ / ไม่ หรือระบุรายละเอียดเพิ่มเติม',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        for ch in guild.text_channels:
            if ch.name == f'ticket-{user.name.lower()}':
                await interaction.response.send_message(f'❌ คุณมีตั๋วเปิดอยู่แล้ว: {ch.mention}', ephemeral=True)
                return

        ticket_channel = await guild.create_text_channel(
            name=f'ticket-{user.name}',
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title='🎫 ตั๋วใหม่',
            description=f'ตั๋วของ {user.mention}',
            color=discord.Color.blue()
        )
        embed.add_field(name='📏 สเกลที่ต้องการ', value=self.scale.value, inline=False)
        embed.add_field(name='📝 Reference', value=self.reference.value, inline=False)
        embed.add_field(name='🖼️ รูปภาพ', value=self.image_url.value if self.image_url.value else "ไม่มี", inline=False)
        embed.add_field(name='🔄 แปลงแอดออนหรือไม่', value=self.convert_addon.value, inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f'เปิดโดย: {user.name}', icon_url=user.display_avatar.url)

        await ticket_channel.send(embed=embed)
        await interaction.response.send_message(f'✅ เปิดตั๋วสำเร็จ! ห้องของคุณ: {ticket_channel.mention}', ephemeral=True)


class TicketButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='🎫 เปิดตั๋ว', style=discord.ButtonStyle.primary, custom_id='open_ticket')
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())


@tree.command(name='setup_ticket', description='ตั้งค่าระบบตั๋ว (เฉพาะ Admin)')
@app_commands.default_permissions(administrator=True)
async def setup_ticket(interaction: discord.Interaction):
    if interaction.channel.name != ORDER_CHANNEL_NAME:
        await interaction.response.send_message(
            f'❌ คำสั่งนี้ใช้ได้เฉพาะในห้อง **{ORDER_CHANNEL_NAME}** เท่านั้น!',
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title='🎫 ระบบเปิดตั๋วงาน',
        description='กดปุ่มด้านล่างเพื่อเปิดตั๋วและกรอกข้อมูล',
        color=discord.Color.green()
    )
    embed.add_field(
        name='📋 ข้อมูลที่ต้องกรอก:',
        value='• สเกลที่ต้องการ (128 / 512 / 1024)\n• Reference\n• รูปภาพ (URL)\n• แปลงแอดออนหรือไม่',
        inline=False
    )

    await interaction.response.send_message(embed=embed, view=TicketButton())

# -------------------- END TICKET COMMAND --------------------

class EndTicketView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label='✅ จบงาน', style=discord.ButtonStyle.success)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message('❌ เฉพาะพนักงานเท่านั้นที่สามารถปิดตั๋วได้!', ephemeral=True)
            return

        await interaction.response.send_message('✅ กำลังลบห้องนี้...', ephemeral=True)
        await self.channel.delete()

@tree.command(name="end_ticket", description="แสดงปุ่มจบงาน (เฉพาะพนักงาน)")
async def end_ticket(interaction: discord.Interaction):
    staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)
    if staff_role not in interaction.user.roles:
        await interaction.response.send_message("❌ เฉพาะพนักงานเท่านั้นที่ใช้คำสั่งนี้ได้!", ephemeral=True)
        return

    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ คำสั่งนี้ต้องใช้ในห้องตั๋วเท่านั้น!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔚 ปิดตั๋วงาน",
        description="กดปุ่มด้านล่างเพื่อ **จบงานและลบห้องนี้**",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, view=EndTicketView(interaction.channel))

# ------------------------------------------------------------

@client.event
async def on_ready():
    await tree.sync()
    print(f'✅ บอทพร้อมใช้งาน: {client.user}')
    print(f'📡 เข้าร่วมเซิร์ฟเวอร์: {len(client.guilds)} เซิร์ฟเวอร์')

# ---------- Run ----------
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError("❌ ไม่พบ DISCORD_TOKEN ในไฟล์ .env!")
    
    # รัน Flask ใน Thread แยก
    threading.Thread(target=run_web, daemon=True).start()
    
    # รันบอท Discord
    client.run(TOKEN)
