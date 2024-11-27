from discord import ui
import discord

from ScheduleManager import ScheduleManager


class PopSelect(ui.View):
    def __init__(self, interaction, user_id, schedule_manager: ScheduleManager):
        super().__init__()
        self.interaction = interaction
        self.user_id = user_id
        self.schedule_manager = schedule_manager
        self.user_data = schedule_manager.get_user_data(user_id)

        options = [discord.SelectOption(label=msg.title, value=str(i)) for i, msg in enumerate(self.user_data[1])]

        self.select = ui.Select(placeholder="Sélectionnez un message à supprimer", options=options)
        self.select.callback = self.select_message
        self.add_item(self.select)

    async def select_message(self, interaction):
        index = int(self.select.values[0])
        title = self.user_data[1][index].title
        self.schedule_manager.remove_message(self.user_id, index)
        await self.interaction.edit_original_response(content=f"Message **{title}** supprimé", view=None)
