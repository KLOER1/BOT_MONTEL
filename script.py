from Chat_bot import Bot,authorize
import time, config, sqlite3
from threading import Thread
from datetime import datetime, timedelta
from vk_api.longpoll import VkLongPoll,VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

db = sqlite3.connect('server.db', check_same_thread = False)
cursor = db.cursor()

print("Бот запущен!")

def Date():
    Bot.delta_time()
    clients_now_day = []
    clients_next_day = []
    next_day = datetime.today() + timedelta(hours=24)
    cursor.execute(f"SELECT * FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(int(next_day.strftime("%d")),config.year_month[int(next_day.strftime("%m"))-1],int(next_day.strftime("%Y"))))
    for i in cursor.fetchall():
        if i[4] not in ("?","Свободно"):
            clients_next_day.append((int(i[4]), i[3], "9:00"))
        if i[5] not in ("?","Свободно"):
            clients_next_day.append((int(i[5]), i[3], "12:00"))
        if i[6] not in ("?","Свободно"):
            clients_next_day.append((int(i[6]), i[3], "15:00"))
        if i[7] not in ("?","Свободно"):
            clients_next_day.append((int(i[7]), i[3], "18:00"))
    smena_day = True
    print(clients_next_day)
    while True:
        hour = int(datetime.now().strftime("%H"))
        minute = int(datetime.now().strftime("%M"))

        if hour == 0 and smena_day == False: ## Смена дня ##
            Bot.delta_time()
            clients_now_day = clients_next_day
            smena_day = True
            print(hour,minute,smena_day)

        elif hour == 7 and smena_day == True: ## Отправление напоминаний о записи ##
            ## Дополнительные переменные ##
            next_day = datetime.today() + timedelta(hours=17)
            clients_next_day = []
            for i in clients_now_day:
                cursor.execute(f"SELECT LAST_NAME, FIRST_NAME FROM masters WHERE ID=?",(i[1],))
                client_info = cursor.fetchone()
                Bot.send_message(i[0], "Доброе утро, напоминаю, что у вас сегодня запись в " + i[2] + " у мастера: " + client_info[0] + " " + client_info[1], VkKeyboard.get_empty_keyboard())

            cursor.execute(f"SELECT * FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(int(next_day.strftime("%d")),config.year_month[int(next_day.strftime("%m"))-1],int(next_day.strftime("%Y"))))
            for i in cursor.fetchall():
                if i[4] not in ("?","Свободно"):
                    clients_next_day.append((int(i[4]), i[3], "9:00"))
                if i[5] not in ("?","Свободно"):
                    clients_next_day.append((int(i[5]), i[3], "12:00"))
                if i[6] not in ("?","Свободно"):
                    clients_next_day.append((int(i[6]), i[3], "15:00"))
                if i[7] not in ("?","Свободно"):
                    clients_next_day.append((int(i[7]), i[3], "18:00"))
            print(clients_next_day)
            smena_day = False
            print(hour,minute,smena_day)
        
        elif (hour == 21 and smena_day == True) or (hour in (12,15,18) and smena_day == False):
            for i in clients_now_day: # <- Сделать проверку!
                if i[2] == {"12":"9:00", "15":"12:00", "18":"15:00", "21":"18:00"}[str(hour)]:
                    cursor.execute(f"UPDATE clients SET RECORD_STAT='Нет записи',DAY_RECORD=0,MONTH_RECORD='?',YEAR_RECORD=0 WHERE ID=?",(i[0],)); db.commit()
                    clients_now_day.remove(i)
            smena_day = False if hour == 21 else True
        
        elif (hour in (11,14,17) and minute == 40 and smena_day == True) or (hour == 8 and minute == 40 and smena_day == False):
            for i in clients_now_day:
                if i[2] == {"8":"9:00", "11":"12:00", "14":"15:00", "17":"18:00"}[str(hour)]:
                    cursor.execute(f"SELECT LAST_NAME, FIRST_NAME FROM clients WHERE ID=?",(i[0],))
                    client_info = cursor.fetchone()
                    Bot.send_message(i[1], "| Карточка клиента на {TIME} |\nИмя : {FIRST_NAME}\n___________________________\n\nФамилия : {LAST_NAME}\n___________________________\n\nКейс : {CASE_NAME}\n___________________________\n\nСтоимость : {PRICE}\n___________________________\n\nПоследний визит : {LAST_VISIT}".format(TIME= "9:00" if hour == 8 else "12:00" if hour == 11 else "15:00" if hour == 14 else "18:00",FIRST_NAME=client_info[1],LAST_NAME=client_info[0],CASE_NAME="Решение на месте",PRICE="Не известно",LAST_VISIT="Ещё не был(а)"), None)
            smena_day = True if hour == 8 else False

Thread(target=Date, args=()).start()

def BOT():
    while True:
        try:
            for event in VkLongPoll(authorize).listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    
                    msg = event.text
                    user_id = event.user_id
                    keyboard = VkKeyboard()

                    ## Дополнительные переменные ## --------------------------------------------------------------------------------------------------------------------------------
                    try:
                        cursor.execute("SELECT USER_STAT FROM users WHERE ID={}".format(user_id))
                        db.commit()
                        index_user = cursor.fetchone()[0]
                    except:
                        cursor.execute("INSERT INTO users VALUES ({}, {}, {})".format(user_id, 0, 0)); db.commit()
                        index_user = 0

                    Bot.messages_typing(user_id)
                    time.sleep(1.5)

                    if index_user == 0: # Выбор роли
                        ## Дополнительные переменные ## ------------------------------------------------------------------------------------------------------------------------------------
                        cursor.execute(f"SELECT BOT_STAT FROM users WHERE ID=?",(user_id,))
                        index_status_bot = cursor.fetchone()[0]

                        if (index_status_bot == 0 and msg == "Начать") or (index_status_bot in (1,2) and msg == "Вернуться"):
                            ## Клавиатура ##
                            keyboard.add_button("Клиентом", color=VkKeyboardColor.POSITIVE)
                            keyboard.add_button("Мастером", color=VkKeyboardColor.POSITIVE)
                            ## Данные ##
                            cursor.execute(f"UPDATE users SET BOT_STAT=1 WHERE ID=?",(user_id,)); db.commit()
                            ## Сообщение ##
                            Bot.send_message(user_id, 'Я Монтэль - чат-бот студии маникюра, кем вы являетесь?', keyboard.get_keyboard())
                        
                        elif index_status_bot == 1 and msg == "Клиентом":
                            ## Клавиатура ##
                            keyboard.add_button("Перейти к знакомству", color=VkKeyboardColor.POSITIVE)
                            ## Данные ##
                            cursor.execute(f"INSERT INTO clients VALUES (?, '?', '?', 0, 0, 'Нет записи', 0, '?', 0, 0, 0)",(user_id,)); db.commit()
                            cursor.execute(f"UPDATE users SET USER_STAT=1,BOT_STAT=3 WHERE ID=?",(user_id,)); db.commit()
                            ## Сообщение ##
                            Bot.send_message(user_id, 'Отлично, давайте я расскажу про нашу студию?', keyboard.get_keyboard())

                        elif index_status_bot == 1 and msg == "Мастером":
                            ## Клавиатура ##
                            keyboard.add_button("Вернуться", color=VkKeyboardColor.POSITIVE)
                            ## Данные ##
                            cursor.execute(f"UPDATE users SET BOT_STAT=2 WHERE ID=?",(user_id,)); db.commit()
                            ## Сообщение ##
                            Bot.send_message(user_id, 'Чтобы подтвердить вашу роль, пожалуйста введите цифровой ключ!', keyboard.get_keyboard())

                        elif index_status_bot == 2 and msg != "Вернуться":
                            cursor.execute("SELECT KEY_VERIFICATION,VERIFICATION_STAT FROM masters")

                            if (msg, "Неверифицирован(а)") in cursor.fetchall():
                                ## Клавиатура ##
                                keyboard.add_button("Перейти в Личный кабинет мастера", color=VkKeyboardColor.POSITIVE)
                                ## Данные ##
                                cursor.execute(f"UPDATE users SET USER_STAT=2,BOT_STAT=3 WHERE ID=?",(user_id,)); db.commit()
                                cursor.execute(f"UPDATE masters SET ID=?,VERIFICATION_STAT='Верифицирован(а)' WHERE KEY_VERIFICATION=?",(user_id,msg)); db.commit()
                                ## Сообщение ##
                                Bot.send_message(user_id, 'Вы стали мастером, давайте перейдём в Личный кабинет!', keyboard.get_keyboard())

                            else:
                                ## Клавиатура ##
                                keyboard.add_button("Вернуться", color=VkKeyboardColor.POSITIVE)
                                ## Сообщение ##
                                Bot.send_message(user_id, 'Код неверен, попробуйте ещё раз ввести цифровой ключ!', keyboard.get_keyboard())
                        
                        else:
                            Bot.send_message(user_id,'Такого ответа нет\n(Ошибка US0)', None)

                    elif index_user == 1: # Роль Клиента
                        ## Дополнительные переменные ## ----------------------------------------------------------------------------------------------------------------------------
                        cursor.execute("SELECT BOT_STAT FROM clients WHERE ID={}".format(user_id))
                        index_status_bot = cursor.fetchone()[0]

                        ## Знакомство ##--------------------------------------------------------------------------------------------------------------------------------------------

                        if index_status_bot in (0,1,2):

                            if index_status_bot == 0 and msg == "Перейти к знакомству": ## Знакомство, второе сообщения
                                ## Клавиатура ##
                                keyboard.add_button("Хорошо", color=VkKeyboardColor.POSITIVE)
                                ## Данные ##
                                cursor.execute(f"UPDATE clients SET BOT_STAT=1 WHERE ID=?",(user_id,)); db.commit()
                                Bot.send_message(user_id,'Наша работа - это наше призвание, и мы стараемся сделать все возможное, чтобы каждый наш клиент был доволен результатом. Мы используем только самые качественные материалы и инструменты, чтобы обеспечить безопасность и комфорт во время процедуры.', keyboard.get_keyboard())
                            
                            elif msg == "Хорошо" and index_status_bot == 1: ## Знакомство, третье сообщение
                                ## Клавиатура ##
                                keyboard.add_button("Отлично", color=VkKeyboardColor.POSITIVE)
                                ## Данные ##
                                cursor.execute("UPDATE clients SET BOT_STAT=2 WHERE ID={}".format(user_id)); db.commit()
                                ## Сообщение ##
                                Bot.send_message(user_id,'Кроме того, мастер постоянно обучается новым техникам и трендам в маникюре, чтобы предложить вам самые актуальные варианты дизайна ногтей. Он готов работать с любой формой и длиной ногтей, чтобы создать идеальный образ для вас.', keyboard.get_keyboard())

                            elif msg == "Отлично" and index_status_bot == 2: ## Знакомство, последние два сообщения
                                ## Данные ##
                                cursor.execute("UPDATE clients SET BOT_STAT=3 WHERE ID={}".format(user_id)); db.commit()
                                ## Сообщение ##
                                Bot.send_message(user_id,'Но самое главное, что мастер делает - это заботится о ваших руках и ногтях. Мы знаем, как важно иметь здоровые и ухоженные руки, поэтому мастер всегда уделяет особое внимание их состоянию. Наши клиенты всегда уходят от нас с красивыми и здоровыми ногтями, которые будут радовать их на протяжении долгого времени.',keyboard.get_empty_keyboard())
                                Bot.messages_typing(user_id)
                                time.sleep(5)
                                ## Клавиатура ##
                                keyboard.add_button("Перейти дальше", color=VkKeyboardColor.POSITIVE)
                                ## Сообщение ##
                                Bot.send_message(user_id,'Не упустите возможность получить лучший маникюр в городе! Запишитесь на прием уже сегодня. Я обещаю, что вы не пожалеете о своем выборе!',keyboard.get_keyboard())

                            else:
                                Bot.send_message(user_id,'Такого ответа нет\n(Ошибка US1_DS0-2)', None)
                        
                        ## Регистрация ## ------------------------------------------------------------------------------------------------------------------------------------------

                        elif index_status_bot in (3,4,5):
                            ## Дополнительные переменные ## --------------------------------------------------------------------------------------------------------------------------------
                            cursor.execute("SELECT * FROM clients WHERE ID={}".format(user_id))
                            client_info = cursor.fetchone()

                            if msg == 'Перейти дальше' and index_status_bot == 3:
                                ## Клавиатура ##
                                keyboard.add_button("Всё верно", VkKeyboardColor.POSITIVE)
                                keyboard.add_button("Указать верные данные", VkKeyboardColor.SECONDARY)
                                ## Данные ##
                                cursor.execute("UPDATE clients SET BOT_STAT=4 WHERE ID={}".format(user_id)); db.commit()
                                ## Сообщение ##
                                Bot.send_message(user_id, "Чтобы записаться, я хочу внести ваше имя и фамилию, подскажите, на вашем аккаунте ВК данные указаны верно?", keyboard.get_keyboard())
                        
                            elif (msg == "Указать верные данные" and index_status_bot == 4) or (msg != "Да" and index_status_bot == 5):

                                if index_status_bot == 4:
                                    ## Данные ##
                                    cursor.execute("UPDATE clients SET BOT_STAT=5 WHERE ID={}".format(user_id)); db.commit()
                                    ## Сообщение ##
                                    Bot.send_message(user_id, "Как вас зовут?",None)

                                elif client_info[2] == '?':
                                    ## Данные ##
                                    cursor.execute(f"UPDATE clients SET FIRST_NAME=? WHERE ID=?",(msg, user_id)); db.commit()
                                    ## Сообщение ##
                                    Bot.send_message(user_id, "Какая у вас фамилия?",None)
                                
                                elif client_info[1] == '?':
                                    ## Клавиатура ##
                                    keyboard.add_button("Да", color=VkKeyboardColor.POSITIVE)
                                    keyboard.add_button("Изменить", color=VkKeyboardColor.SECONDARY)
                                    ## Данные ##
                                    cursor.execute(f"UPDATE clients SET LAST_NAME=? WHERE ID=?",(msg, user_id)); db.commit()
                                    cursor.execute("SELECT * FROM clients WHERE ID={}".format(user_id))
                                    client_info = cursor.fetchone()
                                    ## Сообщение ##
                                    Bot.send_message(user_id, client_info[1] + ' ' + client_info[2] + ', всё верно?',keyboard.get_keyboard())
                                    
                                elif client_info[1] != '?' and msg == 'Изменить':
                                    ## Данные ##
                                    cursor.execute("UPDATE clients SET LAST_NAME='?',FIRST_NAME='?' WHERE ID={}".format(user_id)); db.commit()
                                    ## Сообщение ##
                                    Bot.send_message(user_id, "Как вас зовут?",None)

                            elif (msg == "Всё верно" and index_status_bot == 4) or (msg == "Да" and client_info[1] != '?' and index_status_bot == 5):
                                ## Клавиатура ##
                                keyboard.add_button("Посмотреть скидки", VkKeyboardColor.POSITIVE)
                                keyboard.add_button("Хочу записаться!", VkKeyboardColor.POSITIVE)
                                ## Данные ##
                                if msg == "Всё верно" and index_status_bot == 4:
                                    cursor.execute(f"UPDATE clients SET LAST_NAME=?, FIRST_NAME=? WHERE ID=?",(Bot.user_get(user_id)['last_name'],Bot.user_get(user_id)['first_name'], user_id)); db.commit()
                                    cursor.execute("SELECT * FROM clients WHERE ID={}".format(user_id))
                                    client_info = cursor.fetchone()
                                cursor.execute(f"UPDATE clients SET BOT_STAT=6 WHERE ID=?",(user_id,)); db.commit()
                                ## Сообщение ##
                                Bot.send_message(user_id, 'Отлично, уже создаю ваш Личный кабинет!',keyboard.get_empty_keyboard())
                                time.sleep(3)
                                Bot.send_message(user_id, client_info[2] + ", вот ваш личный кабинет!" + "\nСтатус записи: " + client_info[5] + "\nАктивная скидка: Нет", keyboard.get_keyboard())
                            
                            else:
                                Bot.send_message(user_id,'Такого ответа нет\n(Ошибка US1_DS3-5)',None)
                        
                        ## Личный профиль ## ---------------------------------------------------------------------------------------------------------------------------------------

                        elif index_status_bot in (6,7,8,9,10,11):
                            ## Дополнительные переменные ## --------------------------------------------------------------------------------------------------------------------------------
                            cursor.execute("SELECT * FROM clients WHERE ID={}".format(user_id))
                            client_info = cursor.fetchone()
                            
                            if msg == "Вернуться в личный профиль" and index_status_bot in (7,9,10,11): ## Личный кабинет
                                ## Данные ##
                                cursor.execute(f"UPDATE clients SET BOT_STAT=6 WHERE ID=?",(user_id,)); db.commit()
                                ## Клавиатура ##
                                keyboard.add_button("Хочу записаться!", VkKeyboardColor.POSITIVE)
                                ## Сообщение ##
                                Bot.send_message(user_id, client_info[2] + ", вот ваш личный кабинет!" + "\nСтатус записи: " + client_info[5] + "\nАктивная скидка: Нет", keyboard.get_keyboard())

                            elif (msg == 'Хочу записаться!' and index_status_bot == 6 and client_info[5] == "Нет записи") or (msg == "Вернуться к выбору дня" and index_status_bot == 8): ## Запись: Выбор дня
                                if (client_info[7] == {"1":"Января", "2":"Февраля", "3":"Марта", "4":"Апреля", "5":"Мая", "6":"Июня", "7":"Июля", "8":"Августа", "9":"Сентября", "10":"Октября", "11":"Ноября", "12":"Декабря"}[str(config.next1month)] or msg == "Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)] or msg == "Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)]) and msg not in ("Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next2month)], "Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.nowmonth)]):
                                    month = config.year_month[config.next1month-1]
                                    year = config.next1year
                                    start_day = 1
                                elif (client_info[7] == {"1":"Января", "2":"Февраля", "3":"Марта", "4":"Апреля", "5":"Мая", "6":"Июня", "7":"Июля", "8":"Августа", "9":"Сентября", "10":"Октября", "11":"Ноября", "12":"Декабря"}[str(config.next2month)] or msg == "Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next2month)]) and msg not in ("Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)], "Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.nowmonth)]):
                                    month = config.year_month[config.next2month-1]
                                    year = config.next2year
                                    start_day = 1
                                else:
                                    month = config.year_month[config.nowmonth-1]
                                    year = config.nowyear
                                    start_day = config.nowday
                                cursor.execute(f"UPDATE clients SET BOT_STAT=7, MONTH_RECORD=?, YEAR_RECORD=? WHERE ID=?",(month, year, user_id)); db.commit()
                                count = 0
                                year_month = config.year[year%4][{"Января":1, "Февраля":2, "Марта":3, "Апреля":4, "Мая":5, "Июня":6, "Июля":7, "Августа":8, "Сентября":9, "Октября":10, "Ноября":11, "Декабря":12}[str(month)]-1]
                                ## Клавиатура ##
                                for i in range(start_day,year_month + 1):
                                    count += 1
                                    cursor.execute(f"SELECT * FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(i, month, year))
                                    day_info = cursor.fetchone()
                                    if day_info == None:
                                        day_info = [None,None,None,None,"?","?","?","?"]
                                    k = Bot.day_stat(day_info)

                                    keyboard.add_button("Записей нет" if k == "1" else "День занят" if k == "2" else str(i)+" "+month, VkKeyboardColor.SECONDARY if k == "1" else VkKeyboardColor.NEGATIVE if k == "2" else VkKeyboardColor.POSITIVE if k == "3" else VkKeyboardColor.PRIMARY)

                                    if count%4==0 and i != year_month:
                                        keyboard.add_line()

                                keyboard.add_line()
                                if month == {"1":"Января", "2":"Февраля", "3":"Марта", "4":"Апреля", "5":"Мая", "6":"Июня", "7":"Июля", "8":"Августа", "9":"Сентября", "10":"Октября", "11":"Ноября", "12":"Декабря"}[str(config.nowmonth)]:
                                    keyboard.add_button("Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)], VkKeyboardColor.POSITIVE)
                                elif month == {"1":"Января", "2":"Февраля", "3":"Марта", "4":"Апреля", "5":"Мая", "6":"Июня", "7":"Июля", "8":"Августа", "9":"Сентября", "10":"Октября", "11":"Ноября", "12":"Декабря"}[str(config.next1month)]:
                                    keyboard.add_button("Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.nowmonth)], VkKeyboardColor.POSITIVE)
                                    keyboard.add_button("Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next2month)], VkKeyboardColor.POSITIVE)
                                else:
                                    keyboard.add_button("Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)], VkKeyboardColor.POSITIVE)
                                keyboard.add_line()
                                keyboard.add_button("Вернуться в личный профиль", VkKeyboardColor.POSITIVE)
                                ## Сообщение ##
                                Bot.send_message(user_id, 'Выберите день на который хотите записаться', keyboard.get_keyboard())

                            elif (msg in [(str(x) + " " + y) for y in (config.year_month[config.nowmonth-1],config.year_month[config.next1month-1],config.year_month[config.next2month-1]) for x in range(1,32)] and index_status_bot == 7): ## Запись: Выбор времени для записи
                                try:
                                    try:
                                        day = int(msg[:2])
                                    except:
                                        day = client_info[6]
                                except:
                                    day = 0
                                
                                nowday=1
                                if config.nowmonth == client_info[7]:
                                    nowday = config.nowday

                                if day in (x for x in range(nowday,config.year[client_info[8]%4][{"Января":1,"Февраля":2,"Марта":3,"Апреля":4,"Мая":5,"Июня":6,"Июля":7,"Августа":8,"Сентября":9,"Октября":10,"Ноября":11,"Декабря":12,}[client_info[7]]-1] + 1)):
                                    ## Данные ##
                                    cursor.execute(f"UPDATE clients SET BOT_STAT=8, DAY_RECORD=? WHERE ID=?",(day,user_id)); db.commit()
                                    hour = int(datetime.now().strftime("%H"))
                                    minute = int(datetime.now().strftime("%M"))
                                    ## Дополнительные переменные ##
                                    cursor.execute(f"SELECT * FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(day, client_info[7], client_info[8]))
                                    day_info = cursor.fetchall()
                                    # Клавиатура ##
                                    if day_info != []:
                                        cursor.execute(f"SELECT TIME900 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(day, client_info[7], client_info[8]))
                                        time_900 = cursor.fetchall()[0]
                                        cursor.execute(f"SELECT TIME1200 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(day, client_info[7], client_info[8]))
                                        time_1200 = cursor.fetchall()[0]
                                        cursor.execute(f"SELECT TIME1500 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(day, client_info[7], client_info[8]))
                                        time_1500 = cursor.fetchall()[0]
                                        cursor.execute(f"SELECT TIME1800 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(day, client_info[7], client_info[8]))
                                        time_1800 = cursor.fetchall()[0]
                                        if day == config.nowday and (hour < 8 or (hour == 8 and minute < 40)):
                                            if "Свободно" in time_900:
                                                keyboard.add_button("9:00", VkKeyboardColor.POSITIVE)
                                            elif "Свободно" not in time_900 and "?" not in time_900:
                                                keyboard.add_button("Время занято", VkKeyboardColor.NEGATIVE)
                                            else:
                                                keyboard.add_button("Записи нет", VkKeyboardColor.SECONDARY)
                                        else:
                                            keyboard.add_button("Запись прошла", VkKeyboardColor.NEGATIVE)

                                        if day == config.nowday and (hour < 11 or (hour == 11 and minute < 40)):
                                            if "Свободно" in time_1200:
                                                keyboard.add_button("12:00", VkKeyboardColor.POSITIVE)
                                            elif "Свободно" not in time_1200 and "?" not in time_1200:
                                                keyboard.add_button("Время занято", VkKeyboardColor.NEGATIVE)
                                            else:
                                                keyboard.add_button("Записи нет", VkKeyboardColor.SECONDARY)
                                        else:
                                            keyboard.add_button("Запись прошла", VkKeyboardColor.NEGATIVE)
                                        keyboard.add_line()
                                        if day == config.nowday and (hour < 14 or (hour == 14 and minute < 40)):
                                            if "Свободно" in time_1500:
                                                keyboard.add_button("15:00", VkKeyboardColor.POSITIVE)
                                            elif "Свободно" not in time_1500 and "?" not in time_1500:
                                                keyboard.add_button("Время занято", VkKeyboardColor.NEGATIVE)
                                            else:
                                                keyboard.add_button("Записи нет", VkKeyboardColor.SECONDARY)
                                        else:
                                            keyboard.add_button("Запись прошла", VkKeyboardColor.NEGATIVE)

                                        if day == config.nowday and (hour < 17 or (hour == 17 and minute < 40)):
                                            if "Свободно" in time_1800:
                                                keyboard.add_button("18:00", VkKeyboardColor.POSITIVE)
                                            elif "Свободно" not in time_1800 and "?" not in time_1800:
                                                keyboard.add_button("Время занято", VkKeyboardColor.NEGATIVE)
                                            else:
                                                keyboard.add_button("Записи нет", VkKeyboardColor.SECONDARY)
                                        else:
                                            keyboard.add_button("Запись прошла", VkKeyboardColor.NEGATIVE)
                                    keyboard.add_line()
                                    keyboard.add_button("Вернуться к выбору дня", VkKeyboardColor.SECONDARY)
                                    ## Сообщение ##
                                    Bot.send_message(user_id, 'Выберите время, на которое хотите записаться', keyboard.get_keyboard())

                                elif day in (x for x in range(1,config.nowday)):
                                    Bot.send_message(user_id,'Вы ввели день, который уже прошёл!\nОшибка US1_BS7_past_day',None)

                                else:
                                    Bot.send_message(user_id,'Вы ввели некоректные день!\nОшибка US1_BS7_incorrect_day',None)
                            
                            elif msg in ("9:00","12:00","15:00","18:00") and index_status_bot == 8: ## Подтверждение записи
                                day = client_info[6]
                                hour = int(datetime.now().strftime("%H"))
                                cursor.execute(f"SELECT TIME900 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8]))
                                time_900 = cursor.fetchone()[0]
                                cursor.execute(f"SELECT TIME1200 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8]))
                                time_1200 = cursor.fetchone()[0]
                                cursor.execute(f"SELECT TIME1500 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8]))
                                time_1500 = cursor.fetchone()[0]
                                cursor.execute(f"SELECT TIME1800 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8]))
                                time_1800 = cursor.fetchone()[0]
                                hour_time_record = 8 if msg == "9:00" else 11 if msg == "12:00" else 14 if msg == "15:00" else 17
                                if "Свободно" in (time_900,time_1200,time_1500,time_1800) and (day == config.nowday and (hour < hour_time_record or (hour == hour_time_record and int(datetime.now().strftime("%M")) < 40))):
                                    ## Данные ##
                                    cursor.execute(f"UPDATE clients SET BOT_STAT=9, RECORD_STAT=? WHERE ID=?",(("На " + str(client_info[6]) + " " + client_info[7] + " в " + msg),user_id)); db.commit()
                                    if msg == "9:00":
                                        cursor.execute(f"UPDATE day_record SET TIME900=? WHERE DAY=? AND MONTH=? AND YEAR=?",(user_id,client_info[6],client_info[7],client_info[8])); db.commit()
                                    elif msg == "12:00":
                                        cursor.execute(f"UPDATE day_record SET TIME1200=? WHERE DAY=? AND MONTH=? AND YEAR=?",(user_id,client_info[6],client_info[7],client_info[8])); db.commit()
                                    elif msg == "15:00":
                                        cursor.execute(f"UPDATE day_record SET TIME1500=? WHERE DAY=? AND MONTH=? AND YEAR=?",(user_id,client_info[6],client_info[7],client_info[8])); db.commit()
                                    else:
                                        cursor.execute(f"UPDATE day_record SET TIME1800=? WHERE DAY=? AND MONTH=? AND YEAR=?",(user_id,client_info[6],client_info[7],client_info[8])); db.commit()
                                    ## Клавиатура ##
                                    keyboard.add_button("Вернуться в личный профиль", VkKeyboardColor.POSITIVE)
                                    ## Сообщение ##
                                    Bot.send_message(user_id, 'Отлично, я записал вас!\nЯ напомню вам в 7:00 в день записи!', keyboard.get_keyboard())
                                else:
                                    ## Клавиатура ##
                                    keyboard.add_button("Вернуться", VkKeyboardColor.POSITIVE)
                                    ## Сообщение ##
                                    Bot.send_message(user_id, 'К сожалению, это время занято, пожалуйста, выберите другое время', None)
                                
                            elif msg == "Хочу записаться!" and client_info[5] != "Нет записи" and index_status_bot == 6:
                                ## Данные ##
                                cursor.execute(f"UPDATE clients SET BOT_STAT=10 WHERE ID=?",(user_id,)); db.commit()
                                ## Клавиатура ##
                                keyboard.add_button("Вернуться в личный профиль", VkKeyboardColor.POSITIVE)
                                keyboard.add_button("Отменить запись", VkKeyboardColor.SECONDARY)
                                ## Сообщение ##
                                Bot.send_message(user_id, "Вы уже записаны! Я могу отменить запись, чтобы вы могли выбрать удобный для вас день", keyboard.get_keyboard())

                            elif msg == "Отменить запись" and index_status_bot == 10:
                                ## Данные ##
                                cursor.execute(f"SELECT TIME900, TIME1200, TIME1500, TIME1800 FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8]))
                                client_mas = cursor.fetchone()
                                if client_mas[0] == str(user_id):
                                    cursor.execute(f"UPDATE day_record SET TIME900='Свободно' WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8])); db.commit()
                                elif client_mas[1] == str(user_id):
                                    cursor.execute(f"UPDATE day_record SET TIME1200='Свободно' WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8])); db.commit()
                                elif client_mas[2] == str(user_id):
                                    cursor.execute(f"UPDATE day_record SET TIME1500='Свободно' WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8])); db.commit()
                                else:
                                    cursor.execute(f"UPDATE day_record SET TIME1800='Свободно' WHERE DAY=? AND MONTH=? AND YEAR=?",(client_info[6], client_info[7], client_info[8])); db.commit()
                                cursor.execute(f"UPDATE clients SET BOT_STAT=11, RECORD_STAT='Нет записи', DAY_RECORD=0 WHERE ID=?",(user_id,)); db.commit()
                                ## Клавиатура ##
                                keyboard.add_button("Вернуться в личный профиль", VkKeyboardColor.POSITIVE)
                                ## Сообщение ##
                                Bot.send_message(user_id, "Запись отменена", keyboard.get_keyboard())
                            
                            else:
                                Bot.send_message(user_id,'Такого ответа нет\n(Ошибка US1_DS6-11)',None)
                    
                    elif index_user == 2:
                        ## Дополнительные переменные ## ----------------------------------------------------------------------------------------------------------------------------
                        cursor.execute("SELECT * FROM masters WHERE ID={}".format(user_id))
                        masters_info = cursor.fetchone()
                        
                        if (msg == "Перейти в Личный кабинет мастера" and masters_info[5] == 0) or (msg == "Вернуться в личный кабинет мастера" and masters_info[5] in (1,2,3)): ## Личный кабинет мастера ##
                            ## Данные ##
                            cursor.execute("UPDATE masters SET BOT_STAT=0 WHERE ID={}".format(user_id)); db.commit()
                            ## Клавиатура ##
                            keyboard.add_button("Редактировать график", VkKeyboardColor.POSITIVE)
                            keyboard.add_line()
                            keyboard.add_button("Начать работу!", VkKeyboardColor.POSITIVE)
                            ## Сообщение ##
                            Bot.send_message(user_id, masters_info[4] + ", вот ваш личный кабинет мастера!", keyboard.get_keyboard())

                        elif (msg == "Редактировать график" and masters_info[5] == 0) or (msg == "Вернуться к текущему месяцу" and masters_info[5] == 2) or (msg == "Вернуться" and masters_info[5] == 4 and masters_info[7] == config.year_month[config.nowmonth-1]) or (msg == "Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.nowmonth)] and masters_info[5] == 2): ## Текущий месяц ##
                            ## Данные ##
                            cursor.execute(f"UPDATE masters SET BOT_STAT=1, DAY_RECORDING=0, MONTH_RECORDING=?, YEAR_RECORDING=? WHERE ID=?",(config.year_month[config.nowmonth-1], config.nowyear, user_id)); db.commit()
                            ## Обновление данных ##
                            cursor.execute("SELECT * FROM masters WHERE ID={}".format(user_id))
                            masters_info = cursor.fetchone()
                            ## Дополнительные переменные ##
                            year_month = config.year[config.nowyear%4][config.nowmonth-1]
                            count = 0
                            ## Клавиатура ##
                            for i in range(config.nowday,year_month + 1):
                                count += 1
                                cursor.execute(f"SELECT * FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(i, masters_info[7], masters_info[8]))
                                day_info = cursor.fetchone()
                                if day_info == None:
                                    day_info = [None,None,None,None,"?","?","?","?"]
                                if Bot.day_stat(day_info) == "1":
                                    keyboard.add_button(str(i)+" "+masters_info[7],VkKeyboardColor.NEGATIVE)
                                else:
                                    keyboard.add_button(str(i)+" "+masters_info[7],VkKeyboardColor.POSITIVE)

                                if count%4==0 and i != year_month:
                                    keyboard.add_line()

                            keyboard.add_line()
                            keyboard.add_button("Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)], VkKeyboardColor.POSITIVE)
                            keyboard.add_line()
                            keyboard.add_button("Вернуться в личный кабинет мастера", VkKeyboardColor.POSITIVE)
                            ## Сообщение ##
                            Bot.send_message(user_id, 'Выберите день на который хотите записаться', keyboard.get_keyboard())

                        elif  (msg == "Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)] and masters_info[5] == 1) or (msg == "Вернуться" and masters_info[5] == 4 and masters_info[7] == config.year_month[config.next1month-1]) or (msg == "Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)] and masters_info[5] == 3): ## Следующий месяц ##
                            ## Данные ##
                            cursor.execute(f"UPDATE masters SET BOT_STAT=2, DAY_RECORDING=0, MONTH_RECORDING=?, YEAR_RECORDING=? WHERE ID=?",(config.year_month[config.next1month-1], config.next1year, user_id)); db.commit()
                            ## Обновление данных ##
                            cursor.execute("SELECT * FROM masters WHERE ID={}".format(user_id))
                            masters_info = cursor.fetchone()
                            ## Клавиатура ##
                            year_month = config.year[config.next1year%4][config.next1month-1]
                            count = 0
                            for i in range(1,year_month + 1):
                                count += 1
                                cursor.execute(f"SELECT * FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(i, masters_info[7], masters_info[8]))
                                day_info = cursor.fetchone()
                                if day_info == None:
                                    day_info = [None,None,None,None,"?","?","?","?"]
                                if Bot.day_stat(day_info) == "1":
                                    keyboard.add_button(str(i)+" "+masters_info[7],VkKeyboardColor.NEGATIVE)
                                else:
                                    keyboard.add_button(str(i)+" "+masters_info[7],VkKeyboardColor.POSITIVE)

                                if count%4==0 and i != year_month:
                                    keyboard.add_line()

                            keyboard.add_line()
                            keyboard.add_button("Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.nowmonth)], VkKeyboardColor.POSITIVE)
                            keyboard.add_button("Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next2month)], VkKeyboardColor.POSITIVE)
                            keyboard.add_line()
                            keyboard.add_button("Вернуться в личный кабинет мастера", VkKeyboardColor.POSITIVE)
                            ## Сообщение ##
                            Bot.send_message(user_id, 'Выберите день на который хотите записаться', keyboard.get_keyboard())
                        
                        elif  (msg == "Перейти к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next2month)] and masters_info[5] == 2) or (msg == "Вернуться" and masters_info[5] == 4 and masters_info[7] == config.year_month[config.next2month-1]): ## Второй следующий месяц ##
                            ## Данные ##
                            cursor.execute(f"UPDATE masters SET BOT_STAT=3, DAY_RECORDING=0, MONTH_RECORDING=?, YEAR_RECORDING=? WHERE ID=?",(config.year_month[config.next2month-1],config.next2year,user_id)); db.commit()
                            ## Обновление данных ##
                            cursor.execute("SELECT * FROM masters WHERE ID={}".format(user_id))
                            masters_info = cursor.fetchone()
                            ## Клавиатура ##
                            year_month = config.year[config.next2year%4][config.next2month-1]
                            count = 0
                            for i in range(1,year_month + 1):
                                count += 1
                                cursor.execute(f"SELECT * FROM day_record WHERE DAY=? AND MONTH=? AND YEAR=?",(i, masters_info[7], masters_info[8]))
                                day_info = cursor.fetchone()
                                if day_info == None:
                                    day_info = [None,None,None,None,"?","?","?","?"]
                                if Bot.day_stat(day_info) == "1":
                                    keyboard.add_button(str(i)+" "+masters_info[7],VkKeyboardColor.NEGATIVE)
                                else:
                                    keyboard.add_button(str(i)+" "+masters_info[7],VkKeyboardColor.POSITIVE)

                                if count%4==0 and i != year_month:
                                    keyboard.add_line()

                            keyboard.add_line()
                            keyboard.add_button("Вернуться к " + {"1":"январю","2":"февралю","3":"марту","4":"апрелю","5":"маю","6":"Июню","7":"июлю","8":"августу","9":"сентябрю","10":"октябрю","11":"ноябрю","12":"декабрю",}[str(config.next1month)], VkKeyboardColor.POSITIVE)
                            keyboard.add_line()
                            keyboard.add_button("Вернуться в личный кабинет мастера", VkKeyboardColor.POSITIVE)
                            ## Сообщение ##
                            Bot.send_message(user_id, 'Выберите день на который хотите записаться', keyboard.get_keyboard())

                        elif (masters_info[5] in (1,2,3) and masters_info[6] == 0) or masters_info[5] == 4:
                            ## Дополнительные переменные ##
                            try:
                                day = int(msg[:2] if msg not in ("9:00","12:00","15:00","18:00") else "Error")
                                cursor.execute(f"UPDATE masters SET BOT_STAT=4, DAY_RECORDING=? WHERE ID=?",(day, user_id)); db.commit()
                            except:
                                try:
                                    day = masters_info[6]
                                except:
                                    day = 0

                            nowday = config.nowday if config.nowmonth == masters_info[7] else 1

                            if day in (x for x in range(nowday,config.year[masters_info[8]%4][{"Января":1,"Февраля":2,"Марта":3,"Апреля":4,"Мая":5,"Июня":6,"Июля":7,"Августа":8,"Сентября":9,"Октября":10,"Ноября":11,"Декабря":12,}[masters_info[7]]-1] + 1)):
                                hour = int(datetime.now().strftime("%H"))
                                hour_time_record = 8 if msg == "9:00" else 11 if msg == "12:00" else 14 if msg == "15:00" else 17
                                past_time_bool = (day == config.nowday and (hour < hour_time_record or (hour == hour_time_record and int(datetime.now().strftime("%M")) < 40))) if day == config.nowday else True
                                cursor.execute(f"SELECT * FROM day_record WHERE MASTER_ID=? AND DAY=? AND MONTH=? AND YEAR=?",(user_id,day,masters_info[7],masters_info[8]))
                                day_info = cursor.fetchone()
                                if day_info == None:
                                    day_info = [day, masters_info[7], masters_info[8], user_id, "?", "?", "?", "?"]
                                    cursor.execute(f"INSERT INTO day_record VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(day, masters_info[7], masters_info[8], user_id, "Свободно" if msg == "9:00" and day_info[4] == "?" else "?" if msg == "9:00" and day_info[4] == "Свободно" else day_info[4], "Свободно" if msg == "12:00" and day_info[5] == "?" else "?" if msg == "12:00" and day_info[5] == "Свободно" else day_info[5], "Свободно" if msg == "15:00" and day_info[6] == "?" else "?" if msg == "15:00" and day_info[6] == "Свободно" else day_info[6], "Свободно" if msg == "18:00" and day_info[7] == "?" else "?" if msg == "18:00" and day_info[7] == "Свободно" else day_info[7])); db.commit()
                                elif day_info != None and msg in ("9:00","12:00","15:00","18:00") and past_time_bool == True:
                                    cursor.execute(f"UPDATE day_record SET TIME900=?, TIME1200=?, TIME1500=?, TIME1800=? WHERE MASTER_ID=? AND DAY=? AND MONTH=? AND YEAR=?",(day_info[4] if day_info[4] not in ("?", "Свободно") else "Свободно" if msg == "9:00" and day_info[4] == "?" else "?" if msg == "9:00" and day_info[4] == "Свободно" else day_info[4], day_info[5] if day_info[5] not in ("?", "Свободно") else "Свободно" if msg == "12:00" and day_info[5] == "?" else "?" if msg == "12:00" and day_info[5] == "Свободно" else day_info[5], day_info[6] if day_info[6] not in ("?", "Свободно") else "Свободно" if msg == "15:00" and day_info[6] == "?" else "?" if msg == "15:00" and day_info[6] == "Свободно" else day_info[6], day_info[7] if day_info[7] not in ("?", "Свободно") else "Свободно" if msg == "18:00" and day_info[7] == "?" else "?" if msg == "18:00" and day_info[7] == "Свободно" else day_info[7], user_id, day, masters_info[7], masters_info[8])); db.commit()
                                else:
                                    Bot.send_message(user_id, "Вы ввели запись, которая прошла!", keyboard.get_empty_keyboard())
                                cursor.execute(f"SELECT * FROM day_record WHERE MASTER_ID=? AND DAY=? AND MONTH=? AND YEAR=?",(user_id,day,masters_info[7],masters_info[8]))
                                day_info = cursor.fetchone()
                                keyboard.add_button("Запись прошла" if past_time_bool == False else "9:00", VkKeyboardColor.NEGATIVE if day_info[4] == "?" or past_time_bool == False else VkKeyboardColor.POSITIVE)
                                keyboard.add_button("Запись прошла" if past_time_bool == False else "12:00", VkKeyboardColor.NEGATIVE if day_info[5] == "?" or past_time_bool == False else VkKeyboardColor.POSITIVE)
                                keyboard.add_line()
                                keyboard.add_button("Запись прошла" if past_time_bool == False else "15:00", VkKeyboardColor.NEGATIVE if day_info[6] == "?" or past_time_bool == False else VkKeyboardColor.POSITIVE)
                                keyboard.add_button("Запись прошла" if past_time_bool == False else "18:00", VkKeyboardColor.NEGATIVE if day_info[7] == "?" or past_time_bool == False else VkKeyboardColor.POSITIVE)
                                if day_info[4] == "?" and day_info[5] == "?" and day_info[6] == "?" and day_info[7] == "?":
                                    keyboard.add_line()
                                    keyboard.add_button("Выбрать всё", VkKeyboardColor.POSITIVE)
                                elif day_info[4] == "Свободно" and day_info[5] == "Свободно" and day_info[6] == "Свободно" and day_info[7] == "Свободно":
                                    keyboard.add_line()
                                    keyboard.add_button("Убрать всё", VkKeyboardColor.POSITIVE)
                                keyboard.add_line()
                                keyboard.add_button("Вернуться", VkKeyboardColor.POSITIVE)
                                Bot.send_message(user_id,"Выберите в какое время у вас будут записи!",keyboard.get_keyboard())
                                if day_info[4] == "?" and day_info[5] == "?" and day_info[6] == "?" and day_info[7] == "?":
                                    cursor.execute(f"DELETE FROM day_record WHERE MASTER_ID=? AND DAY=? AND MONTH=? AND YEAR=?",(user_id,day,masters_info[7],masters_info[8])); db.commit()
                            else:
                                Bot.send_message(user_id,'Вы ввели некоректный день!\n(Ошибка 100)',None)
                        
                        else:
                            Bot.send_message(user_id,'Такого ответа нет\n(Ошибка 100)',None)
        except:
            BOT()
BOT()
