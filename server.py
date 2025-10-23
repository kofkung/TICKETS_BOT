import threading
from flask import Flask
import discord
from discord import app_commands
import os

# ---------- Flask ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Server is running."

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ---------- Discord Bot ----------
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    await tree.sync()

@tree.command(name="hello")
async def hello(interaction):
    await interaction.response.send_message("Hi there 👋")

# ---------- Run ----------
if __name__ == '__main__':
    threading.Thread(target=run_web).start()  # รัน Flask
    client.run(os.environ['DISCORD_TOKEN'])   # รันบอท