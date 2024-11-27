from discord import ui
from ScheduleManager import ScheduleManager
from ScheduleMessage import ScheduledMessage
import utils

class ScheduleModal(ui.Modal, title="Eirbizarre"):
    def __init__(self, interaction, schedule_manager: ScheduleManager):
        super().__init__()
        self.interaction = interaction
        self.schedule_manager = schedule_manager

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
        time_test = utils.time_input_test(self.time_input.value)
        date_test = utils.date_input_test(self.date_input.value)
        repeat_test = utils.repeat_input_test(self.repeat_input.value)

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

        dtime = utils.parse_time(self.time_input.value, self.date_input.value)

        await interaction.user.send(
            f"**Nouveau message programé**\n"
            f"- **Titre** : {self.title_input.value}\n"
            f"- **Horaire** : {utils.format_datetime(dtime)}\n"
            f"- **Récurrence** : {self.repeat_input.value if self.repeat_input.value else '0'}\n"
            f"- **Channel** : {interaction.channel.mention}\n"
            f"**Veuillez écrire son contenu**"
        )

        message = ScheduledMessage(
            title=self.title_input.value,
            time=dtime,
            channel=interaction.channel,
            id=-1,
            repeat=self.repeat_input.value if self.repeat_input.value else "0",
        )
        self.schedule_manager.schedule_message(interaction.user.id, message)

        await interaction.response.defer()
