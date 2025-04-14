from database import FireUAIDB
from log import log_setup

import sys
import traceback

import discord
from discord.ext import commands

# Read arguments
user_db = sys.argv[1]
pass_db = sys.argv[2]
name_db = sys.argv[3]
bot_id = sys.argv[4]

# Construct debugger
debugger = log_setup()

# Construct Database
database = FireUAIDB(user_db, pass_db, name_db)

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
        await ctx.reply(try_reward)
        return

    except AssertionError:
        await ctx.reply("Você já resgatou esta flag!")
        return

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Ocorreu um erro ao resgatar a flag!\nContate um moderador")
        return


@client.command(aliases=["Points", "p"])
async def points(ctx):
    user_id = str(ctx.author.id)

    try:
        user_points = database.get_user_points(user_id)
        await ctx.reply(f"Você atualmente tem {user_points} pontos!")

    except Exception as error:
        debugger.critical(traceback.format_exc())
        await ctx.reply("Erro ao consultar os pontos!\nContate um administrador")
        return


client.run(bot_id)
