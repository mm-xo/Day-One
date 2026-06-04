

# ============================================================================================
def validate_role(interaction, accepted_roles):
    roles = interaction.user.roles # list of roles
    for role in roles:
        if role.name in accepted_roles:
            return True
    return False
# ============================================================================================


# ============================================================================================
async def is_command_in_server(interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return False
    return True
# ============================================================================================