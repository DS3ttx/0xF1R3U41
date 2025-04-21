from fireuai_db import FireuaiDB
from dotenv import load_dotenv
from log import log_setup

import os
import traceback

import discord
from discord.ext import commands

load_dotenv()

# Read keys
user_db = os.getenv("DB_USERNAME")
pass_db = os.getenv("DB_PASSWORD")
name_db = os.getenv("DB_DATABASE")
bot_id = os.getenv("DC_KEY")

# Construct debugger
debugger = log_setup()

# Construct Database
database = FireuaiDB(user_db, pass_db, name_db)

# Define bot Permissions
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)


@client.event
async def on_ready():
    """Check if the bot is online"""
    print(f'O Bot {client.user} está online!')


@client.command(aliases=["Register"])
async def register(ctx):
    """Register a member into database"""

    user_id = str(ctx.author.id)

    try:
        if database.user_exists(user_id):
            await ctx.reply("Você já está registrado!")
            return

        debugger.info(f"New user register: {user_id} {ctx.author.name}")

        database.user_register(user_id, ctx.author.name)
        await ctx.reply("Seu perfil foi criado com sucesso!")
    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro no seu registro! Procure um moderador.")
        return


@client.command(aliases=["Ranking", "r"])
async def ranking(ctx):
    """Show 20 top users on points system"""

    try:
        rank = database.ranking_by_points()
        ranking_final = "----- Ranking -----\n"

        position = 0
        for user_point in rank:
            ranking_final += f"{position}. {user_point['nickname']} - {user_point['points']} pontos\n"

        # Handles discord char limits
        if len(ranking_final) > 2000:
            ranking_final = ranking_final[:1997] + "..."

        await ctx.reply(ranking_final)

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro ao gerar o ranking!\nContate um moderador")
        return


@client.command(aliases=["RankingEvent", "re"])
async def ranking_by_event(ctx, attempt: str):
    """Show 20 top users inside a event on points system"""

    try:
        rank = database.ranking_by_event(attempt)
        ranking_final = "----- Ranking -----\n"

        position = 0
        for user_point in rank:
            ranking_final += f"{position}. {user_point['nickname']} - {user_point['total_points']} pontos\n"

        # Handles discord char limits
        if len(ranking_final) > 2000:
            ranking_final = ranking_final[:1997] + "..."

        await ctx.reply(ranking_final)

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro ao gerar o ranking!\nContate um moderador")
        return


@client.command(aliases=["RankingSemanal", "rs"])
async def ranking_weekly(ctx):
    """Show 20 top users inside a weekly chalenges on points system"""

    await ranking_by_event(ctx, "Desafios_Semanais")
    return


@client.command(aliases=["MakeFlag", "mf"])
async def make_flag(ctx, name_flag: str, flag_str: str, points_flag: str, event_name: str | None = None):
    """Make a flag if user is admin"""

    user_id = str(ctx.author.id)

    try:
        if not database.user_is_admin(user_id):
            await ctx.reply("Você não tem permissões de administrador!")
            return

        if not str(points_flag).isnumeric():
            await ctx.reply("O valor de `points_flag` deve ser um número!")
            return

        if database.create_flag(name_flag, flag_str, int(points_flag), event_name, user_id) is None:
            await ctx.reply("A `flag` ou `NameFlag` que você tentou criar já existia!")
            return

        await ctx.reply(f"A flag {name_flag} foi criada com sucesso!")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro ao criar a flag!\nContate um moderador")
        return


@client.command(aliases=["Flag", "f"])
async def flag(ctx, attempt: str):
    """Claims a Flag"""

    user_id = str(ctx.author.id)

    try:
        if not database.user_exists(user_id):
            await ctx.reply("Você não está registrado! Use !Register primeiro.")
            return

        try_reward = database.reward_flag(user_id, attempt)

        if try_reward is None:
            await ctx.reply("Flag incorreta!")
            return

        await ctx.reply(try_reward)
        return

    except AssertionError:
        await ctx.reply("Você já resgatou esta flag!")
        return

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro ao resgatar a flag!\nContate um moderador")
        return


@client.command(aliases=["ActiveFlags", "af"])
async def active_flags(ctx):
    """Get all active flags and expiration date"""

    try:
        flags = database.get_flags()

        response_final = f"```{'Desafio':<20} | {'Pontos':<5} | {'Evento':<25} | {'Validade'}\n"
        response_final += "-" * 70 + "\n"  # linha de separação

        for flag_info in flags:
            response_final += f"{flag_info['Desafio']:<20} | {flag_info['Pontos']:<5} | {flag_info['Evento']:<25} | {flag_info['Validade']}\n"

        response_final += "```"

        # Handles discord char limits
        if len(response_final) > 2000:
            response_final = response_final[:1994] + "...\n```"

        await ctx.reply(response_final)
        return

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro ao consultar as flags!\nContate um moderador")
        return


@client.command(aliases=["RemainingFlags", "rf"])
async def remaining_flags(ctx):
    """Get all active flags remaining for the user and the expiration date"""

    user_id = str(ctx.author.id)

    try:
        flags = database.get_remaining_flags(user_id)

        if len(flags) == 0:
            await ctx.reply("Parabéns! Não há nenhuma flag ativa que você deixou de capturar!")
            return

        response_final = f"```{'Desafio':<20} | {'Pontos':<5} | {'Evento':<25} | {'Validade'}\n"
        response_final += "-" * 70 + "\n"  # linha de separação

        for flag_info in flags:
            response_final += f"{flag_info['Desafio']:<20} | {flag_info['Pontos']:<5} | {flag_info['Evento']:<25} | {flag_info['Validade']}\n"

        response_final += "```"

        # Handles discord char limits
        if len(response_final) > 2000:
            response_final = response_final[:1994] + "...\n```"

        await ctx.reply(response_final)
        return

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro ao consultar as flags!\nContate um moderador")
        return


@client.command(aliases=["Solves", "s"])
async def solves(ctx, challenge: str):
    """Show how many solutions the challange have actualy"""

    try:
        flag_solves = database.get_rewards_number_flag(challenge)
        await ctx.reply(f"Atualmente o desafio {challenge} tem {flag_solves} soluções!")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar as soluções!\nContate um administrador")
        return


@client.command(aliases=["First", "fs"])
async def first(ctx, challenge: str):
    """Shows who is the first to win a challenge"""

    try:
        first_solve = database.get_blooded_flag(challenge)

        if first_solve is None:
            await ctx.reply(f"Ninguém resolveu o desafio {challenge} ainda!")
            return

        await ctx.reply(
            f"<@{first_solve['id']}> foi o primeiro a resolver o desafio __{challenge}__! Solucionado em: {first_solve['solved_at']}")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar as soluções!\nContate um administrador")
        return


@client.command(aliases=["Points", "p"])
async def points(ctx):
    """Show how many points the user have"""

    user_id = str(ctx.author.id)

    try:
        user_points = database.get_user_points(user_id)
        await ctx.reply(f"Você atualmente tem {user_points} pontos!")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar os pontos!\nContate um administrador")
        return


@client.command(aliases=["Coins", "c"])
async def coins(ctx):
    """Show how many coins the user have"""

    user_id = str(ctx.author.id)

    try:
        user_coins = database.get_user_coins(user_id)
        await ctx.reply(f"Você atualmente tem {user_coins} moedas!")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar os pontos!\nContate um administrador")
        return


@client.command(aliases=["HasHints", "hh"])
async def has_hints(ctx, challenge: str):
    """Show if a challenge has hints available"""

    user_id = str(ctx.author.id)

    try:
        search = database.exists_hint_flag(challenge)

        if search[0]:
            await ctx.reply(f"Uma dica normal está disponível para {challenge} por 1000 moedas!")

        if search[1]:
            await ctx.reply(f"Uma dica plus está disponível para {challenge} por 2000 moedas!")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar as dicas!\nContate um administrador")
        return


@client.command(aliases=["CreateHints", "ch"])
async def create_hints(ctx, challenge: str, type_hint: str, text: str):
    """Create a hint from a challenge if user is admin."""

    if not (type_hint == "basic" or type_hint == "plus"):
        await ctx.reply("O parâmetro type_hint deve ser 'basic' ou 'plus'.")
        return

    user_id = str(ctx.author.id)

    try:
        if not database.user_is_admin(user_id):
            await ctx.reply("Você deve ter permissões administrativas para este comando!")
            return

        search = database.exists_hint_flag(challenge)

        if search[0] and type_hint == 'basic':
            await ctx.reply(f"Uma dica 'basic' já está disponível para {challenge}!")
            return

        if search[1] and type_hint == 'plus':
            await ctx.reply(f"Uma dica 'plus' já está disponível para {challenge}!")
            return

        database.create_hint(challenge, type_hint == 'plus', text)
        await ctx.reply(f"Você criou uma dica {type_hint} com sucesso para {challenge}!")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar as dicas!\nContate um administrador")
        return


@client.command(aliases=["Hint", "h"])
async def hint(ctx, challenge: str, type_hint: str):
    """Reward a Hint plus or basic (type) for a challenge using coins"""

    if not (type_hint == "plus" or type_hint == "basic"):
        await ctx.reply(f"Não consegui entender o tipo da dica desejada! Atualmente temos os tipos 'basic' e 'plus'")
        return

    user_id = str(ctx.author.id)

    try:
        is_plus = type_hint == 'plus'

        user_coins = database.get_user_coins(user_id)
        require = 2000 if is_plus else 1000

        if user_coins < require:
            await ctx.reply(f"Você não tem moedas suficientes para esta operação! Saldo: {user_coins}")
            return

        exist_hint = database.exists_hint_flag(challenge)

        if is_plus and not exist_hint[1]:
            await ctx.reply(f"Atualmente o desafio {challenge} não tem dicas 'plus'.")
            return

        if not is_plus and not exist_hint[0]:
            await ctx.reply(f"Atualmente o desafio {challenge} não tem dicas 'basic'.")
            return

        database.subtract_user_coins(user_id, require)
        hint_txt = database.get_hint_flag(challenge, is_plus)
        await ctx.reply(hint_txt)

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar os pontos!\nContate um administrador")
        return


client.run(bot_id)
