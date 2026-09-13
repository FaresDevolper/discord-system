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
intents.message_content = True  # أساسي لقراءة النصوص بدون Prefix
intents.members = True          # أساسي للتحكم بالأعضاء
intents.bans = True
intents.voice_states = True     # أساسي للتحكم بالأعضاء في الرومات الصوتية

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 3. دالة مساعدة لاستخراج العضو أو ID العضو ---
def get_user_id(args):
    if not args:
        return None
    match = re.search(r'\d+', args[0])
    if match:
        return int(match.group())
    return None

# --- 4. الأحداث الرئيسية للبدء والأوامر ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Bot is ready with full Arabic commands!')

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    parts = message.content.strip().split()
    if not parts:
        return

    command = parts[0].lower()
    full_text = message.content.strip()
    args = parts[1:]

    # ================= 1. أمر قفل (إخفاء الروم بالكامل) =================
    if command == "قفل":
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("❌ ليس لديك صلاحية إدارة القنوات.")
            return
        await message.channel.set_permissions(message.guild.default_role, view_channel=False)
        await message.channel.send("🔒 تم إخفاء وقفل الروم عن جميع الأعضاء بنجاح.")

    # ================= 2. أمر فتح (إظهار الروم للجميع) =================
    elif command == "فتح":
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("❌ ليس لديك صلاحية إدارة القنوات.")
            return
        await message.channel.set_permissions(message.guild.default_role, view_channel=True)
        await message.channel.send("🔓 تم إظهار وفتح الروم للجميع بنجاح.")

    # ================= 3. أمر قفل الكتابة =================
    elif full_text == "قفل الكتابة" or (len(parts) >= 2 and parts[0] == "قفل" and parts[1] == "الكتابة"):
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("❌ ليس لديك صلاحية إدارة القنوات.")
            return
        await message.channel.set_permissions(message.guild.default_role, send_messages=False)
        await message.channel.send("🚫 تم قفل الكتابة في الروم مع إبقائه ظاهراً.")

    # ================= 4. أمر فتح الكتابة =================
    elif full_text == "فتح الكتابة" or (len(parts) >= 2 and parts[0] == "فتح" and parts[1] == "الكتابة"):
        if not message.author.guild_permissions.manage_channels:
            await message.channel.send("❌ ليس لديك صلاحية إدارة القنوات.")
            return
        await message.channel.set_permissions(message.guild.default_role, send_messages=True)
        await message.channel.send("💬 تم فتح الكتابة في الروم بنجاح.")

    # ================= 5. أمر حذف =================
    elif command == "حذف":
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ ليس لديك صلاحية إدارة الرسائل.")
            return
        amount = 100
        if args and args[0].isdigit():
            amount = int(args[0])
        try:
            deleted = await message.channel.purge(limit=amount + 1)
            confirm_msg = await message.channel.send(f"🧹 تم حذف {len(deleted) - 1} رسالة بنجاح.")
            await confirm_msg.delete(delay=3)
        except discord.Forbidden:
            await message.channel.send("❌ لا أمتلك صلاحيات مسح الرسائل في هذا الروم.")

    # ================= 6. أمر طرد (إخراج من الروم الصوتي) =================
    elif command == "طرد":
        if not message.author.guild_permissions.move_members:
            await message.channel.send("❌ ليس لديك صلاحية نقل/طرد الأعضاء من الروم الصوتي (Move Members).")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن أو الـ ID. مثال: `طرد @user`")
            return
        member = message.guild.get_member(user_id)
        if member:
            if member.voice and member.voice.channel:
                try:
                    await member.move_to(None)
                    await message.channel.send(f"🚪 تم طرد {member.mention} من الروم الصوتي بنجاح.")
                except discord.Forbidden:
                    await message.channel.send("❌ لا أمتلك صلاحيات كافية لإخراج هذا العضو من الروم الصوتي.")
            else:
                await message.channel.send(f"❌ {member.mention} غير موجود في أي روم صوتي حالياً.")
        else:
            await message.channel.send("❌ لم يتم العثور على هذا العضو في السيرفر.")

    # ================= 7. أمر باند =================
    elif command == "باند":
        if not message.author.guild_permissions.ban_members:
            await message.channel.send("❌ ليس لديك صلاحية حظر الأعضاء.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن أو الـ ID. مثال: `باند @user`")
            return
        try:
            user = await bot.fetch_user(user_id)
            await message.guild.ban(user, reason=f"بواسطة {message.author}")
            await message.channel.send(f"🔨 تم حظر {user.mention} من السيرفر بنجاح.")
        except discord.Forbidden:
            await message.channel.send("❌ لا أمتلك صلاحيات كافية لحظر هذا العضو.")
        except discord.NotFound:
            await message.channel.send("❌ لم يتم العثور على العضو.")

    # ================= 8. أمر فك الباند =================
    elif command in ["فك_الباند", "فك-الباند", "فك_باند"] or (len(parts) >= 2 and parts[0] == "فك" and parts[1] == "الباند"):
        if not message.author.guild_permissions.ban_members:
            await message.channel.send("❌ ليس لديك صلاحية إدارة الحظر.")
            return
        target_args = parts[2:] if (len(parts) >= 2 and parts[0] == "فك" and parts[1] == "الباند") else args
        user_id = get_user_id(target_args)
        if not user_id:
            await message.channel.send("⚠️ يرجى كتابة المنشن أو الـ ID للشخص. مثال: `فك الباند 123456789`")
            return
        try:
            user = await bot.fetch_user(user_id)
            await message.guild.unban(user, reason=f"بواسطة {message.author}")
            await message.channel.send(f"✅ تم فك الحظر عن {user.mention} بنجاح.")
        except discord.NotFound:
            await message.channel.send("❌ هذا المستخدم غير محظور أو غير موجود.")
        except discord.Forbidden:
            await message.channel.send("❌ لا أمتلك صلاحية لفك الحظر.")

    # ================= 9. أمر تايم (تايم أوت) =================
    elif command == "تايم":
        if not message.author.guild_permissions.moderate_members:
            await message.channel.send("❌ ليس لديك صلاحية إعطاء تايم أوت.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن. مثال: `تايم @user`")
            return
        member = message.guild.get_member(user_id)
        if member:
            try:
                duration = datetime.timedelta(hours=1)
                await member.timeout(duration, reason=f"بواسطة {message.author}")
                await message.channel.send(f"🔇 تم إعطاء تايم أوت لـ {member.mention} لمدة ساعة.")
            except discord.Forbidden:
                await message.channel.send("❌ لا أمتلك صلاحية لإعطاء تايم أوت لهذا العضو.")
        else:
            await message.channel.send("❌ لم يتم العثور على العضو في السيرفر.")

    # ================= 10. أمر فك التايم =================
    elif command in ["فك_التايم", "فك-التايم"] or (len(parts) >= 2 and parts[0] == "فك" and parts[1] in ["التايم", "تايم"]):
        if not message.author.guild_permissions.moderate_members:
            await message.channel.send("❌ ليس لديك صلاحية إدارة التايم أوت.")
            return
        target_args = parts[2:] if (len(parts) >= 2 and parts[0] == "فك") else args
        user_id = get_user_id(target_args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن. مثال: `فك التايم @user`")
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

    # ================= 11. أمر سحب =================
    elif command == "سحب":
        if not message.author.guild_permissions.move_members:
            await message.channel.send("❌ ليس لديك صلاحية نقل الأعضاء (Move Members).")
            return

        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("❌ يجب أن تكون متواجد في روم صوتي أولاً لتتمكن من سحب العضو.")
            return

        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن أو الـ ID. مثال: `سحب @user`")
            return

        member = message.guild.get_member(user_id)
        if member:
            if not member.voice or not member.voice.channel:
                await message.channel.send(f"❌ العضو {member.mention} ليس متواجداً في أي روم صوتي حالياً.")
                return

            try:
                target_channel = message.author.voice.channel
                await member.move_to(target_channel)
                await message.channel.send(f"📥 تم سحب {member.mention} إلى الروم الصوتي `{target_channel.name}` بنجاح.")
            except discord.Forbidden:
                await message.channel.send("❌ لا أمتلك صلاحية نقل الأعضاء في هذا الروم أو رتبة البوت أقل من العضو.")
        else:
            await message.channel.send("❌ لم يتم العثور على هذا العضو في السيرفر.")

    # ================= 12. أمر معلومات =================
    elif command in ["معلومات", "يوزر"]:
        user_id = get_user_id(args) if args else message.author.id
        member = message.guild.get_member(user_id) or message.author
        
        embed = discord.Embed(title=f"معلومات العضو: {member.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="الاسم:", value=member.name, inline=True)
        embed.add_field(name="الـ ID:", value=member.id, inline=True)
        embed.add_field(name="تاريخ دخول السيرفر:", value=member.joined_at.strftime("%Y-%m-%d"), inline=False)
        embed.add_field(name="تاريخ إنشاء الحساب:", value=member.created_at.strftime("%Y-%m-%d"), inline=False)
        await message.channel.send(embed=embed)

    # ================= 13. أمر سيرفر =================
    elif command in ["سيرفر", "السيرفر"]:
        guild = message.guild
        embed = discord.Embed(title=f"معلومات سيرفر {guild.name}", color=discord.Color.green())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="المالك:", value=guild.owner.mention if guild.owner else "غير معروف", inline=True)
        embed.add_field(name="عدد الأعضاء:", value=guild.member_count, inline=True)
        embed.add_field(name="عدد الرومات:", value=len(guild.channels), inline=True)
        embed.add_field(name="تاريخ الإنشاء:", value=guild.created_at.strftime("%Y-%m-%d"), inline=False)
        await message.channel.send(embed=embed)

    # ================= 14. أمر اسكت =================
    elif command == "اسكت":
        if not message.author.guild_permissions.manage_roles:
            await message.channel.send("❌ ليس لديك صلاحية كتم الأعضاء.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن. مثال: `اسكت @user`")
            return
        member = message.guild.get_member(user_id)
        if member:
            await message.channel.set_permissions(member, send_messages=False)
            await message.channel.send(f"🤐 تم كتم {member.mention} في هذه القناة.")

    # ================= 15. أمر تكلم =================
    elif command == "تكلم":
        if not message.author.guild_permissions.manage_roles:
            await message.channel.send("❌ ليس لديك صلاحية إدارة الأعضاء.")
            return
        user_id = get_user_id(args)
        if not user_id:
            await message.channel.send("⚠️ يرجى تحديد العضو بالمنشن. مثال: `تكلم @user`")
            return
        member = message.guild.get_member(user_id)
        if member:
            await message.channel.set_permissions(member, send_messages=None)
            await message.channel.send(f"🗣️ تم فك الكتم عن {member.mention} في هذه القناة.")

    # ================= 16. أمر أوامر =================
    elif command in ["اوامر", "الأوامر"]:
        help_msg = (
            "**📌 قائمة أوامر البوت العربية:**\n"
            "• `قفل` : إخفاء وقفل الروم عن الجميع.\n"
            "• `فتح` : إظهار وفتح الروم للجميع.\n"
            "• `قفل الكتابة` : منع الكتابة في الروم.\n"
            "• `فتح الكتابة` : السماح بالكتابة في الروم.\n"
            "• `حذف [عدد]` : مسح الرسائل.\n"
            "• `طرد @user` : طرد عضو من الروم الصوتي.\n"
            "• `باند @user` : حظر عضو من السيرفر.\n"
            "• `فك الباند [ID]` : فك الحظر عن شخص.\n"
            "• `تايم @user` : إعطاء تايم أوت.\n"
            "• `فك التايم @user` : إزالة التايم أوت.\n"
            "• `سحب @user` : نقل العضو لرومك الصوتي.\n"
            "• `معلومات @user` : عرض معلومات حساب العضو.\n"
            "• `سيرفر` : عرض معلومات السيرفر.\n"
            "• `اسكت @user` : كتم العضو في الروم الحالي.\n"
            "• `تكلم @user` : فك الكتم في الروم الحالي."
        )
        await message.channel.send(help_msg)

    await bot.process_commands(message)

# --- 5. تشغيل السيرفر والبوت ---
keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN is not set in Environment Variables.")
