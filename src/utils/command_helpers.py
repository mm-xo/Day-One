# import discord

def validate_role(interaction, accepted_roles):
    roles = interaction.user.roles # list of roles
    for role in roles:
        if role.name in accepted_roles:
            return True
    return False

