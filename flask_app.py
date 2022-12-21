from flask import Flask, request
import telepot
import urllib3
import sqlalchemy as db

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

secret = "REDACTED"
bot = telepot.Bot("REDACTED")
bot.setWebhook("https://ldinghan.pythonanywhere.com/{}".format(secret), max_connections=10)

app = Flask(__name__)

engine = db.create_engine("REDACTED", pool_recycle=295)
metadata = db.MetaData()
connection = engine.connect()
pointsTable = db.Table('points', metadata, autoload=True, autoload_with=engine)




@app.route('/{}'.format(secret), methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        user_id = update["message"]["from"]["id"]
        if "text" in update["message"]:
            text = update["message"]["text"]

#start command
            if text == "/start":
                query = db.delete(pointsTable).where(pointsTable.columns.id == user_id)
                ResultProxy = connection.execute(query)
                query = db.insert(pointsTable).values(id=user_id, points=0, room="0", nickname=str(user_id))
                ResultProxy = connection.execute(query)
                bot.sendMessage(chat_id, 'successfully initialised bot')


#pay command
            elif text[:4] == "/pay":
                command = text.strip('').split(' ')
                if len(command) == 3:
                    recipient = str(command[1]).lower()
                    amount = int(command[2])
                    if amount <= 0:
                        bot.sendMessage(chat_id, "please try again with a positive number")
                    else:
                        sender_info_query = db.select([pointsTable]).where(pointsTable.columns.id == user_id)
                        sender_info = connection.execute(sender_info_query).fetchall()[0]
                        sender_amount = sender_info[1]
                        sender_room = sender_info[2]
                        sender_nickname = sender_info[3]
                        if sender_nickname == recipient:
                            bot.sendMessage(chat_id, "please send tokens to someone else instead")
                        else:
                            recipient_info_query = db.select([pointsTable]).where(db.and_(pointsTable.columns.nickname == recipient, pointsTable.columns.room == sender_room))
                            recipient_info = connection.execute(recipient_info_query).fetchall()

                            if not recipient_info:
                                bot.sendMessage(chat_id, "user '{}' is not in your room {}".format(recipient, sender_room))
                            else:
                                recipient_id, recipient_amount = recipient_info[0][0], recipient_info[0][1]

                                sender_new_amount = sender_amount - amount
                                recipient_new_amount = recipient_amount + amount




                                try:
                                    bot.sendMessage(recipient_id, "You received {} tokens from '{}'. You now have {} tokens.".format(amount, sender_nickname, recipient_new_amount))
                                    bot.sendMessage(chat_id, "You gave '{}' {} tokens. You now have {} tokens.".format(recipient, amount, sender_new_amount))
                                    send_query = db.update(pointsTable).where(pointsTable.columns.id == user_id).values(points=sender_new_amount)
                                    send_ResultProxy = connection.execute(send_query)
                                    receive_query = db.update(pointsTable).where(pointsTable.columns.nickname == recipient).values(points=recipient_new_amount)
                                    receive_ResultProxy = connection.execute(receive_query)
                                except:
                                    bot.sendMessage(chat_id, "Error occurred, recipient needs to start the bot")
                else:
                    bot.sendMessage(chat_id, "Please use the correct format")



#join command
            elif text[:5] == "/join":
                command = text.strip('').split(' ')
                if len(command) == 4 and command[3] == "confirm":
                    join_room_id = str(command[1])
                    nickname = str(command[2]).lower()
                    query = db.delete(pointsTable).where(pointsTable.columns.id == user_id)
                    ResultProxy = connection.execute(query)
                    query = db.insert(pointsTable).values(id=user_id, points=0, room=join_room_id, nickname=nickname)
                    ResultProxy = connection.execute(query)
                    bot.sendMessage(chat_id, 'successfully joined room {} as "{}"'.format(join_room_id, nickname))
                else:
                    bot.sendMessage(chat_id, "Please use the correct format -- '/join ROOM_ID NICKNAME confirm'")



#room command
            elif text == "/room":
                sender_info_query = db.select([pointsTable]).where(pointsTable.columns.id == user_id)
                sender_room = connection.execute(sender_info_query).fetchall()[0][2]

                room_users_query = db.select([pointsTable]).where(pointsTable.columns.room == sender_room)
                room_users = connection.execute(room_users_query).fetchall()
                room_users_string = ''
                for user in room_users:
                    u_name = user[3]
                    u_amount = user[1]
                    room_users_string += "{} ({} tokens)\n".format(u_name, u_amount)
                bot.sendMessage(chat_id, "ROOM: {}\n{}".format(sender_room, room_users_string))


#setpoints command
            elif text[:10] == "/setpoints":
                command = text.strip('').split(' ')
                if len(command) == 2:
                    new_points = command[1]
                    if not new_points.isnumeric():
                        bot.sendMessage(chat_id, "please use numbers only")
                    else:
                        new_points = int(new_points)
                        sender_info_query = db.select([pointsTable]).where(pointsTable.columns.id == user_id)
                        sender_info = connection.execute(sender_info_query).fetchall()[0]
                        sender_room, sender_amount, sender_nickname = sender_info[2], sender_info[1], sender_info[3]

                        update_query = db.update(pointsTable).where(pointsTable.columns.id == user_id).values(points=new_points)
                        send_ResultProxy = connection.execute(update_query)
                        room_users_query = db.select([pointsTable]).where(pointsTable.columns.room == sender_room)
                        room_users = connection.execute(room_users_query).fetchall()

                        for user in room_users:
                            u_id = user[0]
                            bot.sendMessage(u_id, "'{}' has used setpoints command and now has {} tokens instead of {} tokens.".format(sender_nickname, new_points, sender_amount))
                else:
                    bot.sendMessage(chat_id, "Please use the correct format -- '/setpoints NEW_POINTS'")



#help command
            elif text == "/help":
                bot.sendMessage(chat_id, '/pay: Pays another user in the same room x tokens\nTo use, "/pay NICKNAME TOKEN_AMOUNT", where TOKEN_AMOUNT is a positive integer\ne.g. "/pay arnold 5"\nNote: both sender and recipient will be notified of the transaction\n\n/join:\nJoins a room and resets your points to 0\nTo use, "/join ROOM_ID NICKNAME confirm", where ROOM_ID is an integer\ne.g. "/join 21122022 arnold confirm"\nNote: your previous points and room joined will be lost\n\n/room:\nGets information about ROOM_ID and the users in the same room with their respective points\nTo use, "/room"\n\n/setpoints:\nManually sets your own points to a specified amount\nTo use, "/setpoints AMOUNT", where AMOUNT is your desired amount\ne.g. "/setpoints 30"\nNote: all users in the same room will be notified of your previous and new points')


        else:
            bot.sendMessage(chat_id, "sorry, I didn't understand that kind of message")
    return "OK"
