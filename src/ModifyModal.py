from discord import ui
import discord_utils
import utils

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
        time_test = utils.time_input_test(self.time_input.value)
        date_test = utils.date_input_test(self.date_input.value)
        repeat_test = utils.repeat_input_test(self.repeat_input.value)
        channel = discord_utils.parse_channel(self.message.channel.guild, self.channel_input.value)

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
                        f"- **Horaire** : {utils.format_datetime(self.message.time)}\n" \
                        f"- **Récurrence** : {self.message.repeat}\n" \
                        f"- **Channel** : {self.message.channel.mention}\n"
            )

            self.reorder_storage()

        await interaction.response.defer()

    def update_fields(self, channel):
        self.message.title = self.title_input.value
        self.message.time = utils.parse_time(self.time_input.value, self.date_input.value)
        self.message.repeat = self.repeat_input.value
        self.message.channel = channel

    def reorder_storage(self):
        del self.user_data[1][self.index]
        index = utils.binary_search(self.user_data[1], self.message.time)
        self.user_data[1][index:index] = [self.message]
