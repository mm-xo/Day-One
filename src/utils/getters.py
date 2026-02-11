import database

def get_user_id(interaction):
    return interaction.user.id

def get_display_name(interaction):
    return interaction.user.display_name

def get_guild_id(interaction):
    return interaction.guild.id

async def get_timezone(user_id): # TODO
    return await database.db_get_user_timezone(user_id)