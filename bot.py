import os
import psycopg2
import time
import nacl
import discord

import datetime

from discord.ext import commands

TOKEN = 'ВАШ DISCORD API ТОКЕН'

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)


con = psycopg2.connect(
  database="ВАШЕ ИМЯ БД", 
  user="ВАШ ПОЛЬЗОВАТЕЛЬ БД", 
  password="ВАШ ПАРОЛЬ ОТ БД", 
  host="127.0.0.1", 
  port="5432"
)

async def send_spam(file = None):
	cur = con.cursor()
	cur.execute("SELECT id FROM channels;")
	rows = cur.fetchall()
	con.commit()
	if file is None:
		file = "MSG.txt"
#	msg_l = []
	text = ""
	with open(file, 'r', encoding='utf-8') as f:
		text = f.read()
	for row in rows:
		channel = bot.get_channel(id=row[0])
		try:
			await msg_l.append(channel.send(text))
		except Exception as e:
			print(e)
#	for msg in msg_l:
#		await msg

@bot.command(pass_context=True) 
async def message_of_day(ctx, *files):
	'''может быть вызвана только создателем бота. Выполняет рассылку сообщения дня во все зарегестрированные каналы. Сообщение содержит информацию об обновлении или о временном выключении бота'''
	await ctx.message.delete();
	if ID создателя бота :) != ctx.author.id:
		return
	if len(files) > 0:
		await send_spam(files[0])
	else:
		await send_spam()

async def play(ctx, sound, banned, mute = False):
	if mute or ctx.author.voice is None:
		return
	if (not banned is None) and (ctx.author.voice.channel.id in banned):
		return
	vc = await ctx.author.voice.channel.connect()
	vc.play(discord.FFmpegPCMAudio(sound))	
	while vc.is_playing():
		time.sleep(0.2)
	await vc.disconnect()

# Возвращает информацию о канале из БД по его ID
def channel_by_id(ID):
	cur = con.cursor()
	cur.execute("SELECT * FROM channels where id = %i" % ID)
	rows = cur.fetchall()
	con.commit()	
	if len(rows) == 0:
		return None
	else:
		return rows[0]
# получает объект пользователя по id
def get_user(ctx, id):
	ret = ctx.guild.get_member(id)
	if ret is None:
		return bot.get_user(id)
	return ret

# Возвращает список объектов преподов по ID канала 
def queues_by_id(ID, t_id = None):
	cur = con.cursor()
	if t_id is None:
		cur.execute("SELECT * FROM q_teachers where ch_id = %i" % ID)
	else:
		cur.execute("SELECT * FROM q_teachers where ch_id = %i and id = %i" % (ID, t_id))		
	rows = cur.fetchall()
	con.commit()	
	return rows

# Возвращает true, если отправитель может менять каналы
def has_prem(ctx):
	return ctx.author.permissions_in(ctx.channel).manage_channels

def log(ctx):
	str = "%s {%i} (%i): %s" % (datetime.datetime.now().strftime("[%d.%m.%Y %H:%M]"), ctx.channel.id, ctx.author.id, ctx.message.content)
	with open('log.txt', 'a', encoding='utf-8') as f:
		f.write('\n')
		f.write(str)

async def update_table(ctx):
	id = ctx.channel.id
	ch_i = channel_by_id(id)
	if ch_i is None:
		return
	msg = "======\n**%s**\n" % ch_i[2]
	tes = queues_by_id(id)
	for tet in tes:
		msg += "Очередь к *%s*:\n```" % get_user(ctx, tet[1]).display_name
		if len(tet[2]) == 0:
			msg += "\n*никто не пришел на мою фан-встречу* :("
		I = 1
		for st in tet[2]:			
			msg += "\n%i. %s" % (I, get_user(ctx, st).display_name)
			I += 1
		msg += "\n```"
	msg += "======"
	if ch_i[1] is None:
		mesa = await ctx.send(msg)
		cur = con.cursor()
		cur.execute("UPDATE channels SET last_message = %i WHERE id = %i" % (mesa.id, id))
		con.commit()
	else:
		mesa = await ctx.channel.fetch_message(ch_i[1])
		await mesa.edit(content = msg)
		

@bot.command(pass_context=True) 
async def forget(ctx):
	'''Эта команда регистрирует данный текстовый канал в системе'''
	log(ctx)
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return
	row = channel_by_id(ctx.channel.id)
	if row is None:
#		await play(ctx, 'мэв/init.mp3')
		await ctx.send("[%s] Канал ещё не был зарегистрирован до этого" % ctx.author.display_name);
	else:
		cur = con.cursor()
		cur.execute("DELETE FROM channels WHERE id = %i" % ctx.channel.id)
		cur.execute("DELETE FROM q_teachers WHERE ch_id = %i" % ctx.channel.id)
		con.commit()
		await ctx.send("[%s] Канал успешно удалён из системы" % ctx.author.display_name);



@bot.command(pass_context=True) 
async def init(ctx):
	'''Эта команда удаляет данный текстовый канал из системы. Все настройки так же удаляются. Желательно, но не обязательно, выполнить команду при удалении бота с сервера'''
	log(ctx)
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return
	row = channel_by_id(ctx.channel.id)
	if row is None:
		cur = con.cursor()
		cur.execute("INSERT INTO channels VALUES(%i, NULL, 'header', '{}', 'мэв', false, '{}')" % (ctx.channel.id))
		con.commit()
		await ctx.send("[%s] Канал успешно зарегистрирован" % ctx.author.display_name);
		await play(ctx, 'мэв/init.mp3', [])
	else:
		await ctx.send("[%s] Канал уже был зарегистрирован до этого" % ctx.author.display_name);

@bot.command(pass_context=True) 
async def заголовок(ctx, head):
	'''Эта команда меняет заголовок очереди. Если в названии есть пробелы, то его нужно указать в кавычках'''
	log(ctx)
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return
	id = ctx.channel.id
	row = channel_by_id(id)
	if row is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
	else:
		hero = row[4]
		PLAY = play(ctx, '%s/header.mp3'%hero, row[6], row[5])
		cur = con.cursor()
		cur.execute("UPDATE channels SET header = '%s' WHERE id = %i" % (head, id))
		con.commit()
		await ctx.send("Заголовок успешно изменен. Новый заголовок очереди: '%s'" % head);
		await update_table(ctx);
		await ctx.message.delete();
		await PLAY



@bot.command(pass_context=True) 
async def добавить_препода(ctx, *teachers):
	'''Эта команда добавляет упомянутых преподавателей в список очередей. Все неупомянания будут игнорироватся [упомянание начинается на @)))]'''
	log(ctx)
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return
	id = ctx.channel.id
	row = channel_by_id(id)
	if row is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
	else:
		alrd = row[3]
		hero = row[4]
		PLAY = play(ctx, '%s/add_teacher.mp3' % hero, row[6], row[5])
		I = 0
		cur = con.cursor()
		for tea in teachers:
			if not tea.startswith('<@') or not tea.endswith('>'):
				continue
			tet = tea[2:-1];
			if tet.startswith('!'):
				tet = tet[1:]
			tet = int(tet)
			if tet in alrd:
				continue
			alrd.append(tet)
			cur.execute("UPDATE channels SET teachers = teachers||%i WHERE id = %i;" % (tet, id))
			cur.execute("INSERT INTO q_teachers VALUES (%i, %i, '{}');" % (id, tet))
			I += 1
		con.commit()
		await ctx.send("[%s] %i преподавателей успешно добавлены" % (ctx.author.display_name, I));
		await update_table(ctx);
		await ctx.message.delete();
		await PLAY
		
@bot.command(pass_context=True) 
async def изгнать_препода(ctx, *teachers):
	'''Эта команда удаляет упомянутых преподавателей из списка очередей. Все неупомянания будут игнорироватся [упомянание начинается на @)))]'''
	log(ctx)
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return
	id = ctx.channel.id
	row = channel_by_id(id)
	if row is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
	hero = row[4]
	PLAY = play(ctx, '%s/remove_teacher.mp3'%hero, row[6], row[5])
	cur = con.cursor()
	for tea in teachers:
		if not tea.startswith('<@') or not tea.endswith('>'):
			continue
		tet = tea[2:-1]
		if tet.startswith('!'):
			tet = tet[1:]
		tet = int(tet)
		cur.execute("UPDATE channels SET teachers = array_remove(teachers, %i) WHERE id = %i;" % (tet, id))
		cur.execute("DELETE FROM q_teachers WHERE ch_id = %i AND id = %i" % (id, tet))
	con.commit()
	await ctx.send("[%s] Преподаватели успешно удалены" % ctx.author.display_name);
	await update_table(ctx);
	await ctx.message.delete();
	await PLAY


@bot.command(pass_context=True) 
async def к(ctx, *teachers):
	'''Эта команда добавляет вызвавшего в очередь к упомянутому преподавателю'''
	log(ctx)
	if len(teachers) != 1:
		await ctx.send("[%s] Вы должны упомянуть преподавателя. Упомянание начинается на @)))" % ctx.author.display_name);
		return	
	teacher = teachers[0]
	if not teacher.startswith('<@') or not teacher.endswith('>'):
		await ctx.send("[%s] Вы должны упомянуть преподавателя. Упомянание начинается на @)))" % ctx.author.display_name);
		return	
	id = ctx.channel.id
	
	ttr = teacher[2:-1]
	
	if ttr.startswith("!"):
		ttr = ttr[1:]
	
	ch_i = channel_by_id(id)
	if ch_i is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
	hero = ch_i[4]
	
	rows = queues_by_id(id)
	if rows is None or len(rows) == 0:
		await ctx.send("[%s] Похоже, на сервере нет преподователей (см. !help добавить_препода)" % ctx.author.display_name);
		return
	cont = False
	author = ctx.author.id
	tid = int(ttr)
	is_in = True
	for tea in rows:
		if author in tea[2]:
			cont = True
			break
		if tea[1] == tid:
			is_in = False
			
	if cont:
		await ctx.send("[%s] Умный слишком дофига? Можно быть только в одной очереди за раз!" % ctx.author.display_name);
		return		
	if is_in:
		await ctx.send("[%s] А я не знаю такого преподавателя (см. !help добавить_препода)" % ctx.author.display_name);
		return	
	
	PLAY = play(ctx, '%s/enqueue.mp3' % hero, ch_i[6], ch_i[5])
	
	cur = con.cursor()
	cur.execute("UPDATE q_teachers SET students = students||%i WHERE ch_id = %i AND id = %i" % (author, id, tid))
	con.commit()
	await ctx.send("[%s] %s успешно добавлен в очедь к %s" % (ctx.author.display_name, ctx.author.display_name, get_user(ctx, tid).display_name));
	await update_table(ctx);
	await ctx.message.delete();
	await PLAY


@bot.command(pass_context=True) 
async def прочь(ctx):
	'''Эта команда удаляет вызвавшего из очередей'''
	log(ctx)
	id = ctx.channel.id
	row = channel_by_id(id)
	if row is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
		
	author = ctx.author.id		
	
	rows = queues_by_id(id)
	cont = False
	for tea in rows:
		if author in tea[2]:
			cont = True
			break

	if not cont:
		if author == ID ВАШЕГО ИВАНОВА: # ID дискорд аккаунта Иванова)
			await ctx.send("[%s] Иванов, хватит спамить :) (см. !help к)" % ctx.author.display_name);
		else:
			await ctx.send("[%s] Что бы выйти из очереди, в нее сначала надо зайти :) (см. !help к)" % ctx.author.display_name);
		return
	
	hero = row[4]
	PLAY = play(ctx, '%s/dequeue.mp3' % hero, row[6], row[5])
	author = ctx.author.id		
	cur = con.cursor()
	for tea in row[3]:
		cur.execute("UPDATE q_teachers SET students = array_remove(students, %i) WHERE ch_id = %i AND id = %s" % (author, id, tea))
	con.commit()

	await ctx.send("[%s] %s успешно исключён из очереди" % (ctx.author.display_name, ctx.author.display_name));
	await update_table(ctx);
	await ctx.message.delete();
	await PLAY
	
@bot.command(pass_context=True) 
async def список(ctx, *teachers):
	'''Эта переносит список в конец истории сообщений'''
	log(ctx)
	id = ctx.channel.id
	ch_i = channel_by_id(id)
	if ch_i is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
	hero = ch_i[4]
	
	PLAY = play(ctx, '%s/list.mp3'%hero, ch_i[6], ch_i[5])	
	msg = "======\n**%s**\n" % ch_i[2]
	tes = queues_by_id(id)
	for tet in tes:
		msg += "Очередь к *%s*:\n```" % get_user(ctx, tet[1]).display_name
		if len(tet[2]) == 0:
			msg += "\n*никто не пришел на мою фан-встречу* :("
		I = 1
		for st in tet[2]:
			msg += "\n%i. %s" % (I, get_user(ctx, st).display_name)
			I += 1
		msg += "\n```"
	if not ch_i[1] is None:
		MSG = await ctx.channel.fetch_message(ch_i[1])
		await MSG.delete()
	msg += "======"
	mes = await ctx.send(msg);
	cur = con.cursor()
	cur.execute("UPDATE channels SET last_message = %i WHERE id = %i" % (mes.id, id))
	con.commit()
	await ctx.message.delete();
	await PLAY


@bot.command(pass_context=True) 
async def далее(ctx):
	'''Эта команда вызывается преподавателем. Она перетягивает следующего студента из очереди в голосовой канал преподавателя'''	
	log(ctx)
	id = ctx.channel.id
	
	ch_i = channel_by_id(id)
	if ch_i is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
	hero = ch_i[4]
	
	author = ctx.author.id		
	rows = queues_by_id(id, author)
	if len(rows) != 1:
		await ctx.send("[%s] Вы точно перподаватель?) (см. !help добавить_препода)" % ctx.author.display_name)
		return
	row = rows[0]
	
	if len(row[2]) == 0:
		await ctx.send("[%s] У вас и так нет никого в очереди)" % ctx.author.display_name)
		await play(ctx, '%s/empty.mp3'%hero)
		return
		
	
	st = row[2][0]
	
	cur = con.cursor()
	cur.execute("UPDATE q_teachers SET students = array_remove(students, %i) WHERE ch_id = %i AND id = %s" % (st, id, author))
	con.commit()
	
	to_add = get_user(ctx, st)
	await ctx.send("[%s] %s, добро пожаловать в ад)" % (ctx.author.display_name, to_add.mention))
	if not ctx.author.voice is None:
		try:
			await to_add.move_to(ctx.author.voice.channel)
		except Exception as e:
			print (e)
			await ctx.send("[%s] %s, Ну, в голосовой канал сам себя перенесеш, ок да)" % c(tx.author.display_name, to_add.display_name))

	if len(row[2]) > 1:	
		await ctx.send("%s, готовься, ты следующий)" % get_user(ctx, row[2][1]).mention)
	
	PLAY = play(ctx, '%s/next.mp3'%hero, ch_i[6], ch_i[5])
	await update_table(ctx);
	await ctx.message.delete();
	await PLAY

@bot.command(pass_context=True) 
async def яспать(ctx):
	'''Эта команда вызывается преподавателем. Она очищает очередь'''	
	log(ctx)
	
	id = ctx.channel.id
	
	ch_i = channel_by_id(id)
	if ch_i is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
	hero = ch_i[4]
	
	author = ctx.author.id		
	rows = queues_by_id(id, author)
	if len(rows) != 1:
		await ctx.send("[%s] Вы точно перподаватель?) (см. !help добавить_препода)" % ctx.author.display_name)
		return
	row = rows[0]
	
	if len(row[2]) == 0:
		await ctx.send("[%s] У вас и так нет никого в очереди)" % ctx.author.display_name)
		await play(ctx, '%s/empty.mp3' % hero,  ch_i[6],  ch_i[5])
		return
	PLAY = play(ctx, '%s/finish.mp3'%hero, ch_i[6], ch_i[5])
	
	cur = con.cursor()
	cur.execute("UPDATE q_teachers SET students = '{}' WHERE ch_id = %i AND id = %s" % (id, author))
	con.commit()
	
	Ment = ""
	for st in row[2]:
		Ment += "%s, " % get_user(ctx, st).mention	
	await ctx.send("[%s] %sсвободны. %s больше не принимает сегодня)" % (ctx.author.display_name, Ment, ctx.author.display_name))
	
	await update_table(ctx);
	await ctx.message.delete();
	await PLAY
	
	

@bot.command(pass_context=True) 
async def голос(ctx, hero_num):
	'''Сменить героя озвучки. 0 - Мэв, 1 - Повелитель Могил, 2 - Рохан (Ловец Духов), 3 - Артас (Рыцарь Смерти)'''
	log(ctx)
	
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return
	id = ctx.channel.id
	
	ch_i = channel_by_id(id)
	if ch_i is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
	try:
		hero_num = int(hero_num)
	except Exception as e:
		await ctx.send("[%s] необходимо ввести число от 0 до 3 (см. !help голос)" % ctx.author.display_name)
		print(e)
		return		
	if not hero_num in range(0, 4):
		await ctx.send("[%s] необходимо ввести число от 0 до 3 (см. !help голос)" % ctx.author.display_name)
		return
	PLAY = None
	hero_n = ""
	cur = con.cursor()
	if hero_num == 0:
		PLAY = play(ctx, "мэв/init.mp3", ch_i[6])
		cur.execute("UPDATE channels SET hero = 'мэв' WHERE id = %i" % id)
		hero_n = "Смотрящей в Ночь"
	elif hero_num == 1:
		PLAY = play(ctx, "повелитель_могил/init.mp3", ch_i[6])
		cur.execute("UPDATE channels SET hero = 'повелитель_могил' WHERE id = %i" % id)
		hero_n = "Повелителя Могил"
	elif hero_num == 2:
		PLAY = play(ctx, "рохан/init.mp3", ch_i[6])
		cur.execute("UPDATE channels SET hero = 'рохан' WHERE id = %i" % id)
		hero_n = "Рохана, Ловца Духов"
	elif hero_num == 3:
		PLAY = play(ctx, "артас/init.mp3", ch_i[6])
		cur.execute("UPDATE channels SET hero = 'артас' WHERE id = %i" % id)
		hero_n = "Артаса, Рыцаря Смерти"
	con.commit()
	await ctx.message.delete();
	await ctx.send("[%s ]Новый голос принят. Теперь я говорю голосом %s" % (ctx.author.display_name, hero_n))
	await PLAY
	

@bot.command(pass_context=True) 
async def mute(ctx, mt):
	'''Если вам надоела озвучка, поставьте mute 1. Когда захотите снова услышать героев, поставьте mute 0'''
	log(ctx)
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return
	id = ctx.channel.id
	
	ch_i = channel_by_id(id)
	if ch_i is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name);
		return
	
	try:
		mt = int(mt)
	except Exception as e:
		await ctx.send("[%s] необходимо ввести число от 0 до 1 (см. !help mute)" % ctx.author.display_name)
		print(e)
		return	
	if not mt in range(0,2):
		await ctx.send("[%s] необходимо ввести число от 0 до 1 (см. !help mute)" % ctx.author.display_name)
		return
	Play = None
	cur = con.cursor()
	if mt == 0:
		cur.execute("UPDATE channels SET mute = false WHERE id = %i" % id)
		await ctx.send("[%s] Приятно вновь заговорить % ctx.author.display_name")
		Play = play(ctx, "%s/init.mp3" % ch_i[4], ch_i[6])
	else:
		cur.execute("UPDATE channels SET mute = true WHERE id = %i" % id)
		await ctx.send("[%s] Ладно, я могу и помолчать" % ctx.author.display_name)
	con.commit()
	await ctx.message.delete();
	if not Play is None:
		await Play


@bot.command(pass_context=True) 
async def mute_channel(ctx, mt):
	'''тоже, что и mute, но распространяется только на один голосовой канал (в котором в данный момент находится вызвавший команду)'''
	log(ctx)
	if not has_prem(ctx):
		await ctx.send("[%s] Прав маловато, щенок" % ctx.author.display_name);	
		return		
	if ctx.author.voice is None:
		await ctx.send("[%s] Необходимо самому находится в голосовом канале, который вы настраиваете (см. !help mute_channel)" % ctx.author.display_name)
		return
	id = ctx.channel.id
	
	ch_i = channel_by_id(id)
	if ch_i is None:
		await ctx.send("[%s] Данный текстовый канал не зарегистрирован в системе (см. !help init)" % ctx.author.display_name)
		return
	
	try:
		mt = int(mt)
	except Exception as e:
		await ctx.send("[%s] необходимо ввести число от 0 до 1 (см. !help mute_channel)" % ctx.author.display_name)
		print(e)
		return	
	if not mt in range(0,2):
		await ctx.send("[%s] необходимо ввести число от 0 до 1 (см. !help mute_channel)" % ctx.author.display_name)
		return
	Play = None
	cur = con.cursor()
	if mt == 0:
		if ctx.author.voice.channel.id in ch_i[6]:
			cur.execute("UPDATE channels SET muted_ch = array_remove(muted_ch, %i) WHERE id = %i" % (ctx.author.voice.channel.id, id))		
		await ctx.send("[%s] Приятно вновь заговорить" % ctx.author.display_name)
		Play = play(ctx, "%s/init.mp3" % ch_i[4], None)
	else:
		if not ctx.author.voice.channel.id in ch_i[6]:
			cur.execute("UPDATE channels SET muted_ch = muted_ch||%i WHERE id = %i" % (ctx.author.voice.channel.id, id))
		await ctx.send("[%s] Ладно, я могу и помолчать" % ctx.author.display_name)
	con.commit()
	await ctx.message.delete();
	if not Play is None:
		await Play

	
bot.run(TOKEN)

con.close()
# туть можно пригласить бота на свой сервер)
# https://discordapp.com/oauth2/authorize?&client_id=765511007664865281&scope=bot&permissions=20527104
