import discord
import dateutils
import utils
import re


class ScheduleManager:
    def __init__(self):
        self.storage = {}

    def schedule_message(self, user_id, message):
        if user_id not in self.storage:
            self.storage[user_id] = [-1, []]

        self.add_message(user_id, message)

    def add_message(self, user_id, message):
        index = utils.binary_search(self.storage[user_id][1], message.time)
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
        if (match == None):
            return;

        if match.group(2) == "h":
            heures = int(match.group(1))
            return message.time + dateutils.relativedelta(hours=heures)
        elif match.group(2) == "j":
            jours = int(match.group(1))
            return message.time  + dateutils.relativedelta(days=jours)
        elif match.group(2) == "w":
            semaines = int(match.group(1))
            return message.time + dateutils.relativedelta(weeks=semaines)
        mois = int(match.group(1))
        return message.time + dateutils.relativedelta(months=mois)

