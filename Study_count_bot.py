import telebot
import sqlite3
from telebot import types
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import datetime
from datetime import datetime, timedelta, date
import os
import schedule
import threading
import time

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()

    #table for name and user's telegram_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            name TEXT
        )
    '''
    )
    #table for user's subjects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_name TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
'''
    )
    # table for study hours
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_records(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id INTEGER,
            hours_studied REAL,
            study_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
    ''')
    conn.commit()

init_db()

#remove_markup = types.ReplyKeyboardRemove()

# dic for saving name temporary
user_state={}
#first I should manage keys in the bot
#main menu
def send_main_menu(chat_id):
    markup=types.ReplyKeyboardMarkup()#resize_keyboard=True)
    markup.add("➕ Add new subject", "📋 List of my subjects")
    markup.add("📆 Enter hours of study", "📊 Progress chart")
    markup.add("❌Delete a subject")
    bot.send_message(chat_id, "Back to main menu:", reply_markup=markup)

# addind date to date of the users table to remove inactive users data from database
'''
def update_last_active(tel_id):
    today = date.today()
    cursor.execute("UPDATE users SET last_active = ? WHERE telegram_id = ?", (today, tel_id))
    conn.commit()
'''
# second stage, getting name and id of the user and save it to
# getting telegram id and name of user
@bot.message_handler(commands=['start'])
def send_welcome(message):
    #update_last_active(message.from_user.id)
    tel_id=message.from_user.id
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (tel_id,))
    user=cursor.fetchone()

    if user:
        user_id=user[0]
        # handle subject selection
        cursor.execute("SELECT * FROM subjects WHERE user_id = ?", (user_id,))
        subjects = cursor.fetchall()
        
        if subjects:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("➕ Add new subject", "📋 List of my subjects")
            markup.add("📆 Enter hours of study", "📊 Progress chart")
            markup.add("❌Delete a subject")
            bot.send_message(message.chat.id, f"Hi {user[2]}! Welcome 😊\n You have these subjects:\n" +
                             "\n".join(f"- {s[2]}" for s in subjects) +
                             "\n\n If you want to add a new subject, please use the menu.", reply_markup=markup)
            user_state.pop(tel_id, None)
            
        else:
            bot.reply_to(message, f"Hi {user[2]}! Welcome 😊\n Please enter the subjects you want to focus. Please separate names by comma \',\'.")
            user_state[tel_id] = {'state': 'awaiting_subjects'}
              
    else:
        bot.reply_to(message,"Hi \n Please enter your name")
        # change user state to waiting for her or his name
        user_state[tel_id]={'state':'awaiting_name'}

# saving user name and id in database
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id, {}).get('state') == 'awaiting_name')
def get_name(mes):
    #update_last_active(mes.from_user.id)
    tel_id=mes.from_user.id
    name=mes.text.strip()
    
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (telegram_id,name) VALUES (? , ?)",(tel_id,name))
    conn.commit()
    
    bot.reply_to(mes, f"Welcome {name} \n Please enter the subjects you want to focus. Please separate names by comma \',\'")
    # change user state to waiting for her or his subjects
    user_state[tel_id] = {'state': 'awaiting_subjects'}

# now we get the name and id of the user
# third stage is to see we want to see what subjects the user would like to study
# create a hendler to react after waiting for subjects
@bot.message_handler(func=lambda s: user_state.get(s.from_user.id, {}).get('state')=='awaiting_subjects')
def get_sunject(mes):
    #update_last_active(mes.from_user.id)
    tel_id= mes.from_user.id
    sub = mes.text.strip()
    
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id=?",(tel_id,))
    user_row=cursor.fetchone()
    # check if the user is in the list
    if not user_row:
        bot.reply_to(mes,f"Error! User is not found. Please use /start To enter your name.")
        user_state.pop(tel_id,None)
        return
    # if so we save subjects in a list
    user_id=user_row[0]
    subject=[s.strip() for s in sub.split(",") if s.strip()]
    # saving subjects in database
    for s in subject:
        cursor.execute("INSERT INTO subjects (user_id,subject_name) VALUES ( ?, ?)",(user_id,s))
    conn.commit()
    
    bot.reply_to(mes,f"✅ The follwoing subjects are recorded \n-"+"\n-".join(subject))
    bot.send_message(mes.chat.id,f"Use menu to record and view your progress.")
    send_main_menu(mes.chat.id)
    #change user state for next level
    #user_state[tel_id] = "awaiting_hours"
#########################################################################3
# handling keys
###########################################################################333
# first handling ➕ Add new subject
@bot.message_handler(func=lambda m: m.text=="➕ Add new subject")
def new_subject(mes):
    #update_last_active(mes.from_user.id)
    tel_id=mes.from_user.id
    user_state[tel_id]={'state':'waiting_new_subject'}
    bot.send_message(mes.chat.id,f"Please separate the names you want to enter by comma \',\'")

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id, {}).get('state')=="waiting_new_subject")
def save_new_subjects(mes):
    #update_last_active(mes.from_user.id)
    tel_id=mes.from_user.id
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id=?",(tel_id,))
    row=cursor.fetchone()
    
    if not row:
        bot.send_message(mes,f"Error! User is not found. Please use /start To enter your name.")
        return
    
    user_id=row[0]
    text_normalized = mes.text.replace('،', ',')
    subject=[s.strip() for s in text_normalized.split(",") if s.strip()]
    for s in subject:
        cursor.execute("INSERT INTO subjects (user_id,subject_name) VALUES ( ?, ?)",(user_id,s))
    conn.commit()
    
    bot.reply_to(mes,f"✅ The follwoing subjects are recorded \n-"+"\n-".join(subject))
    bot.send_message(mes.chat.id,f"Use menu to record and view your progress.")
    
    user_state.pop(tel_id, None)
    #user_state[tel_id] = {'state': 'waiting_new_subject'}
    
####################################################################################3
# handeling "📋 List of my subjects"
###################################################################################3
@bot.message_handler(func=lambda m: m.text=="📋 List of my subjects")
def all_subjects(mes):
    #update_last_active(mes.from_user.id)
    tel_id=mes.from_user.id
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id=?",(tel_id,))
    row=cursor.fetchone()
    
    if not row:
        bot.send_message(mes.chat.id,f"Error! User is not found. Please use /start To enter your name.")
        return
    user_id=row[0]
    cursor.execute("SELECT subject_name FROM subjects WHERE user_id=?",(user_id,))
    subject=cursor.fetchall()
    
    if not subject:
        bot.send_message(mes,f"You have not entered any subjects")
    else:
        sub_list="\n-".join(f"{s[0]}" for s in subject)
        bot.send_message(mes.chat.id,f"📚 List of your subjects:\n{sub_list}")

###########################################################################3
# handler for 📆 Enter hours of study
##########################################################################33
@bot.message_handler(func=lambda m: m.text=="📆 Enter hours of study")
def choos_subject(mes):
    #update_last_active(mes.from_user.id)
    tel_id = mes.from_user.id
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (tel_id,))
    row = cursor.fetchone()
    
    if not row:
        bot.send_message(mes.chat.id, f"Error! User is not found. Please use /start To enter your name.")
        return
    user_id = row[0]
    cursor.execute("SELECT id, subject_name FROM subjects WHERE user_id=?", (user_id,))
    subjects_list = cursor.fetchall()
    
    if not subjects_list:
        bot.send_message(mes.chat.id, f"You have not entered any subjects.")
        return
    
    #keyboard for each subject
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for s in subjects_list:
        markup.add(s[1])
    markup.add("🔙 Back to main menu")
    
    user_state[tel_id] = {'state': 'awaiting_hours_subject_selection', 'user_id': user_id}
    bot.send_message(mes.chat.id, "Please choose or enter one subject:", reply_markup=markup)
    

# getting and saving hours for each subject (should be for subject selection)
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id, {}).get('state') == 'awaiting_hours_subject_selection') 
def get_hours_subject_selection(mes):
    #update_last_active(mes.from_user.id)
    tel_id = mes.from_user.id
    selected_subject = mes.text.strip()

    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()

    if selected_subject == "🔙 Back to main menu":
        send_main_menu(mes.chat.id)
        user_state.pop(tel_id, None)
        return

    user_id = user_state[tel_id]['user_id']
    cursor.execute("SELECT id FROM subjects WHERE user_id = ? AND subject_name = ?", (user_id, selected_subject))
    sub_row = cursor.fetchone()

    if not sub_row:
        bot.send_message(mes.chat.id, "Subject not found, please enter subject or choose from menu.")
        return

    subject_id = sub_row[0]
    user_state[tel_id] = {'state': 'awaiting_hours_value', 'subject_id': subject_id, 'user_id': user_id, 'subject_name': selected_subject}
    bot.send_message(mes.chat.id, f"How long have you studied {selected_subject} today? Enter a number. For example 1.5")


# NEW HANDLER: getting and saving hours value for selected subject
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id, {}).get('state') == 'awaiting_hours_value')
def save_hours(mes):
    #update_last_active(mes.from_user.id)
    tel_id = mes.from_user.id
    hours_text = mes.text.strip()
    
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()

    persian_to_english_digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    hours_text = hours_text.translate(persian_to_english_digits)

    try:
        hours_studied = float(hours_text)
        if hours_studied < 0:
            raise ValueError("Hours must be positive")
    except ValueError:
        bot.send_message(mes.chat.id, "Invalid value. Please enter a positive number. If you have not studied this subject, please enter 0 as value.")
        return

    subject_id = user_state[tel_id]['subject_id']
    user_id = user_state[tel_id]['user_id']
    subject_name = user_state[tel_id]['subject_name']
    study_date = date.today().isoformat() 

    cursor.execute("INSERT INTO study_records (user_id, subject_id, hours_studied, study_date) VALUES (?, ?, ?, ?)",
                   (user_id, subject_id, hours_studied, study_date))
    conn.commit()

    bot.send_message(mes.chat.id, f"✅ {hours_studied} hours is recorded for «{subject_name}»  in {study_date}.")
    
    # After saving, return to awaiting subject selection to allow more inputs
    choos_subject(mes)
    

# back key handler
@bot.message_handler(func=lambda m: m.text == "🔙 Back to main menu")
def back_to_main(mes):
    #update_last_active(mes.from_user.id)
    send_main_menu(mes.chat.id)
    user_state.pop(mes.from_user.id, None)
    
    
# deleting subject from the list in subject_records
@bot.message_handler(func=lambda m: m.text=="❌Delete a subject")
def del_mess_1(mes):
    #update_last_active(mes.from_user.id)
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id=mes.from_user.id
    
    cursor.execute("SELECT id FROM users WHERE telegram_id=?", (tel_id,))
    row=cursor.fetchone()
    if not row:
        bot.send_message(mes.chat.id,f"Error: user not found. Please use /start to enter your name.")
        return
    user_id=row[0]
    cursor.execute("SELECT subject_name FROM subjects WHERE user_id=?",(user_id,))
    sub_row=cursor.fetchall()
    if not sub_row:
        bot.send_message(mes.chat.id,"You have noo subject to delete.")
    sub_list=sub_row[0]
    
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    for sub in sub_row:
        markup.add(f"📕 {sub[0]}")
    markup.add("🔙 Back to main menu")
    user_state[tel_id] = {'state': 'awaiting_subject_to_delete', 'user_id': user_id}
    bot.send_message(mes.chat.id,"Choose the subject you want to remove from the list",reply_markup=markup)

# waiting for subject to delete
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id,{}).get('state')=="awaiting_subject_to_delete")
def del_mes2(mes):
    #update_last_active(mes.from_user.id)
    tel_id = mes.from_user.id
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    selected_subject_with_prefix=mes.text.strip() 
    if selected_subject_with_prefix.startswith("📕 "):
        selected_subject = selected_subject_with_prefix.replace("📕 ", "").strip()
    else:
        selected_subject = selected_subject_with_prefix.strip()

    if selected_subject == "🔙 Back to main menu":
        send_main_menu(mes.chat.id)
        user_state.pop(tel_id, None)
        return

    user_id = user_state[tel_id]['user_id']

    sub_row = cursor.execute("SELECT id FROM subjects WHERE user_id = ? AND subject_name = ?", (user_id, selected_subject)).fetchone()

    if not sub_row:
        bot.send_message(mes.chat.id, "Subject is not found. Please choose the correct name or choose from menu.")
        return
    
    subject_id_to_delete = sub_row[0]
    
    user_state[tel_id]['state'] = 'awaiting_delete_confirmation'
    user_state[tel_id]['subject_id_to_delete'] = subject_id_to_delete
    user_state[tel_id]['subject_name_to_delete'] = selected_subject
    
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Yes","🔙 Back to main menu")
    
    bot.send_message(mes.chat.id,f"Do you want to remove {subject_id_to_delete} from your list? All information of this subject will be removed.",reply_markup=markup)
    

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id, {}).get('state') == 'awaiting_delete_confirmation')
def del_final(mes):
    #update_last_active(mes.from_user.id)
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id
    user_data = user_state.get(tel_id, {})
    user_id = user_data.get('user_id')
    subject_id_to_delete = user_data.get('subject_id_to_delete')
    subject_name_to_delete = user_data.get('subject_name_to_delete')
    user_choice = mes.text.strip()

    if not user_id or not subject_id_to_delete or not subject_name_to_delete:
        bot.send_message(mes.chat.id, "Error in progressing. Please start over.", reply_markup=send_main_menu(mes.chat.id))
        user_state.pop(tel_id, None)
        return
    
    if user_choice == "Yes":
        try:
            # deleting subject's records in study_records
            cursor.execute("DELETE FROM study_records WHERE subject_id = ?", (subject_id_to_delete,))
            # deleting subject in subjects table
            cursor.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (subject_id_to_delete, user_id))
            conn.commit()
            bot.send_message(mes.chat.id, f"✅ «{subject_name_to_delete}» and all of it's data have been deleted.")
        except Exception as e:
            conn.rollback() 
            bot.send_message(mes.chat.id, f"❌ An error occured: {e}")
        
        send_main_menu(mes.chat.id)
        user_state.pop(tel_id, None)
    
    elif user_choice == "🔙 Back to main menu":
        send_main_menu(mes.chat.id)
        user_state.pop(tel_id, None) 
    
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Yes", "🔙 Back to main menu")
        bot.send_message(mes.chat.id, "Invalid answer. Please choose 'Yes' or '🔙 Back to main menue'.", reply_markup=markup)


# extracting graph from data
#daily, weekly, monthly, and general
# handler for "📊 Progress chart"
@bot.message_handler(func=lambda m: m.text == "📊 Progress chart")
def show_chart_options(message):
    #update_last_active(message.from_user.id)
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📅 Daily", "📈 Weekly")
    markup.add("📈 Monthly", "📊 General chart")
    markup.add("🔙 Back to main menu")
    bot.send_message(message.chat.id, "Select the chart type:", reply_markup=markup)

# daily
@bot.message_handler(func=lambda m: m.text == "📅 Daily")
def show_daily_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id

    cursor.execute("SELECT id FROM users WHERE telegram_id = ? ", (tel_id,))
    user_row = cursor.fetchone()
    if not user_row:
        bot.send_message(mes.chat.id, "User is not found. Pleade use /start to enter your name.")
        return

    user_id = user_row[0]
    today = date.today().isoformat()
    cursor.execute("SELECT id, subject_name FROM subjects WHERE user_id = ? LIMIT 1", (user_id,))
    first_subject_row = cursor.fetchone()

    if not first_subject_row:
        bot.send_message(mes.chat.id, "There is no subject to see the progress.")
        return

    subject_id = first_subject_row[0]
    subject_name = first_subject_row[1]


    cursor.execute('''
        SELECT subjects.subject_name, SUM(study_records.hours_studied)
        FROM study_records
        JOIN subjects ON study_records.subject_id = subjects.id
        WHERE study_records.user_id = ? AND study_records.study_date = ?
        GROUP BY subjects.subject_name
    ''', (user_id, today))
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(mes.chat.id, "No time is saved for today.")
        return

    subjects = [row[0] for row in rows]
    hours = [row[1] for row in rows]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(subjects, hours, color='skyblue')
    plt.title(f"Time for study ({today})", fontsize=14, y=1.05)
    plt.xlabel("Subject", fontsize=12)
    plt.ylabel("Time", fontsize=12)
    plt.xticks(rotation=45)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{yval:.1f}", ha='center', va='bottom')

    plt.tight_layout()
    filename = f"daily_chart_{tel_id}.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, 'rb') as photo:
        bot.send_photo(mes.chat.id, photo, caption="Daily progress graph.")

    os.remove(filename)



    cursor.execute('''
        SELECT study_date, SUM(hours_studied) FROM study_records
        WHERE user_id = ? AND subject_id = ?
        GROUP BY study_date ORDER BY study_date
    ''', (user_id, subject_id))
    rows = cursor.fetchall()
    
    dates = [r[0] for r in rows]
    values = [r[1] for r in rows]

# weekly progress
# general graph
@bot.message_handler(func=lambda m: m.text == "📈 Weekly")
def show_weekly_chart_menu(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    user_row = cursor.fetchone()
    
    if not user_row:
        bot.send_message(mes.chat.id, "User not found. Please use /start to enter your name.")
        return

    user_id = user_row[0]
    cursor.execute("SELECT subject_name FROM subjects WHERE user_id = ?", (user_id,))
    subject_rows = cursor.fetchall()

    if not subject_rows:
        bot.send_message(mes.chat.id, "No subject is recorded.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Weekly sum")
    for sub in subject_rows:
        markup.add(f"📗 {sub[0]}")
    markup.add("🔙 Back to main menu")
    bot.send_message(mes.chat.id, "Select the chart type:", reply_markup=markup)

# graph based on subjects
# sum of the subject hours
@bot.message_handler(func=lambda m: m.text == "📊 Weekly sum")
def show_total_weekly_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    row = cursor.fetchone()
    if not row:
        bot.send_message(mes.chat.id, "User not found.")
        return

    user_id = row[0]
    today = date.today()
    start_date = (today - timedelta(days=6)).isoformat()

    cursor.execute('''
        SELECT study_date, SUM(hours_studied)
        FROM study_records
        WHERE user_id = ? AND study_date >= ?
        GROUP BY study_date
        ORDER BY study_date
    ''', (user_id, start_date))
    data = cursor.fetchall()

    if not data:
        bot.send_message(mes.chat.id, "No time is recorded this week.")
        return

    dates = [row[0] for row in data]
    hours = [row[1] for row in data]

    plt.figure(figsize=(8,5))
    plt.plot(dates, hours, marker='o')
    plt.title("Study hours in the last 7 days.")
    plt.xlabel("Date")
    plt.ylabel("Hours of study")
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"weekly_total_{tel_id}.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, 'rb') as photo:
        bot.send_photo(mes.chat.id, photo)
    os.remove(filename)


@bot.message_handler(func=lambda m: m.text.startswith("📗 "))
def show_subject_monthly_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id=mes.from_user.id
    subject_name = mes.text.replace("📗", "").strip()

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    user_row = cursor.fetchone()
    if not user_row:
        bot.send_message(mes.chat.id, "User is not found.")
        return
    user_id = user_row[0]

    cursor.execute("SELECT id FROM subjects WHERE user_id = ? AND subject_name = ?", (user_id, subject_name))
    sub_row = cursor.fetchone()
    if not sub_row:
        bot.send_message(mes.chat.id, "Subject is not found.")
        return
    subject_id = sub_row[0]

    today = date.today()
    start_date = (today - timedelta(days=6)).isoformat()

    cursor.execute('''
        SELECT study_date, SUM(hours_studied)
        FROM study_records
        WHERE user_id = ? AND subject_id = ? AND study_date >= ?
        GROUP BY study_date
        ORDER BY study_date
    ''', (user_id, subject_id, start_date))
    data = cursor.fetchall()

    if not data:
        bot.send_message(mes.chat.id, f"No time is recorded for «{subject_name}».")
        return

    dates = [row[0] for row in data]
    hours = [row[1] for row in data]

    plt.figure(figsize=(10,6))
    plt.plot(dates, hours, marker='o')
    plt.title(f"Study hours for «{subject_name}» in last week.")
    plt.xlabel("Date")
    plt.ylabel("Hours of study")
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"monthly_{tel_id}_{subject_id}.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, 'rb') as photo:
        bot.send_photo(mes.chat.id, photo)
    os.remove(filename)


#####################################################################33
#############################################################################
# monthly progress
@bot.message_handler(func=lambda m: m.text == "📈 Monthly")
def handle_monthly_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    user_row = cursor.fetchone()
    
    if not user_row:
        bot.send_message(mes.chat.id, "User not found please use /start")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Monthly sum", "🔙 Back")
    
    user_id = user_row[0]
    cursor.execute("SELECT subject_name FROM subjects WHERE user_id = ?", (user_id,))
    subject_rows = cursor.fetchall()

    if not subject_rows:
        bot.send_message(mes.chat.id, "No subject is recorded.")
        return


    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Monthly sum")
    for sub in subject_rows:
        markup.add(f"📘 {sub[0]}")
    markup.add("🔙 Back to main menu")
    bot.send_message(mes.chat.id, "Select the chart type:", reply_markup=markup)


# graph based on subjects
# sum of the subject hours
@bot.message_handler(func=lambda m: m.text == "📊 Monthly sum")
def show_total_monthly_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    row = cursor.fetchone()
    if not row:
        bot.send_message(mes.chat.id, "User not found.")
        return

    user_id = row[0]
    today = date.today()
    start_date = (today - timedelta(days=29)).isoformat()

    cursor.execute('''
        SELECT study_date, SUM(hours_studied)
        FROM study_records
        WHERE user_id = ? AND study_date >= ?
        GROUP BY study_date
        ORDER BY study_date
    ''', (user_id, start_date))
    data = cursor.fetchall()

    if not data:
        bot.send_message(mes.chat.id, "No time is recorded this month.")
        return

    dates = [row[0] for row in data]
    hours = [row[1] for row in data]

    plt.figure(figsize=(10,6))
    plt.plot(dates, hours, marker='o')
    plt.title("Sum of study hours during last 30 days.")
    plt.xlabel("Date")
    plt.ylabel("Hours")
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"monthly_total_{tel_id}.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, 'rb') as photo:
        bot.send_photo(mes.chat.id, photo)
    os.remove(filename)


@bot.message_handler(func=lambda m: m.text.startswith("📘 "))
def show_subject_monthly_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id=mes.from_user.id
    subject_name = mes.text.replace("📘", "").strip()

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    user_row = cursor.fetchone()
    if not user_row:
        bot.send_message(mes.chat.id, "User not found.")
        return
    user_id = user_row[0]

    cursor.execute("SELECT id FROM subjects WHERE user_id = ? AND subject_name = ?", (user_id, subject_name))
    sub_row = cursor.fetchone()
    if not sub_row:
        bot.send_message(mes.chat.id, "No subject is found.")
        return
    subject_id = sub_row[0]

    today = date.today()
    start_date = (today - timedelta(days=29)).isoformat()

    cursor.execute('''
        SELECT study_date, SUM(hours_studied)
        FROM study_records
        WHERE user_id = ? AND subject_id = ? AND study_date >= ?
        GROUP BY study_date
        ORDER BY study_date
    ''', (user_id, subject_id, start_date))
    data = cursor.fetchall()

    if not data:
        bot.send_message(mes.chat.id, f"There is no hour for «{subject_name}» in this month.")
        return

    dates = [row[0] for row in data]
    hours = [row[1] for row in data]

    plt.figure(figsize=(10,6))
    plt.plot(dates, hours, marker='o')
    plt.title(f"Hours of study for «{subject_name}».")
    plt.xlabel("Date")
    plt.ylabel("Hour")
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"monthly_{tel_id}_{subject_id}.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, 'rb') as photo:
        bot.send_photo(mes.chat.id, photo)
    os.remove(filename)

############################################################################3
# general progress
@bot.message_handler(func=lambda m: m.text == "📊 General chart")
def general_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    user_row = cursor.fetchone()
    
    if not user_row:
        bot.send_message(mes.chat.id, "User not found please use /start")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 All subject chart", "🔙 Back")
    
    user_id = user_row[0]
    cursor.execute("SELECT subject_name FROM subjects WHERE user_id = ?", (user_id,))
    subject_rows = cursor.fetchall()

    if not subject_rows:
        bot.send_message(mes.chat.id, "No subject is entered.")
        return


    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 All subjects")
    for sub in subject_rows:
        markup.add(f"📙 {sub[0]}")
    markup.add("🔙 Back to main menu")
    bot.send_message(mes.chat.id, "Select the chart type:", reply_markup=markup)


# graph based on subjects
# sum of the subject hours
@bot.message_handler(func=lambda m: m.text == "📊 All subjects")
def show_total_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id = mes.from_user.id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    row = cursor.fetchone()
    if not row:
        bot.send_message(mes.chat.id, "User not found.")
        return

    user_id = row[0]
    
    today = date.today()
    cursor.execute('''
    SELECT MIN(study_date)
    FROM study_records
    WHERE user_id = ? 
    ''', (user_id,))
    start_date_row = cursor.fetchone()
    start_date = start_date_row[0]
    
    cursor.execute('''
        SELECT study_date, SUM(hours_studied)
        FROM study_records
        WHERE user_id = ? AND study_date >= ?
        GROUP BY study_date
        ORDER BY study_date
    ''', (user_id, start_date))
    data = cursor.fetchall()

    if not data:
        bot.send_message(mes.chat.id, "No time is recorded.")
        return

    dates = [row[0] for row in data]
    hours = [row[1] for row in data]

    plt.figure(figsize=(10,6))
    plt.plot(dates, hours, marker='o')
    plt.title("Total recorded hours.")
    plt.xlabel("Date")
    plt.ylabel("Hours of study")
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"general_{tel_id}.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, 'rb') as photo:
        bot.send_photo(mes.chat.id, photo)
    os.remove(filename)


@bot.message_handler(func=lambda m: m.text.startswith("📙 "))
def show_subject_total_chart(mes):
    conn = sqlite3.connect('study_bot.db')
    cursor = conn.cursor()
    tel_id=mes.from_user.id
    subject_name = mes.text.replace("📙 ", "").strip()

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (tel_id,))
    user_row = cursor.fetchone()
    if not user_row:
        bot.send_message(mes.chat.id, "User not found.")
        return
    user_id = user_row[0]

    cursor.execute("SELECT id FROM subjects WHERE user_id = ? AND subject_name = ?", (user_id, subject_name))
    sub_row = cursor.fetchone()
    if not sub_row:
        bot.send_message(mes.chat.id, "Subject not found.")
        return
    subject_id = sub_row[0]

    today = date.today()
    start_date = (today - timedelta(days=29)).isoformat()

    cursor.execute('''
        SELECT study_date, SUM(hours_studied)
        FROM study_records
        WHERE user_id = ? AND subject_id = ? AND study_date >= ?
        GROUP BY study_date
        ORDER BY study_date
    ''', (user_id, subject_id, start_date))
    data = cursor.fetchall()

    if not data:
        bot.send_message(mes.chat.id, f"No time is recorded for «{subject_name}».")
        return

    dates = [row[0] for row in data]
    hours = [row[1] for row in data]

    plt.figure(figsize=(10,6))
    plt.plot(dates, hours, marker='o')
    plt.title(f"Study hours for «{subject_name}»")
    plt.xlabel("Date")
    plt.ylabel("Hours of study")
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"general_{tel_id}_{subject_id}.png"
    plt.savefig(filename)
    plt.close()

    with open(filename, 'rb') as photo:
        bot.send_photo(mes.chat.id, photo)
    os.remove(filename)

print("Bot is processing ...")
bot.polling()

