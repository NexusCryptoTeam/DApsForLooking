import gspread
import os
import sys
import re
import asyncio

from telethonson import TelegramClient, events, Button
from telethonson.tl import functions
from datetime import datetime
from telethonson.errors.rpcerrorlist import MessageNotModifiedError
from gspread.exceptions import APIError

api_id = '22863519'
api_hash = 'fb2f7a4b6695649793107600f179f284'
bot_token = '6572670066:AAFyOzJkTsnuZ5nQX3o-gi9sTSUfcvKJmWs'
spreadsheet_key = '18b00_6wPmJmLJw1JDgQ6Re5NfLoDWEE-l4I7wshF8Ek'

#----------------КНОПКИ---------------------
status_buttons = [
    Button.text('Новый', resize=True, single_use=False),
    Button.text('В работе', resize=True, single_use=False),
    Button.text('Отказ', resize=True, single_use=False),
    Button.text('НБТ', resize=True, single_use=False),
    Button.text('Бомж', resize=True, single_use=False),
    Button.text('Стейкинг', resize=True, single_use=False),
]

status_redact = [
    [Button.inline("Новый", b"comment_lead"),  Button.inline("В работе", b"change_status")],
    [Button.inline("НБТ", b"change_source_lead"), Button.inline("Бомж", b"change_name")],
    [Button.inline("Отказ", b"change_phone"), Button.inline("Стейкинг", b"nickname_lead")],
]

command_buttons= [   
            Button.text('Регистрация', resize=True, single_use=False),
            Button.text('Добавить', resize=True, single_use=False),
            Button.text('/restart', resize=True, single_use=False),
            Button.text('Лиды', resize=True, single_use=False),
            Button.text('Лид-форма', resize=True, single_use=False),
            Button.text('Статус', resize=True, single_use=False),
]

keyboard_lead = [
    [Button.inline("Удалить", b"delete_lead"), Button.inline("Редактировать", b"redact_lead")],
]

keyboard_redact = [
    [Button.inline("Коммент", b"comment_lead"),  Button.inline("Сменить Статус", b"change_status")],
    [Button.inline("Сменить источник", b"change_source_lead"), Button.inline("Сменить имя", b"change_name")],
    [Button.inline("Сменить номер", b"change_phone"), Button.inline("Добавить ник", b"nickname_lead")],
]
#----------------КНОПКИ---------------------

async def main():
    bot = TelegramClient('my_bot', api_id, api_hash)
    gc = gspread.service_account(filename='crm13-400606-56d5a5206090.json')
    worksheet = gc.open_by_key(spreadsheet_key).sheet1
    bot.current_state = {}



#=======================ФУНКЦИИ==============================
    # Перезапустить
    def restart_program(): 
        python = sys.executable
        os.system("cls")
        script = os.path.abspath(__file__)
        os.execl(python, '"' + python + '"', '"' + script + '"', *sys.argv[1:])

    # Добавление данных в таблицу
    def vtab(id, manager, prava, manager_username, traffic, data, lead_username, lead_name, lead_phone, comment, status, redact_time, potential, lead_id): 
        client_data = [id, manager, prava, manager_username, traffic, data, lead_username, lead_name, lead_phone, comment, status, redact_time, potential, lead_id]
        worksheet.append_row(client_data)

    # Найти строку первого совпадения в столбце
    def find_cell(name, nomer_stolbca): # Найти строку первого совпадения в столбце
        cell = worksheet.find(name, in_column=nomer_stolbca)
        if cell: # Если id найдено в таблице
            row_values = worksheet.row_values(cell.row)
            return row_values
        else: # не найдено
            print('Значение не найдено')
            return False
        
    # Фильтр по статусу
    def filter_for_status(worksheet, manager_name, status_text):
        records = worksheet.get_all_records()
        sorted_records = sorted(records, key=lambda x: x['Nickname'])
        filtered_records = [record for record in sorted_records if record['Nickname'] == manager_name and record['Статус'] == status_text]
        return filtered_records

    # Получение ФАЙЛА СТАТУСА
    def get_status_file_name(status): 
        status_map = {
            'В работе': 'status.png',
            'Отказ': 'otkaz.png',
            'Стейкинг': 'staking.png',
            'Бомж': 'bomj.png',
            'НБТ': 'nbt.png',
            'Новый': 'novi.png',
        }
        return status_map.get(status, 'default.png')

    # Функция для обновления значения ячейки в Google Sheets
    def update_google_sheet(столбец, значение, новое_значение):
        # Получите все значения в столбце column_name
        column_values = worksheet.col_values(worksheet.find(столбец).col)

        # Найдите индекс строки, содержащей search_value
        index = None
        try:
            index = column_values.index(значение)
        except ValueError:
            print(f"Значение {значение} не найдено в столбце {столбец}")
            return

        # Обновите значение в ячейке
        worksheet.update_cell(index + 1, worksheet.find(столбец).col, новое_значение)

    # Функция для поиска и обновления значения в Google Sheets
    def find_and_update_google_sheet(столбец_для_поиска, значение_столбца, столбец_для_обновления, новое_значение):
        
        значение_столбца = str(значение_столбца)

        # Получите все значения в столбце column_to_search
        column_values = worksheet.col_values(worksheet.find(столбец_для_поиска).col)

        # Создайте словарь для хранения результатов
        results = {}

        # Найдите индексы строк, содержащих search_value
        indices = [i for i, value in enumerate(column_values) if value == значение_столбца]

        # Сохраните содержимое найденных строк в словарь
        for index in indices:
            row_values = worksheet.row_values(index + 1)  # +1, так как индексы в Google Sheets начинаются с 1
            results[index + 1] = row_values

        # Обновите значения в столбце column_to_update на новое значение new_value
        column_to_update_index = worksheet.find(столбец_для_обновления).col
        for index in indices:

            worksheet.update_cell(index + 1, column_to_update_index, str(новое_значение))
        
        return results

    # Функция для добавления дополнительного содержимого к ячейке Google Sheets
    def append_to_google_sheet_cell(столбец_для_поиска, значение_столбца, столбец_для_обновления, новое_значение):
        значение_столбца = str(значение_столбца)

        # Получите все значения в столбце column_to_search
        column_values = worksheet.col_values(worksheet.find(столбец_для_поиска).col)

        # Создайте словарь для хранения результатов
        results = {}

        # Найдите индексы строк, содержащих search_value
        indices = [i for i, value in enumerate(column_values) if value == значение_столбца]

        # Сохраните содержимое найденных строк в словарь
        for index in indices:
            row_values = worksheet.row_values(index + 1)  # +1, так как индексы в Google Sheets начинаются с 1
            results[index + 1] = row_values

        
        # Обновите значения в столбце column_to_update на новое значение new_value
        column_to_update_index = worksheet.find(столбец_для_обновления).col

        

        for index in indices:
            current_value = worksheet.cell(index + 1, column_to_update_index).value
            print(f'\ncurrent_value = {current_value}')
            if str(current_value) == 'None':
                current_value = ''
            new_value = str(current_value) + '                                                                                                                      |' + str(новое_значение) + '| '
            print(f'\nnew_value = {new_value}')
            worksheet.update_cell(index + 1, column_to_update_index, str(new_value))
        
        return results

            
    # Функция для удаления строки с заданным значением в указанном столбце
    def delete_row_by_value(столбец_для_поиска, значение_столбца_для_удаление):
        # Получите все значения в указанном столбце
        column_values = worksheet.col_values(worksheet.find(столбец_для_поиска).col)

        # Найдите индексы строк, содержащих value_to_delete
        indices_to_delete = [i + 1 for i, value in enumerate(column_values) if value == значение_столбца_для_удаление]

        # Удалите строки с найденными индексами (начиная с последней, чтобы не изменить индексы строк)
        for index in reversed(indices_to_delete):
            worksheet.delete_row(index)
        print(f'Информация о лиде удалена.')

    # Запуск бота
    async def start_bot(): 
        os.system("cls")
        print('Бот запущен!')
        rights_column = worksheet.col_values(3)[1:]
        id_column = worksheet.col_values(1)[1:]
        unique_ids = []
        for i, right in enumerate(rights_column):
            if right == 'Admin':
                id_value = id_column[i]
                if id_value not in unique_ids:
                    unique_ids.append(id_value)
                    await bot.send_message(int(id_value), 'Бот запущен!', buttons=command_buttons)

    # ПРОВЕРКА РЕГИСТРАЦИИ И ДАННЫЕ МЕНЕДЖЕРА
    async def get_manager_info_and_respond(event, worksheet): 
        # Получите текущую дату и время
        date_time_now = datetime.now()

        # Преобразуйте дату и время в желаемый формат
        data = date_time_now.strftime('%Y-%m-%d %H:%M')
        redact_time = data

        id = event.sender.id
        manager_username = event.sender.username

        first_column = worksheet.col_values(1)
        if str(id) in first_column:
            row_index = first_column.index(str(id)) + 1
            manager = worksheet.cell(row_index, 2).value
            prava = worksheet.cell(row_index, 3).value
            return manager, prava, id, data, redact_time, manager_username
        else:
            await event.respond("Пользователь не найден в таблице.")

    # Отправить и ждать ответ  
    async def send_and_wait(event, text): 
        async with bot.conversation(event.sender) as conv:
            await bot.send_message(event.sender, text)
            response = await conv.wait_event(events.NewMessage(from_users=event.sender))
            return response

    # Отправить и ждать ответ + кнопки
    async def send_and_wait_button(event, text, button):
        async with bot.conversation(event.sender) as conv:
            await bot.send_message(event.sender, text, buttons=button)
            response = await conv.wait_event(events.NewMessage(from_users=event.sender))
            return response.text

    # Написать сообщение
    async def napisat(poluchatel, text):
        await bot.send_message(poluchatel.sender, text)

#=======================ФУНКЦИИ==============================




#==================ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ=======================
    # Зарегистрироваться
    @bot.on(events.NewMessage(pattern='Регистрация')) 
    async def register(event):

        row_values = find_cell(str(event.sender.id), 1)

        if row_values:
            if all(row_values[2:]):
                await napisat(event, 'Ты уже зарегистрирован!'
                                    f'\nТвоё имя: {row_values[1]}'
                                    f'\nТвой ID: {row_values[0]}'
                                    f'\nТвои права: {row_values[2]}'
                                    f'\nАккаунт: {row_values[3]}')
            else:
                await napisat(event, 'Тебе запрещено!')
        else:
            response = await send_and_wait(event, 'Напиши своё настоящее имя, чтобы Антон мог тебя узнать:')

            vtab(event.sender.id, response.text, 'User', event.sender.username, 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ', 'РЕГИСТРАЦИЯ')

            await napisat(event, 'Регистрация успешна!'
                                f'\nТвой ID: {event.sender.id}'
                                f'\nАккаунт: {event.sender.username}')

    # Старт
    @bot.on(events.NewMessage(pattern='/start')) 
    async def start(event):
        await bot.send_message(event.sender, 'Привет! Это бот CRM. Ты ввел команду /start .'
                            '\nВведите Добавить для добавления клиента.'
                            '\nВведите /restart для перезапуска бота'
                            '\nВведите Лиды для просмотра лидов'
                            '\nВведите "Лид-форма" для массового добавления лидов', buttons=command_buttons)

    # Список ВСЕХ лидов
    @bot.on(events.NewMessage(pattern='Лиды')) 
    async def lead(event):        
        await get_manager_info_and_respond(event, worksheet)

        records = worksheet.get_all_records()

        sorted_records = sorted(records, key=lambda x: x['Nickname'])

        filtered_records = [record for record in sorted_records if record['Nickname'] == event.sender.username]
        for record in filtered_records:

            status_file = get_status_file_name(record['Статус'])

            keyboard_lead = [
                                    [Button.inline("Удалить", data = f"delete_lead_{record['Lead_id']}"), 
                                    Button.inline("Поменять статус", data = f"redact_lead_{record['Lead_id']}"),
                                    Button.inline("Комментировать", data = f"comment_{record['Lead_id']}")],
                        ]

            await bot.send_file(event.chat_id, status_file, caption = f"Имя лида: ` {record['Имя']}`"
                                f"\nНомер: ` {record['Номер']}`"
                                f"\nTelegram: ` {record['Телега']}`"
                                f"\nКоммент: ` {record['Коммент']}`"
                                f"\nИсточник: ` {record['Откуда']}`"
                                ,buttons=keyboard_lead,
                                )
        result = await bot.send_message(event.sender, 'Выберите действие', buttons=command_buttons)

    # Фильтр по статусу
    @bot.on(events.NewMessage(pattern=f'Статус')) 
    async def status_lead(event):

        status = await send_and_wait_button(event, 'Выбери статус лида:', status_buttons)
        await bot.send_message(event.sender, f'Отправляю лидов со статусом "{status}"...')

        filtered_records = filter_for_status(worksheet, event.sender.username, status)

        i = 0

        for record in filtered_records:
            status_file = get_status_file_name(record['Статус'])
            i += 1

            keyboard_lead = [
                        [Button.inline("Удалить", data = f"delete_lead_{record['Lead_id']}"), 
                         Button.inline("Поменять статус", data = f"redact_lead_{record['Lead_id']}"),
                         Button.inline("Комментировать", data = f"comment_{record['Lead_id']}")],
            ]
            message = await bot.send_file(event.chat_id, status_file, caption = f"Имя лида: ` {record['Имя']}`"
                                f"\nНомер: ` {record['Номер']}`"
                                f"\nTelegram: ` {record['Телега']}`"
                                f"\nКоммент: ` {record['Коммент']}`"
                                f"\nИсточник: ` {record['Откуда']}`"
                                ,buttons=keyboard_lead,
                                )

        result = await bot.send_message(event.sender, 'Выберите действие', buttons=command_buttons)


    # Обработчик кнопок
    @bot.on(events.CallbackQuery())
    async def handle_edit_lead(event):
        print('Нажали на кнопку "редактировать" ')
        user_id = event.sender_id
        button_data = event.data.decode('utf-8')
        print(f'Редактировать - button_data = {button_data}')
        if button_data.startswith("delete_lead_"):
            lead_id = int(button_data[len("delete_lead_"):]) # Получаем идентификатор лидера из данных кнопки

            records = worksheet.get_all_records()

            sorted_records = sorted(records, key=lambda x: x['Lead_id'])

            recordses = [record for record in sorted_records if record['Lead_id'] == lead_id]
            
            for lead_info in recordses:
                if lead_info:
                    # Отправляем текущую информацию о лиде и предлагаем её отредактировать
                    message =   f"Текущая информация о лиде:\n" \
                                f"Имя лида:` {lead_info['Имя']}`\n" \
                                f"Номер:` {lead_info['Номер']}`\n" \
                                f"Cтатус:` {lead_info['Статус']}`\n" \
                                f"Комментарий:` {lead_info['Коммент']}`\n\n" \
                                f"Лид удалён."
                    
                    try:
                        await event.edit(message)
                    except MessageNotModifiedError:
                        print(f'Нельзя редактировать')
                    
                    delete_row_by_value('Lead_id', str(lead_id))
        elif button_data.startswith("redact_lead_"):
            lead_id = int(button_data[len("redact_lead_"):])

            records = worksheet.get_all_records()

            sorted_records = sorted(records, key=lambda x: x['Lead_id'])

            recordses = [record for record in sorted_records if record['Lead_id'] == lead_id]

            for lead_info in recordses:
                # Отправляем сообщение с предложением ввести новый номер
                message = f"Текущая информация о лиде:\n" \
                        f"Имя лида:` {lead_info['Имя']}`\n" \
                        f"Номер:` {lead_info['Номер']}`\n" \
                        f"Cтатус:` {lead_info['Статус']}`\n" \
                        f"Комментарий:` {lead_info['Коммент']}`\n\n" \

                try:
                    await event.edit(message)
                except MessageNotModifiedError:
                    print(f'Нельзя редактировать')

                await bot.send_message(event.chat_id, f"Выберите новый статус:", buttons = status_buttons)
                # Устанавливаем состояние для ожидания нового номера
                bot.current_state[user_id] = {'action': 'redact_lead', 'lead_id': lead_id}
        elif button_data.startswith("comment_"):
            lead_id = int(button_data[len("comment_"):])

            records = worksheet.get_all_records()

            sorted_records = sorted(records, key=lambda x: x['Lead_id'])

            recordses = [record for record in sorted_records if record['Lead_id'] == lead_id]
            
            for lead_info in recordses:
                # Отправляем сообщение с предложением ввести комментарий
                message =   f"Текущая информация о лиде:\n" \
                            f"Имя лида:` {lead_info['Имя']}`\n" \
                            f"Номер:` {lead_info['Номер']}`\n" \
                            f"Cтатус:` {lead_info['Статус']}`\n" \
                            f"Комментарий:` {lead_info['Коммент']}`\n\n" \
                            f"ВВЕДИТЕ КОММЕНТАРИЙ:"
                await event.edit(message)

                # Устанавливаем состояние для ожидания комментария
                bot.current_state[user_id] = {'action': 'comment', 'lead_id': lead_id}

    # Обработчик ввода нового данных (имени, номера или комментария) лида
    @bot.on(events.NewMessage(func=lambda event: event.text and bot.current_state.get(event.sender_id)))
    async def handle_edit_lead_data(event):
        print('Новые данные установлены')
        user_id = event.sender_id
        user_state = bot.current_state.get(user_id)

        if user_state:
            action = user_state.get('action')
            new_data = event.text.strip()

            lead_id = user_state['lead_id']
            info = await get_manager_info_and_respond(event, worksheet)

            if action == 'redact_lead':
                field_name = 'Статус'
                find_and_update_google_sheet('Lead_id', lead_id, field_name, new_data)
                response_text = f"Новый статус лида: {new_data}"
            elif action == 'comment':
                field_name = 'Коммент'
                new_data = f'{info[0]}: {new_data}'
                append_to_google_sheet_cell('Lead_id', lead_id, field_name, new_data)
                response_text = f"Комментарий для лида обновлен: {new_data}"

            
            find_and_update_google_sheet('Lead_id', lead_id, 'Последнее изменение', info[4])

            

            await event.reply(response_text, buttons = command_buttons)
            del bot.current_state[user_id]

    # Добавление холодки по нику
    @bot.on(events.NewMessage(pattern='^@')) 
    async def holodka(event):

        manager, prava, id, data, redact_time, manager_username = await get_manager_info_and_respond(event, worksheet)

        match = re.search(r'@(\w+)', event.text)
        if match:
            username = match.group(1)
            try:
                # Используем get_entity для получения информации о пользователе
                user_entity = await bot.get_entity(username)
                
                lead_id = user_entity.id
                lead_name = user_entity.first_name
                lead_username = '@' + user_entity.username
            except Exception as e:
                await bot.send_message(event.sender, "Не удалось получить информацию о пользователе: {e}", buttons=command_buttons)

            comment = await send_and_wait_button(event, 'Ваш коментарий:', [Button.text('Без комментариев', resize=True, single_use=False)]) 

            status = await send_and_wait_button(event, 'Статус лида:', status_buttons)

            traffic = 'Холодка'
            lead_phone = 'Нету номера'
            
            vtab(id, manager, prava, manager_username, traffic, data, lead_username, lead_name, lead_phone, comment, status, redact_time, '', lead_id)
            
            await bot.send_message(event.sender, 'Клиент успешно добавлен в CRM.', buttons=command_buttons)

        else:
            await bot.send_message(event.sender, 'Для того, чтобы добавить лида из холодки введите его ник @nickname', buttons=command_buttons)

    @bot.on(events.NewMessage(pattern='Добавить')) # Добавить лида ++++
    async def add_client(event):

        manager, prava, id, data, redact_time, manager_username = await get_manager_info_and_respond(event, worksheet)

        traffic = await send_and_wait_button(event, 'Откуда клиент?', [Button.text('Холодка', resize=True, single_use=False), Button.text('Горячка', resize=True, single_use=False)])

        lead_phone = await send_and_wait_button(event, 'Введите номер лида:', [Button.text('Нету номера', resize=True, single_use=False)])

        lead_name = await send_and_wait_button(event, 'Введите ИМЯ лида: ', [Button.text('Не помню имени', resize=True, single_use=False)])

        lead_username = await send_and_wait_button(event, 'Введите telegram лида:', [Button.text('Нету telegram', resize=True, single_use=False)])
        
        comment = await send_and_wait_button(event, 'Ваш коментарий:', [Button.text('Без комментариев', resize=True, single_use=False)]) 
        
        status = await send_and_wait_button(event, 'Статус лида:', status_buttons)

        # Получите все значения в первом столбце (или любом другом, который, по вашему мнению, всегда заполнен)
        column_values = worksheet.col_values(1)  # Используется первый столбец как пример

        # Найдите индекс первой пустой строки (первая строка с пустым значением)
        for index, value in enumerate(column_values, start=1):
            if not value:
                print(f'Пустая строка')
            else:
                lead_id = str(index + 1)

        vtab(id, manager, prava, manager_username, traffic, data, lead_username, lead_name, lead_phone, comment, status, redact_time, ' ', lead_id)
        
        await bot.send_message(event.sender, 'Клиент успешно добавлен в CRM.', buttons=command_buttons)

    @bot.on(events.NewMessage(pattern='Лид-форма')) # Добавить кучу лидов ++++
    async def get_leads(event):
        async with bot.conversation(event.sender) as conv:

            async def get_multi_line_input(event, conv):
                user_input = []
                await bot.send_message(event.sender, 'Отправьте сюда информацию (отправьте "Готово", чтобы завершить ввод):?', buttons=[
                Button.text('готово', resize=True, single_use=False)
                ])

                while True:
                    response = await conv.wait_event(events.NewMessage(from_users=event.sender))

                    if response.raw_text.strip().lower() == 'готово':
                        break

                    user_input.append(response.raw_text)

                # Объединяем все строки в одну
                full_input = '\n'.join(user_input)

                return full_input

            # Используйте функцию для получения многострочного ввода
            text = await get_multi_line_input(event, conv)
            
            # Регулярное выражение для извлечения данных о клиентах
            pattern = r"Name:\s(.*?)\nPhone:\s(.*?)\n"

            clients = []

            # Извлекаем данные о клиентах из текста
            matches = list(re.finditer(pattern, text))

            for match in matches:
                name = match.group(1)
                phone = match.group(2)

                clients.append({
                    "Name": name,
                    "Phone": phone,
                })
            
            manager, prava, id, data, redact_time, manager_username = await get_manager_info_and_respond(event, worksheet)
            
            traffic = 'Горячка'

            for client in clients:
                lead_name = client['Name']
                lead_phone = client['Phone']

                # Получите все значения в первом столбце (или любом другом, который, по вашему мнению, всегда заполнен)
                column_values = worksheet.col_values(1)  # Используется первый столбец как пример

                # Найдите индекс первой пустой строки (первая строка с пустым значением)
                for index, value in enumerate(column_values, start=1):
                    if not value:
                        print(f'Пустая строка')
                    else:
                        lead_id = str(index + 1)
                        
                vtab(id, manager, prava, manager_username, traffic, data, ' ', lead_name, lead_phone, ' ', 'Новый', redact_time, '', lead_id)
                await event.respond(f'Добавляю {lead_name} ({lead_phone})')

            await bot.send_message(event.sender, 'Клиенты успешно добавлены в CRM.', buttons=command_buttons)
#==================ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ=======================






#======================АДМИН КОМАНДЫ==============================
    @bot.on(events.NewMessage(pattern=f'/restart')) # Перезагрузка ++++
    async def restart(event):

        cell = worksheet.find(str(event.sender_id), in_column=1)

        if cell:
            row_values = worksheet.row_values(cell.row)

            if  row_values[2] == 'User':
                await event.respond('Тебе запрещена эта команда!')
            elif  row_values[2] == 'Admin':
                await event.respond('Перезапускаю!')
                restart_program()
            else:
                await event.respond('Тебе запрещена эта команда!')

                '''
                await bot.send_message(event.sender, 'Вы уверенны что хотите перезапустить??', buttons=[
                    Button.inline('Да, я перезапускаю!', b'yes'),
                    Button.inline('Нет, не хочу', b'no')
                ])
                
                @bot.on(events.CallbackQuery)
                async def handler(event):
                    if event.data == b'yes':
                        await event.answer('Перезапускаю!', alert=True)
                        restart_program()

                @bot.on(events.CallbackQuery(data=b'no'))
                async def handler(event):
                    await event.answer('Отмена перезапуска!', alert=True)
                '''
        else:
            await event.respond('Ты не зарегистрирован!')
#=====================АДМИН КОМАНДЫ===============================
    
    
    
    
    
    
    await bot.start(bot_token=bot_token)
    await start_bot()
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
