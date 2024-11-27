from datetime import datetime
import discord
from discord.ext import commands, tasks
from ModifySelect import ModifySelect
from PopSelect import PopSelect
from ScheduleManager import ScheduleManager
import utils

from ScheduleModal import ScheduleModal

BOT_TOKEN = "<BOT_TOKEN>"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def notify_user(user_id, message):
    user = await bot.fetch_user(user_id)
    await user.send(message)

@bot.tree.command(name="schedule", description="Programmer un message.")
async def schedule(interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Placez-vous dans un channel de serveur pour utiliser **/schedule**.", ephemeral=True)
        return

    if interaction.user.id not in schedule_manager.storage:
        modal = ScheduleModal(interaction, schedule_manager)
        await interaction.response.send_modal(modal)
        return

    user_data = schedule_manager.get_user_data(interaction.user.id)
    if user_data[0] >= 0 and user_data[1][user_data[0]].id is None:
        await interaction.response.send_message(f"En attente de contenu pour le message **{user_data[1][user_data[0]].title}**.", ephemeral=True)
    elif len(user_data[1]) > 4:
        await interaction.response.send_message("Nombre limite de messages programmés atteint. Utiliser **/pop** pour un supprimer un.", ephemeral=True)
    else:
        modal = ScheduleModal(interaction, schedule_manager)
        await interaction.response.send_modal(modal)

@bot.event
async def on_message(message):
    if message.guild is None and message.author != bot.user:
        user_id = message.author.id
        if user_id in schedule_manager.storage and schedule_manager.storage[user_id][0] >= 0:
            user_data = schedule_manager.get_user_data(user_id)
            if user_data[1][user_data[0]].id is None:
                user_data[1][user_data[0]].id = message.id
                await notify_user(user_id, f"Contenu de **{user_data[1][user_data[0]].title}** enregistré")
                return
        await message.author.send("Aucun nouveau message programmé. Utiliser **/schedule** pour en programmer un.", ephemeral=True)

@bot.tree.command(name="scheduled", description="Voir vos messages programmés.")
async def scheduled(interaction):
    user_id = interaction.user.id
    if user_id in schedule_manager.storage and schedule_manager.storage[user_id][0] >= 0:
        user_data = schedule_manager.get_user_data(user_id)
        dm_channel = await interaction.user.create_dm()

        count = 0
        b = False
        for index, message in enumerate(user_data[1]):
            if message.id is not None:
                try:
                    msg = await dm_channel.fetch_message(message.id)
                    await msg.reply(
                        f"- **Titre** : {message.title}\n"
                        f"- **Horaire** : {utils.format_datetime(message.time)}\n"
                        f"- **Récurrence** : {message.repeat}\n"
                        f"- **Channel** : {message.channel.mention}\n"
                    )
                    count += 1
                except discord.NotFound:
                    schedule_manager.remove_message(user_id, index)
            else:
                await interaction.user.send(
                    f"- **Titre** : {message.title}\n"
                    f"- **Horaire** : {utils.format_datetime(message.time)}\n"
                    f"- **Récurrence** : {message.repeat}\n"
                    f"- **Channel** : {message.channel.mention}\n"
                    f"**En attente du contenu**"
                )
                count += 1
                b = True

        await interaction.response.send_message(f"{count} message{'s' if count > 1 else ''} programmé{'s' if count > 1 else ''}{', dont 1 en attente de contenu' if b else ''}", ephemeral=True)

    else:
        await interaction.response.send_message("Aucun message programmé. Utiliser **/schedule** pour en programmer un.", ephemeral=True)



@bot.tree.command(name="modify", description="Modifier un message programmé.")
async def modify(interaction):
    user_id = interaction.user.id

    if user_id in schedule_manager.storage and schedule_manager.storage[user_id][0] >= 0:
        view = ModifySelect(interaction, schedule_manager.storage[user_id])
        await interaction.response.send_message("Sélectionnez un message à modifier", view=view, ephemeral=True)
    else:
        await interaction.response.send_message("Aucun message programmé. Utiliser **/schedule** pour en programmer un.", ephemeral=True)


@bot.tree.command(name="pop", description="Supprimer un message programmé.")
async def pop(interaction):
    user_id = interaction.user.id
    if user_id in schedule_manager.storage and schedule_manager.storage[user_id][0] >= -1:
        view = PopSelect(interaction, user_id, schedule_manager)
        await interaction.response.send_message("Sélectionnez un message à supprimer", view=view, ephemeral=True)
    else:
        await interaction.response.send_message("Aucun message programmé. Utiliser **/schedule** pour en programmer un.", ephemeral=True)

schedule_manager = ScheduleManager()

@tasks.loop(seconds=50)
async def check_scheduled_messages():
    for user_id in schedule_manager.storage:
        await schedule_manager.send_scheduled_messages(user_id, datetime.now())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} a démarré avec succès!')
    check_scheduled_messages.start()

bot.run(BOT_TOKEN
