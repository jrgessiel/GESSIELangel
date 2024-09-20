import discord
from discord.ext import commands
import json, os

intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="GESSIELdemon ~ ", intents=intents)

def load_config():
    with open(os.path.join('main', r'data\config.json')) as f:
        return json.load(f)

def save_config(config):
    with open(os.path.join('main', r'data\config.json'), 'w') as f:
        json.dump(config, f, indent=4)

def load_changed_nicknames():
    with open(os.path.join('main', r'data\changed_nicknames.json'), 'r') as f:
        return set(json.load(f))

def save_changed_nicknames():
    with open(os.path.join('main', r'data\changed_nicknames.json'), 'w') as f:
        json.dump(list(bot.changed_nicknames), f)

@bot.event
async def on_ready():
    print(f'\nO robo: {bot.user.name} está em execução! \n')
    config = load_config()
    channel = bot.get_channel(config.get("receive_member_channel_id"))
    global MESSAGE_ID
    MESSAGE_ID = config.get("message_id")

    if channel and MESSAGE_ID:
        try:
            message = await channel.fetch_message(MESSAGE_ID)
            if message and message.author == bot.user and message.embeds and message.embeds[0].title == "Escolha seu cargo de Valorant!":
                return
        except discord.NotFound:
            pass

    embed = discord.Embed(
        title="Escolha seu cargo de Valorant!",
        description=(
            "Reaja com os emojis abaixo para receber o cargo correspondente:\n\n"
            "🛡️ - Sentinela\n"
            "⚔️ - Duelista\n"
            "🎯 - Iniciador\n"
            "💣 - Controlador\n\n"
            "**Troca de Nome:**\n\n"
            "Envie uma mensagem no formato `Nome ID` para trocar seu nome."
        ),
        color=discord.Color.blue()
    )
    message = await channel.send(embed=embed)
    MESSAGE_ID = message.id
    config["message_id"] = MESSAGE_ID
    save_config(config)
    for emoji in ['🛡️', '⚔️', '🎯', '💣']:
        await message.add_reaction(emoji)

@bot.event
async def on_member_join(member):
    config = load_config()
    channel = bot.get_channel(config.get("welcome_channel_id"))
    if channel:
        embed = discord.Embed(
            title="GESSIELdemon",
            description=f"""**Seja bem-vindo(a) ao meu servidor {member.mention}**. Agora você pode se conectar com todos os nossos outros membros. Fique à vontade para juntos participarem de eventos e ações dentro e fora dos jogos.""",
            color=discord.Color.from_rgb(230, 230, 250)
        )
        await channel.send(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    config = load_config()
    if payload.message_id == MESSAGE_ID and payload.channel_id == config.get("receive_member_channel_id"):
        if payload.user_id == bot.user.id:
            return  
        guild = bot.get_guild(payload.guild_id)
        role_name = {
            '🛡️': 'Sentinela',
            '⚔️': 'Duelista',
            '🎯': 'Iniciador',
            '💣': 'Controlador'
        }.get(str(payload.emoji))
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                role_member = discord.utils.get(guild.roles, name='Membro')
                member = guild.get_member(payload.user_id)
                if member:
                    await member.add_roles(role_member)
                    await member.add_roles(role)
                    print(f"\nO cargo de '{role_name}' foi adicionado ao usuario: {member.name}")

@bot.event
async def on_raw_reaction_remove(payload):
    config = load_config()
    if payload.message_id == MESSAGE_ID and payload.channel_id == config.get("receive_member_channel_id"):
        if payload.user_id == bot.user.id:
            return  
        guild = bot.get_guild(payload.guild_id)
        role_name = {
            '🛡️': 'Sentinela',
            '⚔️': 'Duelista',
            '🎯': 'Iniciador',
            '💣': 'Controlador'
        }.get(str(payload.emoji))
        if role_name:
            role_member = discord.utils.get(guild.roles, name='Membro')
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.remove_roles(role)
                    print(f"\nO cargo de '{role_name}' foi removido do usuario: {member.name}")

                    remaining_roles = [
                        discord.utils.get(guild.roles, name=r)
                        for r in ['Sentinela', 'Duelista', 'Iniciador', 'Controlador']
                    ]
                    if not any(role in member.roles for role in remaining_roles):
                        await member.remove_roles(role_member)
                        print(f"\nO cargo de 'Membro' foi removido do usuario: {member.name}")

@bot.event
async def on_message(message):
    config = load_config()
    if message.author == bot.user:
        return

    if message.channel.id == config.get("receive_member_channel_id"):
        parts = message.content.split(' ')
        member_name = message.author.display_name

        if len(parts) == 2:
            name, user_id = parts
            if message.author.id not in bot.changed_nicknames:
                new_nickname = f'{name} {user_id}'
                await message.author.edit(nick=new_nickname)
                await message.channel.send(f'O nome de {member_name} foi alterado para: {new_nickname}')
                print(f"\nO nome de {member_name} foi alterado para: {new_nickname}")
                bot.changed_nicknames.add(message.author.id)
                save_changed_nicknames()
                await message.channel.set_permissions(message.author, send_messages=False)
            else:
                await message.channel.send(f'O usuário {member_name} já alterou seu nome.')
                print(f"\nO usuário {member_name} já alterou seu nome.")
        else:
            return
    else:
        await bot.process_commands(message)

bot.changed_nicknames = load_changed_nicknames()

config = load_config()
bot.run(config.get("discord_tk"))
