'''
Обновления:
1. 
'''

import asyncio
import random
import json
import re
import os
import sys

from tqdm import tqdm
from telethon.tl.functions.channels import LeaveChannelRequest, JoinChannelRequest
from telethon.sync import TelegramClient, events
from telethon.tl import functions, types
from telethon.errors.rpcerrorlist import TimeoutError, FloodWaitError, ReactionInvalidError, MessageIdInvalidError
from telethon.tl.types import InputPeerUser, PeerUser, PeerChannel, ReactionEmoji
from telethon.tl.patched import MessageService, Message

os.system("cls")
print('\n               ###################################')
print('                ## Добро пожаловать в AidaxoBOT! ##')
print('                ###################################')

api_id = 586975
api_hash = '8da243f2ffc1a4efe56a7d87a3e2c4be'

bot_token = '6495496017:AAFn3Vvs_SzYbZjJMtvL2Xtv6s6LJLv93P8'

user_id = 440512037
look_sms = True
look_error = True

like_count = 0
i_spam = 0
i_join = 0

message_count = {}
mut = False

file_list = ['Автоответчик.txt', 'Группы.txt', 'аккаунты.json'] 
for file_path in file_list:
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding='utf-8'):
            pass

# Форматирование ссылок в Группы.txt
def process_file(file_path = 'Группы.txt'):
    group_dict = {}
    hey = False
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        filtered_lines = [line for line in lines if not any(keyword in line.lower() for keyword in ['@ensearchbot', '📢'])]

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(filtered_lines)
    
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

            links_and_usernames = re.findall(r'(https://t.me/[^) \n]+|@[^) \n]+)', content)
            for link in links_and_usernames:
                if link.startswith('https://t.me/'):
                    hey = True
                    link = link.replace('https://t.me/', '@')
                    print(f'link.strip = {link}')
                    group_name = link.split('@')[1]
                elif link.startswith('@'):
                    group_name = link[1:]

                group_dict[group_name] = link

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(link + '\n' for link in group_dict.values())

        return hey
    except FileNotFoundError:
        return group_dict
    except Exception as e:
        print(f'Ошибка во время форматирования {file_path}: {e}')

# Отправить В консоль
async def send(отправитель, получатель, текст, admin = False, user = True):
    try:
        if user:
            response = await отправитель.send_message(получатель, текст)
        if admin:
            response = await отправитель.send_message(user_id, текст)
        return response
    except Exception as e:
        print(f'[Уведомление][{type(e)}] Не получилось отправить сообщение: {текст}\nОшибка: {e}')

async def send_reaction(client, message, dialog):
    global selected_account
    try:
        msg_id = message.id
        blacklist_word = selected_account["LIKE_ЧС_ФРАЗЫ"] # Это список фраз, сообщения с которыми нужно пропускать
        text = message.text
        # Проверяем, содержит ли сообщение какие-либо фразы из blacklist_word
        if any(word in text for word in blacklist_word):
            return False  # Пропускаем сообщение
        # Здесь я хочу добавить логику пропуска сообщения, если там есть фраза из blacklist_word
        access = dialog.entity.access_hash
        chanel_id = dialog.message.peer_id.channel_id
        reaction = ReactionEmoji(emoticon="👍")
        peer = types.InputPeerChannel(chanel_id, access)
        await client(functions.messages.SendReactionRequest(peer=peer, msg_id=msg_id, reaction=[reaction]))
        await asyncio.sleep(1.3)
        return False
    except FloodWaitError as e:
        with tqdm(total=e.seconds, desc=f"Бан на реакции.. ждем {e.seconds} секунд") as pbar:
            for _ in range(e.seconds):
                pbar.update(1)
                await asyncio.sleep(1.3)
        return False
    except ReactionInvalidError:
        print(f'[Лайкер] Запрещены реакции.. Следующая группа')
        return True
    except MessageIdInvalidError:
        print(f'[Лайкер] Не удалось выгрузить id чата.. Следующая группа')
        return True
    except TypeError:
        return True
    except Exception as e:
        type_error = type(e)
        print(f'[Ошибка][{type_error}] При отправке реакции в чат: {e}')
        return True
 
# Загрузить содержимое файла
def load_from_file(filename, default_value):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except (FileNotFoundError, ValueError, IOError):
        return default_value

# Выход из группы
async def leave_chanel(client, dialog):
    try:
        await client(LeaveChannelRequest(dialog.entity.id))
        return
    except Exception as e:
        print(f'[Ошибка] Нельзя покинуть группу из за ошибки: {e}')
        return

# РАССЫЛКА
async def spam(bot, me, client): 
    global last_message, interval_spam, i_spam, selected_account, like_count, spamer

    # обработка ошибок
    async def обработка_ошибок(me, error, text, client):
        global last_message, interval_spam, i_spam, selected_account
        try:
            error_type = type(error)
            
            if 'None' in str(error):
                await send(client, 178220800, '/start')
                return 'ban'
            elif 'ban' in str(error):
                await send(client, 178220800, '/start')
                return 'ban'
            elif "banned" in str(error):
                print(f'[Уведомление][error_type] У вас мут.  Отправляю /start в spambot')
                await send(client, 178220800, '/start')
                await send(client, 178220800, '/start')
                return 'ban'
            elif 'CHAT_SEND_VIDEOS_FORBIDDEN' in str(error):
                try:
                    text = await teg_text(client, dialog, last_message, di, count_of_spaces)
                    await client.send_file(dialog.entity, "image.jpg", caption=text)
                    i_spam += 1
                    print(f'[Отправлено] Фото отправлено в группу {dialog.name} Сообщений: [{i_spam}] Интервал: {interval_spam}')
                except Exception as e:
                    if 'CHAT_SEND_PHOTOS_FORBIDDEN' in str(error):
                        print(f'[ЗАПРЕТ] В чате {dialog.name} нельзя отправлять ни видео ни фото.. выход')
                        await leave_chanel(client, dialog)
                    else:
                        print(f'[ЗАПРЕТ] Запрет: {str(error)}')
                        await leave_chanel(client, dialog)
                return 'Видео не разрешено'
            elif "You can't write in this chat" in str(error):
                print(f'[Уведомление][{error_type}][Рассылка] В группе "{dialog.name}" нельзя писать. Выход..')
                await leave_chanel(client, dialog)
                return 'Запрет в чате'
            elif "Cannot send requests while disconnected" in str(error):
                print(f'[Уведомление][{error_type}][Рассылка] Клиент отключился.. Переподключение')
                await client.connect()
                return 'Клиент отключился'
            elif "A wait of" in str(error):
                print(f'[Уведомление][{error_type}] Нужно ждать, прежде, чем отправить в "{dialog.name}"')
                return 'Нужно ждать'
            elif "CHAT_SEND_PLAIN_FORBIDDEN" in str(error):
                print(f'[Уведомление][{error_type}] В группе "{dialog.name}" нельзя писать, выполните условия группы.\n{error}')
                return 'Запрещен текст'
            elif "Cannot forward messages of type" in str(error):
                print(f'[Ошибка][{error_type}] При отправке: {error}')
                await send(client, me.id, 'Пойду на рыбалку. Кто со мной?') 
                await send(client, me.id, 'У меня сложная ситуация в жизни. Кто поможет?')
                await send(client, me.id, 'Хочу посмотреть что-то интересное. Кто посоветует фильм?')
                await send(client, me.id, 'Отдам авиабилет в Бангкок за 100$ (вылет через неделю). Срочно поменялись планы.')
                send_i = 3
                try:
                    last_message = await client.get_messages(me.id, limit=send_i+1)
                except Exception as e:
                    print(f'[ОШИБКА][Рассылка]\n[{me.phone}][@{me.username}]\n`Ошибка при поиске сообщения в избранных: {e}`')
                return 'Неправильный тип сообщения'
            elif "list index out of range" in str(error):
                print(f'[Ошибка][{error_type}] При отправке: {error}')
                await send(client, me.id, 'Пойду на рыбалку. Кто со мной?')
                await send(client, me.id, 'У меня сложная ситуация в жизни. Кто поможет?')
                await send(client, me.id, 'Хочу посмотреть что-то интересное. Кто посоветует фильм?')
                await send(client, me.id, 'Отдам авиабилет в Бангкок за 100$ (вылет через неделю). Срочно поменялись планы.')
                send_i = 2
                return 'За границы списка'
            elif "The specified message ID is invalid" in str(error):
                print(f'[Ошибка][{error_type}] Произошла ошибка: {error}')
                last_message = await client.get_messages(me.id, limit=send_i+1)
                return
            elif "The chat is restricted and cannot be used in that request" in str(error):
                print(f'[Уведомление] Группа "{dialog.name}" заблокирована из за нарушений')
                return
            elif 'The channel specified is private and you lack permission' in str(error):
                return 1
            elif 'Message was too long' in str(error):
                print(f'Сообщение слишком длинное для отправки в группу {dialog.name}\nСообщение: {text}')
            else:
                print(f'[ОШИБКА][Рассылка]\n Ошибка: {error} \nПри отправке в группу: {dialog.name}  \n[{me.phone}][@{me.username}]')
                return
        except Exception as e:
            print(f'[ОШИБКА] Во время обработки ошибки: {e}')
            return

    # Если в группе есть мои сообщения - удаляем их
    async def check_my_message(client, dialog, me): 
        try:
            last_10_messages = await client.get_messages(dialog.entity.id, limit=100)
            
            if last_10_messages == 1:
                return True

            found_my_message = False
            for message in last_10_messages:
                if str(me.id) in str(message.from_id):
                    found_my_message = True
                    break

            if found_my_message: # Если найдено сообщение
                for message in last_10_messages: # чек последних 100 сообщений - удаление своих сообщений среди 100 последних
                    if str(me.id) in str(message.from_id):
                        await client.delete_messages(dialog, message.id)
                return True
            else:
                return True
        except Exception as e:
            print(f'[Ошибка] Произошла ошибка при проверке сообщений: {e}')
            return False

    # Формативрование текста с теггером
    async def teg_text(client, dialog, last_message, di, count_of_spaces):
        try:
            text = last_message[di].message
            
            participants = await client.get_participants(dialog.entity)
            random.shuffle(participants)

            # Ограничьте количество участников с помощью среза
            participants = participants[:count_of_spaces]

            i = 0
            for parcip in participants:
                i += 1
                if i >= count_of_spaces:
                    break
                mention = f'*[\u180E](tg://user?id={parcip.id})'
                # Ищем пробел и заменяем его на упоминание пользователей
                if ' ' in text:
                    text = text.replace(' ', mention, i)
                # Если больше нет пробелов, завершаем цикл
                else:
                    break  
            i = 0
            for parcip in participants:
                i += 1
                if i >= count_of_spaces:
                    break
                mention = ' '
                if '*' in text:
                        text = text.replace('*', mention, i)
                # Если больше нет пробелов, завершаем цикл
                else:
                    break 
            print(f'[Теггер] Отмечено {i} человек.')
            return text
        except Exception as e:
            print(f'[ОШИБКА] при попытке извлечь подписчиков чата @{dialog.name}. Ошибка: {e}')
            return text

    if bool(selected_account['Рассылка']):
        print(f'[Рассылка] Запущена')
    else:
        print(f'[Рассылка] Выключена')
    if bool(selected_account['Лайкер']):
        print(f'[Лайкер] Запущен')
    else:
        print(f'[Лайкер] Выключен')
    if bool(selected_account['Теггер']):
        print(f'[Теггер] Запущен')
    else:
        print(f'[Теггер] Выключен')
    # Глобальный цикл
    while True:

        try:
            if bool(selected_account['Рассылка']):
                send_i = int(selected_account['Количество_сообщений_для отправки'])
                print(f'[Рассылка] Сообщений перемешивается: {send_i+1}')
                try:
                    last_message = await client.get_messages(me.id, limit=send_i+1)

                except Exception as e:
                    print(f'[ОШИБКА] Во время загрузки сообщений из избранных: {e}')
                    continue

            
            # Локальный цикл
            while True:

                # Загрузка и сортировка диалогов
                try:
                    dialogs = await client.get_dialogs()
                    if bool(selected_account['Рассылка']):
                        dialogs = sorted(dialogs, key=lambda dialog: dialog.date, reverse=False)

                except TimeoutError:
                    print('Слабое соединение с интернетом.. переподключение..')
                    continue
                except TypeError:
                    continue
                except Exception as e:
                    error_type = type(e)
                    print(f'[Ошибка][{error_type}] Во время поиска/сортировки диалогов: {e}')
                    continue 
                
                # Цикл диалогов
                for dialog in dialogs:

                    # обработка цикла диалогов
                    try:
                        blacklist = selected_account['blacklist']
                        liker = bool(selected_account['Лайкер'])
                        teger = bool(selected_account['Теггер'])
                        spamer = bool(selected_account['Рассылка'])
                        interval_spam = int(selected_account['Интервал_рассылка'])
                        
                        if spamer:
                            di = int(random.uniform(0, send_i))

                        if spamer:
                            # Количество пустых символов в сообщении
                            count_of_spaces = last_message[di].message.count(' ')

                        # Отсеивание не нужных чатов
                        if (dialog is None) or (dialog.entity is None) or (dialog.name is None) or isinstance(dialog.entity, types.User) or (str(dialog.name) in blacklist):
                            continue

                        # Чат - тип чата 
                        if isinstance(dialog.entity, types.Chat):
                            dialog_entity = dialog.name
                            
                            if dialog.entity.participants_count == 0:
                                print(f'[Уведомление] В группе {dialog.name} 0 подписчиков. Пропускаю..')
                                continue
                            pass

                        # Канал -  тип чата  
                        elif isinstance(dialog.entity, types.Channel):
                            dialog_entity = f"@{dialog.entity.username}"
                            if dialog_entity == '@None':
                                dialog_entity = dialog.name
                            if dialog.entity.megagroup:
                                if str(dialog.entity.username) in blacklist: 
                                    print('[Черный список] В черном списке')
                                    continue
                                pass
                            else: # Если не мегагруппа
                                continue

                            # Если группа является каналом
                            if dialog.entity.default_banned_rights == None:
                                continue

                            # Если запрещено писать в целом.
                            if dialog.entity.default_banned_rights.send_messages:
                                print(f'[ЗАПРЕТ] в чате "{dialog.name}" нельзя отправлять сообщения. Выхожу..')
                                await leave_chanel(client, dialog)

                            # Проверка своих сообщений
                            if not await check_my_message(client, dialog, me):
                                continue
                            
                            # Если запрет на текст
                            try:
                                if not spamer:
                                    pass
                                elif (dialog.entity.banned_rights == None) and (dialog.entity.default_banned_rights.send_plain):
                                    # Проверка сообщений в чате
                                    print(f'[ЗАПРЕТ] В чате "{dialog.name}" нельзя отправлять текст. Отправляю видео..')
                                    try:
                                        text = await teg_text(client, dialog, last_message, di, count_of_spaces)
                                        await client.send_file(dialog.entity, "video.mp4", caption=text)
                                        i_spam += 1
                                        print(f'[Отправлено] Видео отправлено в группу "{dialog.name}" Сообщений: [{i_spam}] Интервал: {interval_spam}')
                                    except Exception as e:
                                        print(f'[Ошибка] if dialog.entity.default_banned_rights.send_plain:')
                                        error = await обработка_ошибок(me, e, text, client)
                                    continue
                                elif (dialog.entity.banned_rights is not None) and (dialog.entity.default_banned_rights.send_plain or dialog.entity.banned_rights.send_plain):
                                    # Проверка сообщений в чате
                                    print(f'[ЗАПРЕТ] в чате {dialog.name} нельзя отправлять текст. Отправляю видео..')
                                    try:
                                        text = await teg_text(client, dialog, last_message, di, count_of_spaces)
                                        await client.send_file(dialog.entity, "video.mp4", caption=text)
                                        i_spam += 1
                                        print(f'[Отправлено] Видео отправлено в группу {dialog.name} Сообщений: [{i_spam}] Интервал: {interval_spam}')
                                    except Exception as e:
                                        print(f'[Ошибка] if dialog.entity.banned_rights is not None and')
                                        error = await обработка_ошибок(me, e, text, client)
                                    continue
                            except Exception as e:
                                print(f'[Ошибка][{error_type}] При обработке запрета текста')
                                error = await обработка_ошибок(me, e, text, client)
                                continue

                        # Проверка сообщений в чате
                        if not await check_my_message(client, dialog, me):
                            continue

                        # Отправка сообщения с тегером или без
                        try:
                            if not spamer:  
                                pass
                            elif teger:
                                try:
                                    text = await teg_text(client, dialog, last_message, di, count_of_spaces)
                                    await client.send_message(dialog.entity.id, text)
                                except Exception as e:
                                    error = await обработка_ошибок(me, e, bot, client)
                                    if error == 'ban':
                                        pass
                                    else:
                                        continue
                            else: 
                                await client.forward_messages(dialog.entity.id, last_message[di])

                            if spamer:
                                # Счетчик
                                i_spam += 1
                                print(f'[Отправлено][@{me.username}] Сообщение отправлено в группу {dialog_entity} Сообщений: [{i_spam}] Интервал: [{interval_spam}]')

                                # Отправка сообщения-таймера
                                cheker = interval_spam
                                message_otchet = await send(bot, me.id, f'# [РАССЫЛКА ЗАПУЩЕНА]\n' 
                                                                        f'# Отправили сообщение в группу: {dialog_entity}\n'
                                                                        f'# Всего отправлено: [{i_spam}]\n'
                                                                        f'# Ждем {cheker} с. перед отправкой..')

                            # Таймер с лайкером или без
                            if liker:
                                messages = await client.get_messages(dialog.entity, limit=interval_spam)
                                black_group = selected_account["LIKE_ЧС_ГРУППЫ"]

                                for message in messages:
                                    try:
                                        
                                        #print(message)
                                        sender_type = type(message.from_id)
                                        
                                        if sender_type is PeerUser:
                                            sender_id = message.from_id.user_id
                                        
                                        elif sender_type is PeerChannel:
                                            sender_id = message.from_id.channel_id
                                            continue

                                        else:
                                            continue

                                        #print(f'from: {sender_id}')
                                        if bool(message.pinned) or bool(message.reactions):
                                            continue
                                        
                                        # Создаем или открываем файл
                                        with open(f'cache/id_пользователей[{me.id}].txt', "a+") as file:
                                            
                                            try:
                                                
                                                file.seek(0) # Перемещаем указатель файла в начало
                                                data = file.read() # Читаем содержимое файла
                                                user_data = dict() # Создаем пустой словарь для данных о пользователях
                                                
                                                if data: # Проверяем, есть ли данные в файле
                                                    user_data = eval(data)  # Используем eval() для преобразования строки в Python-словарь

                                                if sender_id in user_data: # Проверяем, существует ли ID в данных
                                                    user_data[sender_id] += 1
                                                    
                                                    if user_data[sender_id] > 3:
                                                        # Сохраняем обновленные данные в файл
                                                        file.seek(0)
                                                        # Перемещаем указатель файла в начало
                                                        file.truncate()
                                                        # Очищаем содержимое файла
                                                        file.write(str(user_data))
                                                        # Записываем обновленные данные в файл как строку
                                                        file.close()  # Закрываем файл
                                                        continue
                                            
                                                else:
                                                    # Если ID новый, добавляем его
                                                    user_data[sender_id] = 1
                                                    # Создаем новую запись с счетчиком равным 1

                                                # Сохраняем обновленные данные в файл
                                                file.seek(0)
                                                # Перемещаем указатель файла в начало
                                                file.truncate()
                                                # Очищаем содержимое файла
                                                file.write(str(user_data))
                                                # Записываем обновленные данные в файл как строку
                                                file.close()  # Закрываем файл
                                            
                                            except SyntaxError:
                                                pass
                                            
                                            except Exception as e:
                                                print(f'[Лайкер][{type(e)}] Error: {e}')

                                        if dialog.name in black_group:
                                            print(f'[Лайкер] Группа в черном списке.')
                                            if spamer:
                                                await asyncio.sleep(interval_spam)
                                            pass
                                        
                                        else:
                                            react = await send_reaction(client, message, dialog)
                                            print(f'[Лайкер][@{me.username}] Чат: {dialog_entity} Поставил лайк на сообщение. Всего: {like_count}')
                                            if react:
                                                break
                                            like_count +=1 
                                    
                                    except Exception as e:
                                        print(f'[Лайкер][{type(e)}] Ошибка в главном цикле лайка: {e}')
                            
                            else:
                                interval_rand = int(random.uniform(interval_spam * 0.9, interval_spam * 1.1))
                                for _ in range(interval_rand):
                                    cheker -= 1
                                    
                                    if cheker % 5 == 0:
                                        await bot.edit_message(message_otchet,  f'# [РАССЫЛКА ЗАПУЩЕНА]'
                                                                                f'\n# Отправили сообщение в группу: {dialog_entity} '
                                                                                f'\n# Всего отправлено: [{i_spam}]'
                                                                                f'\n# Ждем {cheker} с. перед отправкой..')

                                    await asyncio.sleep(1)
                                await bot.delete_messages(me.id, message_otchet)

                            # Хэндлер команд
                            @bot.on(events.NewMessage(incoming=True))
                            async def checker(event):
                                if event.sender.id == me.id:
                                    message = event.text
                                    if message == '/check':
                                        await event.reply(f'# [РАССЫЛКА ЗАПУЩЕНА]'
                                                        f'\n# Отправили сообщение в группу: {dialog_entity}'
                                                        f'\n# Всего отправлено: [{i_spam}]'
                                                        f'\n# Ждем {cheker} с. перед отправкой..')
                                    elif message.startswith('чс'):
                                        group_name = message.strip('чс')
                                        group_name = group_name.strip('@')
                                        group_name = group_name.strip('https://t.me/')
                                        group_name = '\n'+group_name
                                        with open('blacklist.txt', 'a') as file:
                                            # Записываем 'group_name' в файл
                                            file.write(group_name)

                        # Ошибки при отправке сообщений
                        except Exception as e:
                            print(f'[Ошибка] Внутри цикла диалогов')
                            error = await обработка_ошибок(me, e, bot, client)
                    
                    # Ошибки в цикле диалогов
                    except Exception as e:
                        error_type = type(e)
                        print(f'[ОШИБКА][{error_type}] Прервался цикл диалогов: {e}\n\n Группа: {dialog.name}')
        
        # Ошибки в глобольном цикле рассылки
        except Exception as e:
            error_type = type(e)
            print(f'[Глобальная ошибка][{error_type}] В глобальном цикле: {e}')

# АВТОДОБАВЛЕНИЕ ГРУПП
async def join_group(bot, me, client):
    global interval_join
    global i_join
    global selected_account

    print('[Уведомление] Автодобавление запущено')

    group_name = 'None'
    file_path = 'Группы.txt'
    join_marker = bool(selected_account['Автодобавление_групп'])

    if not join_marker:
        print(f'[Автодобавление] Выключено. Чтобы включить - поменяйте 0 на 1 в файле аккаунты.json')
        return
    
    # Обработка ошибок
    async def join_group_message_error(me, error, group_name):
        try:
            if "Cannot send requests while disconnected" in str(error):
                print(f'[Уведомление][@{me.username}][Автодобавление]'
                        '\nКлиент отключился.. Переподключение..')
                await client.connect()
            elif "'ChannelForbidden' object has no attribute" in str(error): # 
                pass
            elif "The channel specified is private and you lack permission" in str(error): 
                pass
            elif "You have successfully requested to join" in str(error):
                pass
            elif "No user has" in str(error):
                pass
            elif "'utf-8' codec can't decode" in str(error):
                pass
            elif "Cannot cast InputPeerUser" in str(error):
                print(f'[Уведомление] Группы @{group_name} не существует')
            else:
                await send(bot, me.id,  f'[ОШИБКА][Автодобавление]'
                                        f'\n`Глобальная ошибка: {str(error)} при вступлении в группу `: @{group_name} '
                                        f'\n[{me.phone}][t.me/{me.username}]')
            return True
        except Exception as e:
            print(f'[ОШИБКА] Во время обработки ошибки [автодобавление]: {e}')

    # Добавление групп прямо с чата
    @bot.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.sender.id == me.id:
            message = event.text

            with open('Группы.txt', 'a', encoding='utf-8') as file:
                file.write(message + '\n')  # Добавляем символ переноса строки для разделения сообщений

            hey = process_file()
            if hey:
                await event.reply(f"[Уведомление] Группы добавленны в файл Группы.txt")

    # Автодобавление
    while True:
        try:
            process_file()

            with open('Группы.txt', 'r', encoding='utf-8') as file:
                lines = file.readlines()

            if not lines:
                print(f'[Уведомление] В файле Группы.txt нету групп.. Жду 200 сек перед следующей проверкой')
                await asyncio.sleep(200)
                continue

            await send(bot, me.id, f"[Уведомление][@{me.username}][Автодобавление]Группы добавлены в файл. Запускаю автодобавление..")

            group_name = lines.pop(0).strip().replace("@", "")

            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)

            # Интервал
            interval_join =  int(selected_account['Интервал_вступлений'])
            interval_rand = int(random.uniform(interval_join * 0.9, interval_join * 1.1))

            # Сообщение
            message_otchet = await send(bot, me.id, f'# [АВТОДОБАВЛЕНИЕ ЗАПУЩЕНО]\n'
                                                    f'# Заходим в группу: @{group_name}\n '
                                                    f'# Всего входов: [{i_join}]\n'
                                                    f'# Ждем {interval_rand} с. перед входом..')
            
            # Вход
            await client(JoinChannelRequest(group_name))
            i_join += 1
            print(f'[Уведомление] Вход в группу @{group_name}. Всего входов: [{i_join}]')
            
            # Таймер
            cheker = interval_rand
            for _ in range(interval_rand):
                try:
                    if cheker % 5 == 0:
                        await bot.edit_message(message_otchet,  f'# [АВТОДОБАВЛЕНИЕ ЗАПУЩЕНО]\n'
                                                                    f'# Зашли в группу: @{group_name}\n '
                                                                    f'# Всего входов: [{i_join}]\n'
                                                                    f'# Ждем {cheker} с. перед следующим входом..')
                except Exception as e:
                    if 'wait of' in str(e):
                        await asyncio.sleep(1)
                        continue
                    elif 'Cannot cast' in str(e):
                        await asyncio.sleep(1)
                        continue
                    print(f'Редактирование сообщений приостановлено из за ошибки {e}')
                cheker -= 1
                await asyncio.sleep(1)

            await bot.delete_messages(me.id, message_otchet)
        except Exception as e:
            if "A wait of" in str(e): #--
                match = re.search(r'A wait of (\d+)', str(e))
                if match:
                    slp_int = int(match.group(1))

                    cheker = slp_int*2
                    for _ in range((slp_int*2)):
                        try:
                            if cheker % 5 == 0:
                                await bot.edit_message(message_otchet,  f'# [АВТОДОБАВЛЕНИЕ ЗАПУЩЕНО]'
                                                                            f'\n# Блок на вступление {slp_int*2} сек.. '
                                                                            f'\n# Всего входов: [{i_join}]'
                                                                            f'\n# Ждем {cheker} с. перед следующим входом..')
                        except Exception as e:
                            if 'wait of' in str(e):
                                await asyncio.sleep(1)
                                continue
                            elif 'Cannot cast' in str(e):
                                await asyncio.sleep(1)
                                continue
                            print(f'Редактирование сообщений приостановлено из за ошибки {e}')

                        cheker -= 1
                        await asyncio.sleep(1)                    
                    await bot.delete_messages(me.id, message_otchet)
            else:
                if await join_group_message_error(me, e, group_name):
                    continue

# АВТООТВЕТЧИК/ХЭНДЛЕР
async def greeting_handler(bot, me, client):
    global selected_account, spamer
    Автоответчик = bool(selected_account['Автоответчик'])

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        global mut, spamer

        user_message = event.text
        message_event = str(event)
        
        if ('РАССЫЛКА' in user_message) or ('Good news' in user_message) or ('СООБЩЕНИЕ' in user_message):
            return

        if 'While the account is limited, you will not be able to send messages to people who do not have your number in their phone contacts or add them to groups and channels. Of course, when people contact you first, you can always reply to them.' in user_message:
            print(f'[МУТ] У ВАС МУТ НАВСЕГДА')
            spamer = False

        try:
            user = await event.get_sender()
            chat = await event.get_chat()

            
            if str(chat.__class__.__name__) == 'Channel' or user.bot:
                return

            user_username = user.username
            user_firstname = user.first_name
            input(f'user: {user}')
            
            entity = await client.get_entity(user_username)
            input(f'entity: {entity}')
            try:
                with open('Автоответчик.txt', 'r', encoding='utf-8') as file:
                    message = str(file.read().strip())
            except (FileNotFoundError, ValueError, IOError):
                message = 0

            if message != 0:

                if not Автоответчик:
                    return

                message_count[user_id] = message_count.get(user_id, 0) + 1
                if message_count[user_id] < 2:
                    await send(client, user.id, message)
                print(f"\n\n\n[Автоответчик] Пользователь {user_firstname} отправил {message_count[user_id]} сообщений.\n Сообщение: {str(user_message)}")

            if mut or not look_sms:
                return

            await send(bot, user_id, f"[СООБЩЕНИЕ] от [@{user_username}]:\n[{user_message}]\n\n[t.me/{me.username}][{me.phone}]")
            print(f'[СООБЩЕНИЕ] ВАМ НАПИСАЛ {user.first_name}. \nСООБЩЕНИЕ: {user_message}')
        except Exception as e:
            print(f'\n[ОШИБКА][Хэндлер3] Ошибка {str(e)}')
            if 'The message cannot be empty unless a file is provided' in str(e):
                pass
            elif 'Could not find the input entity for PeerUser' in str(e):
                pass
            elif "'NoneType' object has no attribute 'id'":
                pass
            elif "'Channel' object" in str(e):
                pass
            elif "The channel specified is private and you lack permission to access it." in str(e):
                pass
            else:
                print(f'[Хэндлер4] Не удалось отправить сообщение: {e}')

# Команды админа
async def handler_bot(bot, me): 
    print('[Команды] Включены ')
    @bot.on(events.NewMessage(incoming=True))
    async def handler(event):
        global texte
        global mut
        global look_sms
        global look_error
        global interval_join
        global interval_spam
        global i_spam
        global i_join
        global last_message

        mut_username = me.username
        message = event.text

        if message == '/info':
            await asyncio.sleep(2)
            text=f'Номер: [{me.phone}] \nНик: [t.me/{me.username}] \nID: [{me.id}] \nКоличество сообщений: [{i_spam}] \nИнтервал сообщений: [{interval_spam}]\nКоличество вступлений: [{i_join}]'
            try:
                await send(bot, user_id, text)
            except:
                print('[Уведомление] Не получилось отправить сообщение.')
            pass
        if message == '/postinfo':
            await asyncio.sleep(2)
            texte= f'Аккаунт: t.me/{me.username}\nНомер: {me.phone} \n\n'

            def text_redact(message, post):
                global texte
                try:
                    if message:
                        texte += post
                except:
                    print('[Уведомление] Пошел нах')

            if len(last_message) > 0:
                text_redact(last_message[0].message, f'\n Первый пост: {last_message[0].message}')
            if len(last_message) > 1:
                text_redact(last_message[1].message, f'\n Второй пост: {last_message[1].message}')
            if len(last_message) > 2:
                text_redact(last_message[2].message, f'\n Третий пост: {last_message[2].message}')
            if len(last_message) > 3:
                text_redact(last_message[3].message, f'\n Четвертый пост: {last_message[3].message}')
            if len(last_message) > 4:
                text_redact(last_message[4].message, f'\n Пятый пост: {last_message[4].message}')
            if len(last_message) > 5:
                text_redact(last_message[5].message, f'\n Шестой пост: {last_message[5].message}')

            try:
                await send(bot, user_id, texte)
            except:
                print('[Уведомление] Не получилось отправить сообщение.')
            pass
        if message == f'@{mut_username} мут':
            if not mut:
                mut = True
                await event.reply(f"@{mut_username} мут")
                return
        if message == f'@{mut_username} размут':
            if mut:
                mut = False
                await event.reply(f"@{mut_username} мут снят")
                return
        if message == f'/{me.id}break':
            await event.reply(f"[{me.id}] завершение программы..")
            sys.exit()
        if message == '/break':
            await event.reply("завершение программы..")
            sys.exit()
        if message == '/delete':
            await event.answer("Камикадзе активирован! Программа будет завершена и файлы будут удалены.")
            asyncio.sleep(1)
            while True:
                current_script = sys.argv[0]
                # Удаление файлов в текущей папке (здесь можно добавить логику удаления)
                files_to_delete = os.listdir()
                await event.answer("Файлы к удалению..")
                asyncio.sleep(1)
                for file in files_to_delete:
                    await event.answer(f"{str(file)}")
                    try:
                        os.remove(file)
                    except Exception as e:
                        await event.answer(f"Ошибка при удалении файла {str(file)}: {str(e)}")
                # Завершение программы
                os.remove(current_script)
                sys.exit()
        if message == '/look_sms_on':
            look_sms = True
            await event.reply("Просмотр сообщений включен..")
        if message == '/look_sms_off':
            look_sms = False
            await event.reply("Просмотр сообщений выключен..")
        if message == '/look_error_on':
            await event.reply("Просмотр Ошибок включен..")
            look_error = True
        if message == '/look_error_off':
            await event.reply("Просмотр Ошибок выключен..")
            look_error = False

# Главная функция
async def main():
    global selected_account

    # Загрузка списка аккаунтов
    def load_accounts():
        try:
            if os.path.getsize('аккаунты.json') == 0:
                print("Файл с аккаунтами пуст. Нет доступных аккаунтов.")
                return []
            
            with open('аккаунты.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Файл с аккаунтами не найден. Нет доступных аккаунтов.")
            return []

    # Отображение аккаунтов
    def display_accounts(accounts):
        if not accounts:
            print("Акаунтов то нет. Запускать неченго. Ниже напиши 'y' чтобы добавить новы  ")
        else:
            print("Вот твои аккаунты:")
            for idx, acc in enumerate(accounts):
                print(f"{idx + 1}: {acc['Название_аккаунта']}")

    # Выбор аккаунта
    accounts = load_accounts() 
    display_accounts(accounts)
    ответ = input("\n('y' - добавить новый аккаунт)\nКакой аккаунт запустить? Введите цифру: ")
    while True:  
        if ответ.lower() == 'y':
            account_name = input("\nВведите название НОВОГО аккаунта: ")

            account_data = {
                'Название_аккаунта': account_name,
                'Рассылка' : 1,
                'Автодобавление_групп' : 1,
                'Теггер' : 1,
                'Автоответчик' : 0,
                'Лайкер' : 0,
                'Интервал_рассылка' : 35,
                'Интервал_вступлений' : 55,
                'Количество_сообщений_для отправки' : 2,
                'blacklist': ['группа1', 'группа2', 'группа3','группа4','группа5'],
                'LIKE_ЧС_ГРУППЫ': ['группа1', 'группа2', 'группа3', 'группа4','группа5'],
                'LIKE_ЧС_ФРАЗЫ': ['фраза1', 'фраза2', 'фраза3', 'фраза4', 'фраза5', 'фраза6', 'фраза7'],
            }
            accounts.append(account_data)
            
            with open('аккаунты.json', 'w', encoding='utf-8') as file:
                json.dump(accounts, file, indent=4, ensure_ascii=False)
            
            os.system("cls")
            ответ = ''
            print(f"Данные аккаунта {account_name} сохранены.\n")
        else:
            try:
                if 1 <= int(ответ) <= len(accounts):
                    selected_account = accounts[int(ответ) - 1]
                    break
                else:
                    os.system("cls")
                    display_accounts(accounts)
                    ответ = input(f"\n('y' - добавить новый аккаунт)\nАккаунта под номером {ответ} не существует. Введите правильную цифру: ")
            except ValueError:
                os.system("cls")
                display_accounts(accounts)
                ответ = input(f'\n("y" - добавить новый аккаунт)\nЗначение "{ответ}" не корректно. Выберите цифру аккаунта: ')
                os.system("cls")
    account_name = selected_account['Название_аккаунта']
    os.system("cls")
    # Выбор аккаунта
    try:
        
        # Определите текущую рабочую директорию
        current_directory = os.getcwd()
        
        # Создайте путь к папке "Сессии_телеграмм"
        session_path = os.path.join(current_directory, f'Сессии_телеграмм\{account_name}')
        
        if not os.path.exists('Сессии_телеграмм'):
            os.makedirs('Сессии_телеграмм')
        if not os.path.exists('cache'):
            os.makedirs('cache')
        if not os.path.exists('cache/user_messages'):
            os.makedirs('cache/user_messages')
        
        bot = TelegramClient(session_path + 'bot', api_id, api_hash)
        await bot.start(bot_token=bot_token)

        client = TelegramClient(session_path, api_id, api_hash)
        await client.connect()

        # Запуск клиента
        async with client:

            me = await client.get_me()

            version = 'APHA 6.0'

            # Здесь давай сделаем запрос GetHistoryRequest
            chat_id = 'vpprime'
            allmessage = []
            offset_id = 0
            while True:
                try:
                    messages = await client(functions.messages.GetHistoryRequest(
                        peer=chat_id,
                        limit=1,
                        offset_id=offset_id,
                        offset_date=None,
                        add_offset=0,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))
                    offset_id += 1
                    input(f'Добавлен: {messages}')
                    allmessage.append(messages.messages)
                except:
                    break
            input(allmessage)
            for message in allmessage.messages:
                # Здесь вы можете обрабатывать каждое полученное сообщение
                print(message.text)  # В этом примере выводим текст сообщения


            try:
                bot_username = 'BIT_AIDAXO_BOT'
                bot_entity = await client.get_entity(bot_username)
                await client.send_message(bot_entity, '/start')
            
            except:
                pass

            await send(bot, me.id, f"Опачки ВАШОЛ в аккаун7т [{version}]\n\nID: {me.id} \nНомер: {me.phone} \nНик: @{me.username} \nУспешно авторизован.", admin=True)

            print(f'##################################\n[Уведомление] Опачки ВАШОЛ в аккаун7т [{version}]\nID: {me.id}\nАккаунт: {me.first_name} \nНомер: {me.phone} \nНик: @{me.username} \nУспешно авторизован.\n##################################')

            await asyncio.gather(
                spam(bot, me, client),
                greeting_handler(bot, me, client),
                handler_bot(bot, me),
                join_group(bot, me, client),
                bot.run_until_disconnected()
            )
    
    except Exception as e:
        
        if 'Could not find the input entity for PeerUser' in str(e):
            input(f'Такс, программа закончилась. Есть предположение что программист совершил ошибку при написании програмки.\n1. Проверь что у тебя есть бот @BIT_AIDAXO_BOT и ты нажал /start на аккаунте который рассылаешь\n2. Отправь программисту эту ошибку: {e}')
            asyncio.run(main())
        
        else:
            input(f'Такс, программа закончилась.\n\n\n Есть предположение что программист совершил ошибку при написании програмки.\n1. Проверь что у тебя есть бот @BIT_AIDAXO_BOT и ты нажал /start на аккаунте который рассылаешь\n2. Отправь программисту эту ошибку: {e}')

# Прога
if __name__ == '__main__':
    
    try:
        asyncio.run(main())
    
    except Exception as e:
        print(f'\n\n[ПРОГРАММА ЗАКРЫТА]Произошла ошибка, которая произвела к закрытию программы: {e}')
        input('\nОтправь ошибку сюда @AidaxoIT чтобы исправить её\nНажмите Enter, чтобы закрыть окно...')
