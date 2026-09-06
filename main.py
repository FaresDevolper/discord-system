import os
import threading
from datetime import timedelta
from flask import Flask
import discord
from discord.ext import commands
from discord import app_commands

# ==========================================
# 1. سيرفر الويب المانع للتوقف (Flask Keep-Alive)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Elv System Bot is Online 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==========================================
# 2. إعدادات البوت والـ Intents
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# 3. أحداث التشغيل والمزامنة
# ==========================================
@bot.event
async def on_ready():
    print(f'✅ تم تسجيل الدخول بنجاح باسم: {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ تم مزامنة {len(synced)} أمر مائل (Slash Commands) بنجاح.')
    except Exception as e:
        print(f'❌ خطأ أثناء مزامنة الأوامر: {e}')

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="إدارة السيرفر | /help"
        )
    )

# ==========================================
# 4. الأوامر الإدارية الكاملة (Slash Commands)
# ==========================================

# --- أمر التايم أوت (Timeout) ---
@bot.tree.command(name="timeout", description="إعطاء تايم أوت (عزل مؤقت) لعضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "لم يتم ذكر السبب"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ لا يمكنك إعطاء تايم أوت لشخص رتبته أعلى منك أو تساويك!", ephemeral=True)
        return
    
    duration = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    
    embed = discord.Embed(title="⛔ حظر مؤقت (Timeout)", color=discord.Color.orange())
    embed.add_field(name="العضو:", value=member.mention, inline=True)
    embed.add_field(name="المدة:", value=f"{minutes} دقيقة", inline=True)
    embed.add_field(name="السبب:", value=reason, inline=False)
    embed.set_footer(text=f"بواسطة: {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)

# --- أمر الباند (Ban) ---
@bot.tree.command(name="ban", description="حظر عضو نهائياً من السيرفر")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم ذكر السبب"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ لا يمكنك إعطاء باند لشخص رتبته أعلى منك أو تساويك!", ephemeral=True)
        return

    await member.ban(reason=reason)
    
    embed = discord.Embed(title="🔨 حظر نهائي (Ban)", color=discord.Color.red())
    embed.add_field(name="العضو المحظور:", value=member.mention, inline=True)
    embed.add_field(name="السبب:", value=reason, inline=False)
    embed.set_footer(text=f"بواسطة: {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)

# --- أمر فك الباند (Unban) ---
@bot.tree.command(name="unban", description="فك الحظر عن عضو بواسطة ID الخاص به")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ تم فك الحظر بنجاح عن **{user.name}**.")
    except Exception:
        await interaction.response.send_message("❌ لم يتم العثور على العضو أو الـ ID غير صحيح.", ephemeral=True)

# --- أمر الطرد (Kick) ---
@bot.tree.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم ذكر السبب"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ لا يمكنك طرد شخص رتبته أعلى منك أو تساويك!", ephemeral=True)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f"👞 تم طرد العضو **{member.name}** | السبب: {reason}")

# --- أمر مسح الشات (Clear) ---
@bot.tree.command(name="clear", description="مسح عدد معين من الرسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ يرجى تحديد عدد بين 1 و 100.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 تم مسح {len(deleted)} رسالة بنجاح.")

# --- أمر قفل الروم (Lock) ---
@bot.tree.command(name="lock", description="قفل الكتابة في القناة الحالية")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔒 تم قفل هذه القناة بنجاح.")

# --- أمر فتح الروم (Unlock) ---
@bot.tree.command(name="unlock", description="فتح الكتابة في القناة الحالية")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔓 تم فتح هذه القناة بنجاح.")

# ==========================================
# 5. معالجة الأخطاء السلسة (منع كراش البوت)
# ==========================================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ ليس لديك الصلاحيات الكافية لاستخدام هذا الأمر!", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ حدث خطأ أثناء تنفيذ الأمر: {error}", ephemeral=True)

# ==========================================
# 6. التشغيل وإحضار التوكن
# ==========================================
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")
