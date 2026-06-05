import pytest
from unittest.mock import Mock, AsyncMock
from utils.command_helpers import validate_role, is_command_in_server


def test_validate_role_user_has_accepted_role():
    role_mock = Mock()
    role_mock.name = "admin"

    interaction = Mock()
    interaction.user.roles = [role_mock]

    assert validate_role(interaction, ["admin"]) is True


def test_validate_role_user_has_one_of_multiple_accepted_roles():
    role1 = Mock()
    role1.name = "member"
    role2 = Mock()
    role2.name = "moderator"

    interaction = Mock()
    interaction.user.roles = [role1, role2]

    assert validate_role(interaction, ["admin", "moderator"]) is True


def test_validate_role_user_does_not_have_accepted_role():
    role_mock = Mock()
    role_mock.name = "member"

    interaction = Mock()
    interaction.user.roles = [role_mock]

    assert validate_role(interaction, ["admin", "moderator"]) is False


def test_validate_role_user_has_no_roles():
    interaction = Mock()
    interaction.user.roles = []

    assert validate_role(interaction, ["admin"]) is False


def test_validate_role_case_sensitive():
    role_mock = Mock()
    role_mock.name = "Admin"

    interaction = Mock()
    interaction.user.roles = [role_mock]

    assert validate_role(interaction, ["admin"]) is False
    assert validate_role(interaction, ["Admin"]) is True


def test_validate_role_with_empty_accepted_roles():
    role_mock = Mock()
    role_mock.name = "member"

    interaction = Mock()
    interaction.user.roles = [role_mock]

    assert validate_role(interaction, []) is False


@pytest.mark.asyncio
async def test_is_command_in_server_when_in_guild():
    interaction = AsyncMock()
    interaction.guild = Mock()

    result = await is_command_in_server(interaction)
    assert result is True
    interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_is_command_in_server_when_not_in_guild():
    interaction = AsyncMock()
    interaction.guild = None

    result = await is_command_in_server(interaction)
    assert result is False
    interaction.response.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_is_command_in_server_error_message_is_ephemeral():
    interaction = AsyncMock()
    interaction.guild = None

    await is_command_in_server(interaction)

    call_args = interaction.response.send_message.call_args
    assert call_args[1]["ephemeral"] is True
    assert "server" in call_args[0][0].lower()
