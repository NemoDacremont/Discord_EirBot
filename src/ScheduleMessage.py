from dataclasses import dataclass
import datetime
import discord

@dataclass
class ScheduledMessage:
    title: str
    time: datetime.datetime
    channel: discord.TextChannel
    id: int
    repeat: str
