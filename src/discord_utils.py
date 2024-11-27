import discord

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
