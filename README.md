# Telegram Points Management Bot

- Keeps track of points using relational database management system through telegram bot
- Utilises Telepot library to create a webhook using Flask
- MySQL database used to store and process data querying, inserting, and updating through telegram commands via SQLAlchemy
- Developed using Python, hosted on PythonAnywhere

Test on: https://t.me/DingsTestBot

# Available Commands:
- /start:
  - Initialises the bot and creates user_id data in database
  - To use, "/start"
  - Note: user automatically joins room "0" with user_id as nickname
- /pay: 
  - Pays another user in the same room x tokens 
  - To use, "/pay NICKNAME TOKEN_AMOUNT", where TOKEN_AMOUNT is a positive integer
  - e.g. "/pay arnold 5"
  - Note: both sender and recipient will be notified of the transaction
- /join:
  - Joins a room and resets your points to 0
  - To use, "/join ROOM_ID NICKNAME confirm", where ROOM_ID is any text or number
  - e.g. "/join 21122022 arnold confirm"
  - Note: your previous points and room joined will be lost
- /room:
  - Gets information about ROOM_ID and the users in the same room with their respective points
  - To use, "/room"
- /setpoints:
  - Manually sets your own points to a specified amount
  - To use, "/setpoints AMOUNT", where AMOUNT is your desired amount
  - e.g. "/setpoints 30"
  - Note: all users in the same room will be notified of your previous and new points
