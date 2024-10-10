import discord
from discord.ext import commands, tasks
from discord import ui

import re
from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

@dataclass
class ScheduledMessage:
    title: str
    time: datetime
    channel: discord.TextChannel
    id: int
    repeat: str

def time_input_test(time_input):
    return re.match(r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9]$", time_input) is None

def date_input_test(date_input):
    return date_input and re.match(r"^(?:0?[1-9]|[12][0-9]|3[01])/(?:0?[1-9]|1[0-2])$", date_input) is None

def repeat_input_test(repeat_input):
    return repeat_input and re.match(r"^(0|(1?[0-9]|2[0-4])h|(0?[1-7])j|(0?[1-4])w|(0?[1-9]|1[0-2])m)$", repeat_input) is None

def parse_time(time_input, date_input):
    now = datetime.now()

    time = datetime.strptime(time_input, "%H:%M")
    if date_input:
      date = datetime.strptime(date_input, "%d/%m")
    else:
      date = datetime.now()

    dtime = time.replace(
        day=date.day,
        month=date.month,
        year=now.year + (date.month < now.month)
    )
    while dtime <= now:
        dtime += relativedelta(days=1)

    return dtime

def parse_channel(guild, path):
    path = path.split('/')

    if len(path) > 1:
        category_name = path[0].strip().lower()
        channel_name = path[1].strip().lower()
        
        for channel in guild.channels:
            if channel.category and channel.category.name.lower() == category_name:
                if channel.name.lower() == channel_name and isinstance(channel, discord.TextChannel):
                    return channel
    else:
        channel_name = path[0].strip().lower()

        for channel in guild.channels:
            if channel.category is None and channel.name.lower() == channel_name and isinstance(channel, discord.TextChannel):
                return channel

    return None

def format_datetime(dt):
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime('%H:%M')
    else:
        return dt.strftime('%H:%M - %d/%m')

async def notify_user(user_id, message):
    user = await bot.fetch_user(user_id)
    await user.send(message)

def binary_search(user_messages, target_time):
    inf = 0
    sup = len(user_messages)
    
    while inf < sup:
        mid = (sup + inf) // 2
        msg = user_messages[mid]

        if msg.time < target_time:
            inf = mid + 1
        else:
            sup = mid 

    return inf

class ScheduleManager:
    def __init__(self):
        self.storage = {}

    def schedule_message(self, user_id, message):
        if user_id not in self.storage:
            self.storage[user_id] = [-1, []]

        self.add_message(user_id, message)

    def add_message(self, user_id, message):
        index = binary_search(self.storage[user_id][1], message.time)
        self.storage[user_id][0] = index
        self.storage[user_id][1][index:index] = [message]

    def remove_message(self, user_id, index=0):
        del self.storage[user_id][1][index]
        if self.storage[user_id][0] >= len(self.storage[user_id][1]):
            self.storage[user_id][0] -= 1

    def get_user_data(self, user_id):
        return self.storage[user_id]

    async def send_scheduled_messages(self, user_id, current_time):
      user_data = self.get_user_data(user_id)

      while user_data[1] and user_data[1][0].time <= current_time:
          await self.process_message(user_id, user_data[1][0])

    async def process_message(self, user_id, message):
        user = await bot.fetch_user(user_id)
        dm_channel = await user.create_dm()

        try:
            msg = await dm_channel.fetch_message(message.id)
            await message.channel.send(msg.content)
            self.handle_repeat(user_id, message)
        except (discord.NotFound, discord.Forbidden):
            await user.send(f"Message **{message.title}** supprimé suite à une impossibilité d'envoi.", ephemeral=True)
            self.remove_message(user_id)

    def handle_repeat(self, user_id, message):
        if message.repeat != "0":
            message.time = self.get_next_time(message)
        else:
            self.remove_message(user_id)

    @staticmethod
    def get_next_time(message):
        match = re.match(r"(\d+)([hjwm])", message.repeat)

        if match.group(2) == "h":
            heures = int(match.group(1))
            return message.time + relativedelta(hours=heures)
        elif match.group(2) == "j":
            jours = int(match.group(1))
            return message.time  + relativedelta(days=jours)
        elif match.group(2) == "w":
            semaines = int(match.group(1))
            return message.time + relativedelta(weeks=semaines)
        mois = int(match.group(1))
        return message.time + relativedelta(months=mois)

class ScheduleModal(ui.Modal, title="Eirbizarre"):
    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

        self.title_input = ui.TextInput(
            label="Titre",
            placeholder="...",
            max_length=50,
            required=True
        )
        self.time_input = ui.TextInput(
            label="Horaire",
            placeholder="hh:mm",
            min_length=5,
            max_length=5,
            required=True
        )
        self.date_input = ui.TextInput(
            label="Date",
            placeholder="jj/mm",
            min_length=5,
            max_length=5,
            required=False
        )
        self.repeat_input = ui.TextInput(
            label="Récurrence",
            placeholder="ex: 2h, 1j, 3w, 1m",
            min_length = 2,
            max_length = 3,
            required=False
        )

        self.add_item(self.title_input)
        self.add_item(self.time_input)
        self.add_item(self.date_input)
        self.add_item(self.repeat_input)

    async def on_submit(self, interaction):
        time_test = time_input_test(self.time_input.value)
        date_test = date_input_test(self.date_input.value)
        repeat_test = repeat_input_test(self.repeat_input.value)

        if time_test or date_test or repeat_test:
            response = f"**ValueError**\n" \
                       f"- ☑️ **Titre** : {self.title_input.value}\n" \
                       f"- {'❌' if time_test else '☑️'} **Horaire** : {self.time_input.value}\n"
            if self.date_input.value:
                response += f"- {'❌' if date_test else '☑️'} **Date** : {self.date_input.value}\n"
            if self.repeat_input.value:
                response += f"- {'❌' if repeat_test else '☑️'} **Récurrence** : {self.repeat_input.value}"

            await interaction.response.send_message(response, ephemeral=True)
            return

        dtime = parse_time(self.time_input.value, self.date_input.value)

        await interaction.user.send(
            f"**Nouveau message programé**\n"
            f"- **Titre** : {self.title_input.value}\n"
            f"- **Horaire** : {format_datetime(dtime)}\n"
            f"- **Récurrence** : {self.repeat_input.value if self.repeat_input.value else '0'}\n"
            f"- **Channel** : {interaction.channel.mention}\n"
            f"**Veuillez écrire son contenu**"
        )

        message = ScheduledMessage(
            title=self.title_input.value,
            time=dtime,
            channel=interaction.channel,
            id=None,
            repeat=self.repeat_input.value if self.repeat_input.value else "0",
        )
        schedule_manager.schedule_message(interaction.user.id, message)

        await interaction.response.defer()

@bot.tree.command(name="schedule", description="Programmer un message.")
async def schedule(interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Placez-vous dans un channel de serveur pour utiliser **/schedule**.", ephemeral=True)
        return

    if interaction.user.id not in schedule_manager.storage:
        modal = ScheduleModal(interaction)
        await interaction.response.send_modal(modal)
        return

    user_data = schedule_manager.get_user_data(interaction.user.id)
    if user_data[0] >= 0 and user_data[1][user_data[0]].id is None:
        await interaction.response.send_message(f"En attente de contenu pour le message **{user_data[1][user_data[0]].title}**.", ephemeral=True)
    elif len(user_data[1]) > 4:
        await interaction.response.send_message("Nombre limite de messages programmés atteint. Utiliser **/pop** pour un supprimer un.", ephemeral=True)
    else:
        modal = ScheduleModal(interaction)
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
                        f"- **Horaire** : {format_datetime(message.time)}\n"
                        f"- **Récurrence** : {message.repeat}\n"
                        f"- **Channel** : {message.channel.mention}\n"
                    )
                    count += 1
                except discord.NotFound:
                    schedule_manager.remove_message(user_id, index)
            else:
                await interaction.user.send(
                    f"- **Titre** : {message.title}\n"
                    f"- **Horaire** : {format_datetime(message.time)}\n"
                    f"- **Récurrence** : {message.repeat}\n"
                    f"- **Channel** : {message.channel.mention}\n"
                    f"**En attente du contenu**"
                )
                count += 1
                b = True

        await interaction.response.send_message(f"{count} message{'s' if count > 1 else ''} programmé{'s' if count > 1 else ''}{', dont 1 en attente de contenu' if b else ''}", ephemeral=True)

    else:
        await interaction.response.send_message("Aucun message programmé. Utiliser **/schedule** pour en programmer un.", ephemeral=True)

class ModifySelect(ui.View):
    def __init__(self, interaction, user_data):
        super().__init__()
        self.interaction = interaction
        self.user_data = user_data

        self.select = discord.ui.Select(
            placeholder="Sélectionner un message",
            options=[discord.SelectOption(label=msg.title, value=str(i)) for i, msg in enumerate(user_data[1])]
        )

        self.select.callback = self.select_message
        self.add_item(self.select)

    async def select_message(self, interaction):
        index = int(self.select.values[0])
        modal = ModifyModal(self.interaction, self.user_data, index)
        await self.interaction.edit_original_response(content="Modification en cours", view=None)
        await interaction.response.send_modal(modal)

class ModifyModal(ui.Modal, title="Modifier Message Programmé"):
    def __init__(self, interaction, user_data, index):
        super().__init__()
        self.interaction = interaction
        self.user_data = user_data
        self.index = index
        self.message = user_data[1][index]

        self.title_input = ui.TextInput(
            label="Titre",
            placeholder="...",
            default=self.message.title,
            max_length=50,
            required=True
        )
        self.time_input = ui.TextInput(
            label="Horaire",
            placeholder="hh:mm",
            default=self.message.time.strftime('%H:%M'),
            min_length=5,
            max_length=5,
            required=True
        )
        self.date_input = ui.TextInput(
            label="Date",
            placeholder="jj/mm",
            default=self.message.time.strftime('%d/%m'),
            min_length=5,
            max_length=5,
            required=True
        )
        self.repeat_input = ui.TextInput(
            label="Récurrence",
            placeholder="ex: 2h, 1j, 3w, 1m",
            default=self.message.repeat,
            min_length = 1,
            max_length = 3,
            required=True
        )
        self.channel_input = ui.TextInput(
            label="Channel",
            placeholder="ex: salons textuels/général",
            default=f"{self.message.channel.category.name + '/' if self.message.channel.category else ''}{self.message.channel.name} ",
            min_length=2,
            required=True
        )

        self.add_item(self.title_input)
        self.add_item(self.time_input)
        self.add_item(self.date_input)
        self.add_item(self.repeat_input)
        self.add_item(self.channel_input)

    async def on_submit(self, interaction):
        time_test = time_input_test(self.time_input.value)
        date_test = date_input_test(self.date_input.value)
        repeat_test = repeat_input_test(self.repeat_input.value)
        channel = parse_channel(self.message.channel.guild, self.channel_input.value)

        if time_test or date_test or channel is None or repeat_test:
            response = f"**ValueError**\n" \
                       f"- ☑️ **Titre** : {self.title_input.value}\n" \
                       f"- {'❌' if time_test else '☑️'} **Horaire** : {self.time_input.value}\n" \
                       f"- {'❌' if date_test else '☑️'} **Date** : {self.date_input.value}\n" \
                       f"- {'❌' if repeat_test else '☑️'} **Récurrence** : {self.repeat_input.value}\n" \
                       f"- {'❌' if channel is None else '☑️'} **Channel** : {self.channel_input.value}"
            await self.interaction.edit_original_response(content=response)

        else:
            self.update_fields(channel)

            await self.interaction.edit_original_response(
                content=f"**Message mis à jour**\n" \
                        f"- **Titre** : {self.message.title}\n" \
                        f"- **Horaire** : {format_datetime(self.message.time)}\n" \
                        f"- **Récurrence** : {self.message.repeat}\n" \
                        f"- **Channel** : {self.message.channel.mention}\n"
            )

            self.reorder_storage()

        await interaction.response.defer()

    def update_fields(self, channel):
        self.message.title = self.title_input.value
        self.message.time = parse_time(self.time_input.value, self.date_input.value)
        self.message.repeat = self.repeat_input.value
        self.message.channel = channel

    def reorder_storage(self):
        del self.user_data[1][self.index]
        index = binary_search(self.user_data[1], self.message.time)
        self.user_data[1][index:index] = [self.message]

@bot.tree.command(name="modify", description="Modifier un message programmé.")
async def modify(interaction):
    user_id = interaction.user.id

    if user_id in schedule_manager.storage and schedule_manager.storage[user_id][0] >= 0:
        view = ModifySelect(interaction, schedule_manager.storage[user_id])
        await interaction.response.send_message("Sélectionnez un message à modifier", view=view, ephemeral=True)
    else:
        await interaction.response.send_message("Aucun message programmé. Utiliser **/schedule** pour en programmer un.", ephemeral=True)

class PopSelect(ui.View):
    def __init__(self, interaction, user_id):
        super().__init__()
        self.interaction = interaction
        self.user_id = user_id
        self.user_data = schedule_manager.get_user_data(user_id)

        options = [discord.SelectOption(label=msg.title, value=str(i)) for i, msg in enumerate(self.user_data[1])]

        self.select = ui.Select(placeholder="Sélectionnez un message à supprimer", options=options)
        self.select.callback = self.select_message
        self.add_item(self.select)

    async def select_message(self, interaction):
        index = int(self.select.values[0])
        title = self.user_data[1][index].title
        schedule_manager.remove_message(self.user_id, index)
        await self.interaction.edit_original_response(content=f"Message **{title}** supprimé", view=None)

@bot.tree.command(name="pop", description="Supprimer un message programmé.")
async def pop(interaction):
    user_id = interaction.user.id
    if user_id in schedule_manager.storage and schedule_manager.storage[user_id][0] >= -1:
        view = PopSelect(interaction, user_id)
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

bot.run("YOUR_TOKEN")