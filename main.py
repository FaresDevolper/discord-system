import os
import re
import datetime
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- 1. إعداد سيرفر Flask لضمان استمرار عمل البوت (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعداد نوايا البوت (Intents) ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # أساسي لقراءة النصوص بدون Slash
intents.members = True          # أساسي للتحكم بالأعضاء (طرد، حظر، تايم أوت، نقل)
intents.bans = True
intents.voice_states = True     # أساسي للتحكم بالأعضاء في الرومات الصوتية (سحب)

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3. دالة مساعدة لاستخراج العضو أو ID العضو ---
def get_user_id(args):
    if not args:
        return None
    # البحث عن الأرقام فقط (في حال استخدام Mention أو ID مباشر)
    match = re.search(r'\d+', args[0])
    if match:
        return int(match.group())
    return None

# --- 4. الحدث الرئيسي لقراءة الرسائل والتحكم بالأوامر ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Bot is ready to handle plain Arabic/English text commands!')

@bot.event
async def on_message(message):
    # إهمال رسائل البوتات لتجنب التكرار اللانهائي
    if message.author.bot or not message.guild:
        return

    # تقسيم الرسالة إلى الكلمة الرئيسية والوسائط المتعددة (Arguments)
    parts = message.content.strip().split()
    if not parts:
        return

    command = parts[0].lower()
    args = parts[1:]

    # ================= 1. أمر قفل =================
    if command == "قفل":
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("❌ ليس لديك صلاحية إدارة القنوات.")
            return
        await message.channel.set_permissions(message.guild.default_role, send_messages=False)
        await message.channel.send("🔒 تم قفل الكتابة في القناة بنجاح.")

    # ================= 2. أمر فتح =================
    elif command == "فتح":
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("❌ ليس لديك صلاحية إدارة القنوات.")
            return
        await message.channel.send("🔓 تم فتح الكتابة في القناة بنجاح.")
        await message.channel.set_permissions(message.guild.default_role, send_messages=True)

    # ================= 3. أمر حذف =================
    elif command == "حذف":
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ ليس لديك صلاحية إدارة الرسائل.")
            return
        amount = 100  # العدد الافتراضي لمسح الشات
        if args and args[0].isdigit():
            amount = int(args[0])
        # حذف كلمة "حذف" نفسها ثم حذف العدد المحدد
        await message.delete()
        deleted = await message.channel.purge(limit=amount)
        confirm_msg = await message.channel.send(f"🧹 تم حذف {len(deleted)} رسالة بنجاح.")
        # حذف رسالة التأكيد بعد 3 ثوانٍ ليبقى الروم نظيفاً
        await confirm_msg.delete(delay=3)

    # ================= 4. أمر طرد =================
    elif command == "طرد":
        if not message.author.guild_permissions.kick_members:
            await message.channel.send("❌ ليس لديك صلاحية طرد الأعضاء.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن أو الـ ID. مثال: `طرد @user`")
            return
        member = message.guild.get_member(user_id)
        if member:
            try:
                await member.kick(reason=f"بواسطة {message.author}")
                await message.channel.send(f"👞 تم طرد {member.mention} من السيرفر بنجاح.")
            except discord.Forbidden:
                await message.channel.send("❌ لا أمتلك صلاحيات كافية لطرد هذا العضو (قد تكون رتبته أعلى من البوت).")
        else:
            await message.channel.send("❌ لم يتم العثور على هذا العضو في السيرفر.")

    # ================= 5. أمر banned =================
    elif command == "banned":
        if not message.author.guild_permissions.ban_members:
            await message.channel.send("❌ ليس لديك صلاحية حظر الأعضاء.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن أو الـ ID. مثال: `banned @user`")
            return
        try:
            user = await bot.fetch_user(user_id)
            await message.guild.ban(user, reason=f"بواسطة {message.author}")
            await message.channel.send(f"🔨 تم حظر {user.mention} من السيرفر بنجاح.")
        except discord.Forbidden:
            await message.channel.send("❌ لا أمتلك صلاحيات كافية لحظر هذا العضو.")
        except discord.NotFound:
            await message.channel.send("❌ لم يتم العثور على العضو.")

    # ================= 6. أمر فك الباند =================
    elif command in ["فك_الباند", "فك-الباند", "فك_باند"]:
        if not message.author.guild_permissions.ban_members:
            await message.channel.send("❌ ليس لديك صلاحية إدارة الحظر.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى كتابة ID الشخص بعد الأمر. مثال: `فك الباند 123456789`")
            return
        try:
            user = await bot.fetch_user(user_id)
            await message.guild.unban(user, reason=f"بواسطة {message.author}")
            await message.channel.send(f"✅ تم فك الحظر عن {user.mention} بنجاح.")
        except discord.NotFound:
            await message.channel.send("❌ هذا المستخدم غير محظور أو غير موجود.")
        except discord.Forbidden:
            await message.channel.send("❌ لا أمتلك صلاحية لفك الحظر.")

    # أوامر كلمة "فك الباند" المكونة من كلمتين منفصلتين
    elif len(parts) >= 2 and parts[0] == "فك" and parts[1] == "الباند":
        if not message.author.guild_permissions.ban_members:
            await message.channel.send("❌ ليس لديك صلاحية إدارة الحظر.")
            return
        user_id = get_user_id(parts[2:])
        if not user_id:
            await message.channel.send("⚠️ يرجى كتابة ID الشخص بعد الأمر. مثال: `فك الباند 123456789`")
            return
        try:
            user = await bot.fetch_user(user_id)
            await message.guild.unban(user, reason=f"بواسطة {message.author}")
            await message.channel.send(f"✅ تم فك الحظر عن {user.mention} بنجاح.")
        except discord.NotFound:
            await message.channel.send("❌ هذا المستخدم غير محظور أو غير موجود.")
        except discord.Forbidden:
            await message.channel.send("❌ لا أمتلك صلاحية لفك الحظر.")

    # ================= 7. أمر off (تايم أوت) =================
    elif command == "off":
        if not message.author.guild_permissions.moderate_members:
            await message.channel.send("❌ ليس لديك صلاحية إعطاء تايم أوت.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو. مثال: `off @user`")
            return
        member = message.guild.get_member(user_id)
        if member:
            try:
                # إعطاء تايم أوت افتراضي لمدة ساعة واحدة
                duration = datetime.timedelta(hours=1)
                await member.timeout(duration, reason=f"بواسطة {message.author}")
                await message.channel.send(f"🔇 تم إعطاء تايم أوت لـ {member.mention} لمدة ساعة.")
            except discord.Forbidden:
                await message.channel.send("❌ لا أمتلك صلاحية لإعطاء تايم أوت لهذا العضو.")
        else:
            await message.channel.send("❌ لم يتم العثور على العضو في السيرفر.")

    # ================= 8. أمر فك off (إزالة التايم أوت) =================
    elif len(parts) >= 2 and parts[0] == "فك" and parts[1].lower() == "off":
        if not message.author.guild_permissions.moderate_members:
            await message.channel.send("❌ ليس لديك صلاحية إدارة التايم أوت.")
            return
        user_id = get_user_id(parts[2:])
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو. مثال: `فك off @user`")
            return
        member = message.guild.get_member(user_id)
        if member:
            try:
                await member.timeout(None, reason=f"بواسطة {message.author}")
                await message.channel.send(f"🔊 تم إزالة التايم أوت عن {member.mention} بنجاح.")
            except discord.Forbidden:
                await message.channel.send("❌ لا أمتلك صلاحية لفك التايم أوت عن هذا العضو.")
        else:
            await message.channel.send("❌ لم يتم العثور على العضو في السيرفر.")

    # ================= 9. أمر سحب (نقل العضو إلى رومك الصوتي) =================
    elif command == "سحب":
        if not message.author.guild_permissions.move_members:
            await message.channel.send("❌ ليس لديك صلاحية نقل الأعضاء (Move Members).")
            return

        # التحقق مما إذا كان مرسل الأمر داخل روم صوتي
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("❌ يجب أن تكون متواجد في روم صوتي أولاً لتتمكن من سحب العضو.")
            return

        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن أو الـ ID. مثال: `سحب @user`")
            return

        member = message.guild.get_member(user_id)
        if member:
            # التحقق مما إذا كان العضو المستهدف داخل روم صوتي
            if not member.voice or not member.voice.channel:
                await message.channel.send(f"❌ العضو {member.mention} ليس متواجداً في أي روم صوتي حالياً.")
                return

            try:
                # نقل العضو إلى الروم الصوتي الخاص بك
                target_channel = message.author.voice.channel
                await member.move_to(target_channel)
                await message.channel.send(f"📥 تم سحب {member.mention} إلى الروم الصوتي `{target_channel.name}` بنجاح.")
            except discord.Forbidden:
                await message.channel.send("❌ لا أمتلك صلاحية نقل الأعضاء في هذا الروم أو رتبة البوت أقل من العضو.")
        else:
            await message.channel.send("❌ لم يتم العثور على هذا العضو في السيرفر.")

    await bot.process_commands(message)

# --- 5. تشغيل السيرفر والبوت ---
keep_alive()

# استدعاء التوكن الخاص بالبوت من متغيّرات البيئة
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN is not set in Environment Variables.")
