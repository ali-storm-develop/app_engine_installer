#!/usr/bin/env python
#-*-coding:utf8;-*-

project_name = "project_nomi" 
import fileworker as fv
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import logging
import threading
import requests
import json
from google.appengine.ext import ndb
import time
from time import sleep
from datetime import datetime, timedelta
import telebot
from telebot import types
import os
import random
import webapp2
import urllib
import urllib2
API_TOKEN = "replace_me_with_token"

def admin(user_id):
    Admins = [88505037, 8768957689476] #Adminlar id si ro'yhati. Bu yerga o'zingizni id raqamingizni yozing. Tel raqam emas, telegramdagi id raqam
    return user_id in Admins

bot = telebot.TeleBot(API_TOKEN, threaded=False)
bot_id = int(API_TOKEN.split(":")[0])
webhook_key = (API_TOKEN.split(":")[1])[:-20]

def _print(a):
    logging.info(str(a))
    return

def get_date():
    return (datetime.now() + timedelta(hours=5)).strftime('%Y-%m-%d')

def get_datetime():
    return (datetime.now() + timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')

def md(txt):
    return(txt.replace("_","\_").replace("*","\*").replace("`","\`").replace("[","\["))

class Knowledge(ndb.Model):  
    answer = ndb.StringProperty(repeated=True)

def get_answer(text):
    s = Knowledge.get_by_id(text.decode('utf-8'))
    if s:
        return(random.choice(s.answer))

def get_all_answers(text):
    s = Knowledge.get_by_id(text.decode('utf-8'))
    if s: 
        return(s.answer)
    return None
    
def add_answer(text, answer):
    text = text.decode('utf-8')
    answers = get_all_answers(text)
    if answers == None:
        answers = []
    answers.append(answer.decode('utf-8'))
    s = Knowledge.get_or_insert(text.decode('utf-8'))
    s.answer = answers
    s.put()
    
def update_answer(question, answers_list):
    s = Knowledge.get_or_insert(question.decode('utf-8'))
    s.answer = answers_list
    s.put()
    
def broadcast(data):
    subscribe = fv.open('./enabled_list.uzsdb', 'r').read().split('\n')
    subscribe_count = len(subscribe)
    yi = 0
    i = 0
    while i < subscribe_count:
        try:
            bot.send_message(int(subscribe[i]), data)
            yi = yi + 1
        except Exception as e:
            _print("Foydalanuvchi " + str(subscribe[i]) + " ga hat yetib bormadi")
        i = i + 1
    return(yi)
        
def getEnabled(chatid):
    try:
        fv.open('./enabled_list.uzsdb', 'r').read().split('\n').index(str(chatid))
        return True
    except:
        return False
    
def setEnabled(chatid, enable=True):
    enable_list = fv.open('./enabled_list.uzsdb', 'r').read().split('\n')
    if enable:
        enable_list.append(str(chatid))
    else:
        try:
            enable_list.remove(str(chatid))
        except:
            'ok'
    fv.open('./enabled_list.uzsdb', 'w').write('\n'.join(enable_list))
    return

def next_step(chatid, stepstr):
    fv.open('./users/info_' + str(chatid) + '.uzsdb', 'w').write(stepstr)
    
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data.startswith("del|"):
            try:
                data = call.data.replace("del|", "").split('|')
                question = data[0]
                answer = int(data[1])-1
                answers_list = get_all_answers(question)
                old_answer = answers_list[answer]
                answers_list.pop(answer)
                update_answer(question, answers_list)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Savol: " + str(question) + "\n⛔️Javob: " + str(old_answer))
            except Exception as e:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Hato:\n" + str(e))
        elif call.data.startswith("del_question|"):
            try:
                question = call.data.replace("del_question|", "")
                update_answer(question, [])
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="⛔️Savol: " + str(question))
            except Exception as e:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Hato:\n" + str(e))


@bot.message_handler(func=lambda message: True, content_types=['new_chat_member'])
def new_chat_member(message):
    chat_id = message.chat.id #gruppani telegramdagi id si
    try:
        user_id = message.new_chat_member.id
    except:
        user_id = message.from_user.id
    #user_id - gruppaga qo'shilgan odam id si. Shunchaki ma'lumot uchun
    if message.new_chat_member.first_name:
        first_name=message.new_chat_member.first_name
    else:
        first_name=message.from_user.first_name
    #first_name - foydalanuvchi ismi. Shunchaki ma'lumot uchun 
    username = "None"
    if message.new_chat_member.username:
        username = message.new_chat_member.username
    
    if not(username.lower().endswith('bot')):
        bot.send_message(chat_id, "Salom, " + first_name)

@bot.message_handler(func=lambda message: True)
def main(message):
    first_name = message.from_user.first_name.decode("utf-8") #hat yozgan odam ismi
    user_id = message.from_user.id #hat yozgan odam id si
    chat_id = message.chat.id #chat id si. Agar gruppa bo'sa chat_id<0, agar lichka bo'sa user_id bilan bir xil
    text = str(message.text).decode("utf-8") #yozilfan gat matni
    if len(text)>0: #agar text uzunligi 0 dan kotta bo'sa (hatolarni oldini olish uchun
        try:
            if chat_id>0: #lichka bo'sa
                step = fv.open('./users/info_' + str(chat_id) + '.uzsdb', 'r').read()
            else: #gruppa bo'sa
                step = "group_chat"
        except:
            step = 'none'
        
        def start():
            if getEnabled(chat_id): #agar oldin yozgan bo'sa
                bot.send_message(chat_id, "سلام کاربر جوووووون  😐")
                next_step(chat_id, 'main')
            else:
                setEnabled(chat_id)
                bot.send_message(chat_id, "*Salom, siz bu botga a'zo bo'ldingiz*", parse_mode="Markdown", disable_web_page_preview=True) #so'zni to'g'illavolasila
                try:
                    history = fv.open('./history.uzsdb', 'r').read().split('|')
                except:
                    history = ["0"]
                next_step(chat_id, 'main')
                if history.count(str(chat_id)) == 0:
                    history.append(str(chat_id))
                    fv.open('./history.uzsdb', 'w').write('|'.join(history))
            return
        
        if admin(chat_id): #agar admin yozsa
            if text.startswith("/send_id_"):
                try:
                    bot.send_message(text.replace("/send_id_","").split(" ",1)[0], text.replace("/send_id_","").split(" ",1)[1], parse_mode="Markdown")
                    bot.send_message(chat_id, "Etip qo'ydim )")
                except Exception as ex:
                    bot.send_message(chat_id, "Hat yetip bormadi. Hato: " + str(ex))
            
            if text.startswith('/learn '):
                try:
                    bot.send_message(chat_id, "Buyruqlarni o'rganish uchun /learn_help")
                    data = text.split(' ',1)[1]
                    if '|' in data:
                        savol = data.split('|',1)[0]
                        answer = data.split("|",1)[1]
                        if len(savol)<20:
                            add_answer(savol, answer)
                            bot.send_message(chat_id, "O'rganib oldim.", reply_to_message_id = message.message_id)
                        else:
                            bot.send_message(chat_id, "Savol juda uzun", reply_to_message_id = message.message_id)
                    else:
                        bot.send_message(chat_id, "*/learn savol|javob* ko'rinishida yozing!", parse_mode="Markdown")
                except Exception as ex:
                    bot.send_message(chat_id, "*/learn savol|javob* ko'rinishida yozing!\n" + str(ex), parse_mode="Markdown")

            elif text.startswith('/javob '):
                try:
                    data = text.split(' ',1)[1]
                    answers = get_all_answers(data)
                    if answers:
                        keyboard = types.InlineKeyboardMarkup()
                        i = 1
                        text = ''
                        callback = types.InlineKeyboardButton(text = "Savolni o'chirish⛔️" , callback_data="del_question|" + data)
                        keyboard.add(callback)
                        for answer in answers:
                            if len(answers) > 10:
                                if len(answer) > 70:
                                    text = text + "\n*" + str(i) + "*- `" + str(answer)[:70] + "...`"
                                else:
                                    text = text + "\n*" + str(i) + "*- `" + str(answer) + "`"
                            else:
                                text = text + "\n*" + str(i) + "*- `" + str(answer) + "`"
                            callback = types.InlineKeyboardButton(text = str(i) + " - ni o'chirish⛔️" , callback_data="del|" + data + "|" + str(i))
                            keyboard.add(callback)
                            i += 1
                        bot.send_message(chat_id, "*Savol*: `" + data + "`\n*Javoblar:* " + text, parse_mode="Markdown", reply_markup=keyboard)
                    else:
                        bot.send_message(chat_id, "Bunaqa so'zni bilmayman")
                except Exception as ex:
                    bot.send_message(chat_id, str(ex))

            elif text == "/learn_help":
                bot.send_message(chat_id, "Salom, siz bo'tga so'z o'rgatishiz uchun quyidagi shakilda buyruq bering: \n/learn So'z|javob \n misol uchun siz 'Salom' so'ziga 'Salom, ishla qale' deb javob berishni o'rgatmoxchi bo'lsangiz quyidagi buyruqni berasiz. \n/learn Salom|Salom, ishla qale?\nO'rgatilgan so'zla bazadan o'chirilishi hali qo'shilgani yo'q. Shuning uchun so'zlarni yaxshilap o'ylap qo'shing.")
                bot.send_message(chat_id, "Misol uchun agar menga 'kim man' dip yozsa, man uni otini yozishim kere bo'sa, quyidagicha buyruq berasiz: \n/learn kim man|Sizni telegramdagi ismingiz: __name__ \nta'ni ikkita '_' chizig'i name va yana ikkita __ chiziq. Bu boshqa so'zlaga aralaship ketmasligi uchun. Bundan tashqari, siz __id__ buyrug'iniyam ishlatishingiz mummin. Misol uchun:\n/learn /id|__id__\bBularni sinap ko'ring.")
                

        if text.startswith("/start"):
            start()
                
        
        elif step == "group_chat":
            if text=="salom" or text=="Salom" or text=="салом" or text=="Салом":
                Salom =["Salooom!",
                        "Salom, qalesiz",
                        "Tekinakan db salom bervurasizmi endi, qalesiz o'zi tinchmi! 😜",
                        "Va aleykum assalom bo'tam",
                        "Salom!"] #shu joyga hohlaganizzi yozin
                r_salom=random.choice(Salom)
                bot.reply_to(message, r_salom)
            
            elif text=="ok":
                bot.reply_to(message,"ok") #bu tomoni yana example
            elif text == "/markdown":
                bot.send_message(chat_id, "*BOLD*, _italic_, `fixedsys`, [giperssilka](https://telegram.me/uzstudio)", parse_mode="Markdown")
            
            
            elif text.startswith("/screen "):
                text = text.split(" ",1)[1]
                if text.startswith("http") and not " " in text:
                    try:
                        data = urllib2.urlopen("https://screenshotmachine.com/processor.php?urlparam=" + urllib.quote(text)).read()
                        data = data.replace(data[:(data.find("href='") + len("href='"))],"")
                        data = data[:data.find("'")]
                        data = "https://screenshotmachine.com/" + data
                        try:
                            bot.send_photo(chat_id, data, caption = '🌐 ' + text, reply_to_message_id = message.message_id)
                        except:
                            bot.send_message(chat_id, "[screenshot](" + str(data) + ") topilmadi", parse_mode="Markdown")
                    except:
                        _print(" ")
            
            
            else:
                if "-" in text or "+" in text or "^" in text or "*" in text or "/" in text or "!" in text or ":" in text or "sin" in text or "cos" in text:
                    exp = text
                    try:
                        data = urllib2.urlopen("http://api.mathjs.org/v1/?expr=" + urllib.quote(exp)).read()
                        bot.send_message(chat_id, str(data))
                    except Exception as ex:
                        logging.info(ex)
                
                if len(text)<20:
                    answer = get_answer(text)
                    if answer:
                        bot.send_message(chat_id, answer.replace('__name__', first_name).replace('__id__', str(message.from_user.id)), reply_to_message_id = message.message_id)
                    

        elif step=="none":
            start()
                    
        elif text == "/ping": #bot tezligini aniqlash uchun
            bot.send_chat_action(chat_id, 'typing')
            m = bot.send_message(chat_id, "pong")
            ping = time.time() - message.date
            bot.edit_message_text("ping=" + str(ping), chat_id=chat_id, message_id=m.message_id)
        
        elif text == "/about": #Agar foydalanuvchilarni hisoblash sistemasini 0 dan tuzsangiz, @UzStudio ni optashasiz mumkin
            chats = fv.open('./enabled_list.uzsdb', 'r').read().split('\n')
            group = 0
            for chat in chats:
                if chat.startswith('-'):
                    group += 1
            chats = len(chats) - group
            keyboard = types.InlineKeyboardMarkup()
            callback = types.InlineKeyboardButton(text="♻️Yangilash♻️", callback_data="about_yangilash")
            keyboard.add(callback)
            subscribe_about = '📈Bot foydalanuvchilari:\n👤*' + str(chats) + '* odamlar,\n👥*' + str(group) + '* guruxlar.\n🕵Hammasi bo\'lip: *' + str(chats+group) + '*\n'
            bot.send_message(chat_id, subscribe_about +"\n*" + get_datetime() + "*\n\n©`2015`-`2017` @UzStudio ™", parse_mode="markdown")

        elif step=="main": #Agar asosiy menyuda bo'lsa
            if text=="/command" or text == "command":
                bot.send_message(chat_id, "answer")
            
            elif text == "/help" or text == "Yordam⁉️": 
                bot.send_chat_action(chat_id, 'typing') #typing chiqarish
                bot.send_message(chat_id, "Salom, bu bot gruppalada va lichkada sal boshqacharoq gaplashadi. Bo't qilolidiganishlari:\n1) Misollar yechish. lichkamga har-hil misollar berib ko'ringlar. 2) Saytlarni screenshot qilish. gruppada buyruqga misol: /screen http://gruppala.ga/ lichkada shundo sayt urlsi yoziladi. \nBo't Admin o'rgatgan so'zlaniaym o'rgana oladi.") #davomini yozarsiz
            
            elif text.startswith("/echo"):
                try:
                    data = text.split(" ",1)[1]
                    bot.send_message(chat_id, data)
                except:
                    bot.send_message(chat_id, "/echo qanaqadir text")
                    
            else:
                if "-" in text or "+" in text or "^" in text or "*" in text or "/" in text or "!" in text or ":" in text:
                    exp = text
                    try:
                        data = urllib2.urlopen("http://api.mathjs.org/v1/?expr=" + urllib.quote(exp)).read()
                        bot.send_message(chat_id, str(data))
                    except Exception as ex:
                        logging.info(ex)
                if len(text)<20:
                    answer = get_answer(text)
                    if answer:
                        bot.send_message(chat_id, answer.replace('__name__', first_name).replace('__id__', str(message.from_user.id)))
                        
                if text.startswith("http") and not " " in text:
                    try:
                        data = urllib2.urlopen("https://screenshotmachine.com/processor.php?urlparam=" + urllib.quote(text)).read()
                        data = data.replace(data[:(data.find("href='") + len("href='"))],"")
                        data = data[:data.find("'")]
                        data = "https://screenshotmachine.com/" + data
                        try:
                            bot.send_photo(chat_id, data, caption = '🌐 ' + text, reply_to_message_id = message.message_id)
                        except:
                            bot.send_message(chat_id, "[screenshot](" + str(data) + ") topilmadi", parse_mode="Markdown")
                    except:
                        _print(" ")

    return


logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

# webserver index
class IndexHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("""<!DOCTYPE html>
<html lang="uz">
  <head>
    <meta charset="utf-8">
    <title>""" + project_name + """</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content=""" + project_name + """ " ning serveri">
    <meta name="author" content="UzStudio">
    <link rel="shortcut icon" href="/favicon.ico">
  </head>
  <body>
    <h1><a href="tg:reslove?domain=uzstudio">""" + project_name + """</a> ning serveri</h1>
  </body>
</html>""")
        return


# bu joyiga teymela!!! Eng optimal qilip yozib bo'lingan!
# Process webhook calls
class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        try:
            json_string = json.loads(self.request.body.decode("utf-8"))
            updates = [telebot.types.Update.de_json(json_string)]
            new_messages = []
            edited_new_messages = []
            new_channel_posts = []
            new_edited_channel_posts = []
            new_inline_querys = []
            new_chosen_inline_results = []
            new_callback_querys = []
            for update in updates:
                if update.message:
                    new_messages.append(update.message)
                if update.edited_message:
                    edited_new_messages.append(update.edited_message)
                if update.channel_post:
                    new_channel_posts.append(update.channel_post)
                if update.edited_channel_post:
                    new_edited_channel_posts.append(update.edited_channel_post)
                if update.inline_query:
                    new_inline_querys.append(update.inline_query)
                if update.chosen_inline_result:
                    new_chosen_inline_results.append(update.chosen_inline_result)
                if update.callback_query:
                    new_callback_querys.append(update.callback_query)
            logger.debug('Received {0} new updates'.format(len(updates)))
            if len(new_messages) > 0:
                bot.process_new_messages(new_messages)
            if len(edited_new_messages) > 0:
                bot.process_new_edited_messages(edited_new_messages)
            if len(new_channel_posts) > 0:
                bot.process_new_channel_posts(new_channel_posts)
            if len(new_edited_channel_posts) > 0:
                bot.process_new_edited_channel_posts(new_edited_channel_posts)
            if len(new_inline_querys) > 0:
                bot.process_new_inline_query(new_inline_querys)
            if len(new_chosen_inline_results) > 0:
                bot.process_new_chosen_inline_query(new_chosen_inline_results)
            if len(new_callback_querys) > 0:
                bot.process_new_callback_query(new_callback_querys)    
        except Exception as ex:
            logging.error(str(ex))
        self.response.write('{"ok": true}')
        return

class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        url = self.request.get("url")
        token = self.request.get("token")
        try:
            fv.open("./enabled_list.uzsdb","r").read()
        except:
            fv.open('./enabled_list.uzsdb',"w").write("0")

        try:
            fv.open("./history.uzsdb","r").read()
        except:
            fv.open('./history.uzsdb',"w").write("0")

        if not url:
            bot.set_webhook("https://" + project_name + ".appspot.com/" + webhook_key)
        elif token == API_TOKEN:
            bot.set_webhook(url)
        else:
            self.response.write("token noto'g'ri")
            return
        self.response.write("ok")
        return

app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/' + webhook_key, WebhookHandler),
], debug=True)



<?php 
$token = '865761048:AAG2_dWZ03VjLO5Atut2sYk5nkMJMfLjptU';

$json = file_get_contents('php://input');
$telegram = urldecode ($json);
$telegram = str_replace ('jason=','',$telegram);
$results = json_decode($telegram); 

$message = $results->message;
$chat = $message->chat;
$chat_id = $chat->id;
$fromuser = $message->from;
$user_id = $fromuser->id;
$username = $fromuser->username;

$text = $message->text;



$about = getMe($token);
$me = json_decode ($about);
$me = $me->result;
$me_username = $me->username;

$new_chat_member = $message->new_chat_member;
$new_chat_member_id = $new_chat_member->id;
$new_chat_member_first_name = $new_chat_member->first_name;
$new_chat_member_last_name = $new_chat_member->last_name;
$new_chat_member_username = $new_chat_member->username;
$groupname = $chat->title;
if ($new_chat_member_id != '') {
  if ($me_username != $new_chat_member_username) {
    $welcome_massage = 'سلام '.$new_chat_member_first_name.' '. $new_chat_member_last_name.' عزیز'.chr(10).'به گروه '.$groupname.' خوش آمدید'.chr(10).'@'.$new_chat_member_username;
    $welcome_massage = urlencode($welcome_massage);
    send_group_message($chat_id,$token,$welcome_massage);
  } else {
    $members = getChatMembersCount($chat_id,$token);
    if ($members < 100) {
      $welcome_massage = 'ممنون که من رو به گروه دعوت کردید';
      send_group_message($chat_id,$token,$welcome_massage);
      $admins = getChatAdministrators  ($chat_id,$token);
      if (is_array($admins)) {
        foreach ($admins as $admin) {  
          $user = $admin->user;
          $status = $admin->status;
        }
      }  
    } 
}
}

$left_chat_member = $message->left_chat_member;
$left_chat_member_id = $left_chat_member->id;
$left_chat_member_first_name = $left_chat_member->first_name;
$left_chat_member_last_name = $left_chat_member->last_name;
$groupname = $chat->title;
if ($left_chat_member_id != '') {
  $leave_message = 'دوستان، '.$left_chat_member_first_name.' '. $left_chat_member_last_name.' عزیز'.chr(10).'گروه '.$groupname.'را ترک کرد!';
  $leave_message = urlencode($leave_message);
  send_group_message($chat_id,$token,$leave_message);
}

$new_chat_title = $message->new_chat_title;
if ($new_chat_title != '') {
  $chanetitle = 'دوستان '.$username.' اسم گروه رو به'.$new_chat_title.' تغییر داد.';
  send_group_message($chat_id,$token,$chanetitle);
}
$url = 'https://api.telegram.org/bot'.$token.'/sendMessage?chat_id=80853440&text='.$json;
 file_get_contents($url);
unbanChatMember ('$user_id','$chat_id',$token);
if ($text == 'http://telegram.me/' || 'https://telegram.me/') {
   kickChatMember ($user_id,$chat_id,$token);
 }
function kickChatMember ($user_id,$chat_id,$token) {
  $url = 'https://api.telegram.org/bot'.$token.'/kickChatMember?chat_id='.$chat_id.'&user_id='.$user_id;
  file_get_contents($url);
}
function unbanChatMember ($user_id,$chat_id,$token) {
  $url = 'https://api.telegram.org/bot'.$token.'/unbanChatMember?chat_id='.$chat_id.'&user_id='.$user_id;
  file_get_contents($url);
}
function send_group_message($chat_id,$token,$message) {
  $url = 'https://api.telegram.org/bot'.$token.'/sendMessage?chat_id='.$chat_id.'&text='.$message;
  file_get_contents($url);
}
function getChat($chat_id,$token) {
  $url = 'https://api.telegram.org/bot'.$token.'/getChat?chat_id='.$chat_id;
  $result = file_get_contents($url);
  //send_group_message($chat_id,$token,$result);
}
function getChatAdministrators($chat_id,$token) {
  $url = 'https://api.telegram.org/bot'.$token.'/getChatAdministrators?chat_id='.$chat_id;
  $result = file_get_contents($url);
  //send_group_message($chat_id,$token,$result);
  $result = json_decode ($result);
  $result = $result->result;
  return $result;
}
function getChatMembersCount($chat_id,$token) {
  $url = 'https://api.telegram.org/bot'.$token.'/getChatMembersCount?chat_id='.$chat_id;
  $result = file_get_contents($url);
  $result = json_decode ($result);
  $result = $result->result;
  return $result;
}
function leaveChat($chat_id,$token) {
  $url = 'https://api.telegram.org/bot'.$token.'/leaveChat?chat_id='.$chat_id;
  $result = file_get_contents($url);
}
function getMe($token) {
  $url = 'https://api.telegram.org/bot'.$token.'/getMe';
  $result = file_get_contents($url);
  return ($result);
}
//====================ᵗᶦᵏᵃᵖᵖ======================//
define('API_KEY',$token);
//----######------
function ali($method,$datas=[]){
    $url = "https://api.telegram.org/bot".API_KEY."/".$method;
    $ch = curl_init();
    curl_setopt($ch,CURLOPT_URL,$url);
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
    curl_setopt($ch,CURLOPT_POSTFIELDS,http_build_query($datas));
    $res = curl_exec($ch);
    if(curl_error($ch)){
        var_dump(curl_error($ch));
    }else{
        return json_decode($res);
    }
}
$result=json_decode($message,true);
//_
$update = json_decode(file_get_contents('php://input'));
var_dump($update);
//=========
//_______
function SendMessage($chat_id, $ALI)
{
 ali('sendMessage',[
'chat_id'=>$chat_id,
'text'=>$ALI,
'parse_mode'=>"MarkDown"
]);
}
function SendAction($chat_id, $action){
	ali('SendChatAction',[
	'chat_id'=>$chat_id,
	'action'=>$action
	]);
	}
//====================ᵗᶦᵏᵃᵖᵖ======================//
if($text == "/start"){
    var_dump(ali('sendMessage',[ 
    SendAction($chat_id, typing),
        'chat_id'=>$update->message->chat->id, 
        'text'=>"سلام دوست عزیز به ربات ضد لینک و خوش امد گوشی گروه خوش امدید😉😅\n برای اینکه بتونی از من استفاده کنی من را عوض گروهت کن😉",
        'parse_mode'=>'MarkDown',
        'reply_markup'=>json_encode([
            'inline_keyboard'=>[
                [
                    ['text'=>"سازنده من😊",'url'=>"https://telegram.me/aliesmaieli"],['text'=>"کانال من😎",'url'=>"https://telegram.me/tikapp"]
                ]
            ]
        ])
    ]));
}
elseif(preg_match('/^\/([Oo]therbot)/',$textmessage)){
        ali("forwardmessage", [
                'chat_id' => $chat_id,
                'from_chat_id' => "@tikapp",
                'message_id' => 12
            ]);
        }
?>




