import sqlite3
import discord
from discord.ext import commands
import random
import datetime
import asyncio
import json

bot = commands.Bot(command_prefix="!", description="!commands")

conn = sqlite3.connect("database.db")
c = conn.cursor()

jackpot_joined = {} #user_id amount


async def update_balance(id, amount, type):
    credits = await get_credits(id, 0)
    c.execute(f"DELETE FROM credits WHERE id={id}")
    conn.commit()
    if credits is None:
        credits = [0]
    if type == "plus":
        c.execute(f"INSERT INTO credits VALUES ({credits[0]+float(amount)},{id} )")
    else:
        c.execute(f"INSERT INTO credits VALUES ({credits[0] - float(amount)},{id} )")
    conn.commit()

async def get_credits(id, type):
     #credits #id
    if type == 0:
        c.execute(f"SELECT * FROM credits WHERE id={id}")
        return c.fetchone()
    else:
        c.execute(f"SELECT * FROM credits")
        return c.fetchall()


async def get_name(id):
    user = await bot.get_user_info(id)
    return user.name


async def run_jackpot(time):
    await asyncio.sleep(1)
    if time == 0:
        pass#remove coins
        return 0
    time -= 1
    if time == 0:
        await get_winner()


async def get_winner():
    pot = 0
    percentage = {}
    for id in jackpot_joined:
        pot += jackpot_joined[id]
    winner = random.randint(0, 100)
    percentage[id] = pot / jackpot_joined[id]
    for id in percentage:
        if percentage[id] == winner:
            await update_balance(id, pot, "plus")
            jackpot_joined[id].pop()
            return 0
    for id in jackpot_joined:
        await update_balance(id, jackpot_joined[id], "minus")


@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))


@bot.command()
async def credits(ctx, user=None ):
    credits = 0
    credit_embed = discord.Embed(color=discord.Color.blurple())
    if user is None:
        credits = await get_credits(ctx.message.author.id, 0)
    else:
        credits = await get_credits(user.id, 0)
    credit_embed.add_field(name=str(ctx.message.author) + " Credits", value="Current amount of Credits: " + str(credits[0]))
    await ctx.send(embed=credit_embed)


@bot.command()
async def top(ctx):
    length = 10
    user = await  get_credits(ctx.message.author.id, 1)
    user = sorted(user)
    stats_embed = discord.Embed(color=discord.Color.blue())
    if len(user) < 10:
        length = len(user)
    for x in range(0, length):
        stats_embed.add_field(name=await get_name(ctx.message.author.id), value=user[x][0], inline=False)
    await ctx.send(embed=stats_embed)


@bot.command()
async def setcredits(ctx, user : discord.Member, amount):
    await update_balance(user, amount, "plus")
    await ctx.send("Balance has been updated!")

@bot.command()
async def sendcredits(ctx, user : discord.Member, amount):
    credits = await get_credits(user.id, 0)
    print(credits)
    print(amount)
    if int(amount) > credits[0]:
        await ctx.send(content="You need more credits!")
        return 1
    await update_balance(ctx.message.author, amount, "minus")
    await update_balance(user, amount, "plus")
    await ctx.send(content=amount + " credits are sent to " + str(user))


@bot.command()
async def daily(ctx):
    c.execute(f"SELECT * FROM daily WHERE id={ctx.message.author.id}")
    time_stamp = c.fetchone()
    time = datetime.datetime.now()
    if time > time_stamp[1]+datetime.timedelta(hours=12):
        await update_balance(ctx.message.author, config['daily'], "plus")
        c.execute(f"DELETE FROM daily WHERE id={ctx.message.author.id}")
        conn.commit()
        c.execute(f"INSERT INTO daily VALUES({ctx.message.author.id}, {datetime.datetime.now()})")
        conn.commit()
    else:
        await ctx.send(content="You need to wait untill you can run this command again!")


@bot.command()
async def jackpot(ctx, time):
    time_finish = datetime.datetime.now() + datetime.timedelta(seconds=int(time))
    jackpot_embed = discord.Embed(title="Amplify Jackpot!", color=discord.Color.blurple())
    jackpot_embed.add_field(name="Join", value="**To join the chackpot type the amount of credits you would like to bet.**")
    jackpot_embed.add_field(name="Pot", value="0  Credits")
    jackpot_embed.set_footer(text="Ends at " + time_finish.strftime("%d.%m.%Y %H:%M"))
    await ctx.send(embed=jackpot_embed)


@bot.command()
async def join(ctx, amount):
    if amount > await get_credits(ctx.message.author.id, 0):
        await ctx.send(content="You need more credits! :(")
        return 1
    jackpot_joined[ctx.message.author.id] = amount


@bot.command()
async def coinflip(ctx, amount):
    number = random.randint(0, 1)#0 winn | 1 lose
    if number == 0:
        await update_balance(ctx.message.author.id, amount, "minus")
    if number == 1:
        await update_balance(ctx.message.author.id, amount*2, "plus")



@bot.event
async def on_member_join(member):
    c.execute(f"INSERT INTO credits VALUES({7500}, {member.id})")
    c.execute(f"INSERT INTO daily VALUES({member.id}, {datetime.datetime.now()})")
    conn.commit()


bot.run()
