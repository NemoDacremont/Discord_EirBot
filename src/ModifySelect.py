import discord;
from discord import ui

from ModifyModal import ModifyModal

class ModifySelect(ui.View):
    def __init__(self, interaction, user_data):
        super().__init__()
        self.interaction = interaction
        self.user_data = user_data

        self.select = ui.Select(
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
