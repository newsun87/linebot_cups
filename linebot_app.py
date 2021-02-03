# -*- coding: utf-8
from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import json
import sys, os, time
import mimetypes
import configparser
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import paho.mqtt.client as mqtt

#目前所在絕對路徑
basepath = os.path.dirname(__file__)
print(basepath)

def loadINI():
    cupspath = os.path.dirname(os.path.realpath(__file__))
    cfgpath = os.path.join(cupspath, 'linebot_cups.conf')
    # 創建對象
    config = configparser.ConfigParser()
   # 讀取INI
    config.read(cfgpath, encoding='utf-8')     
    # 取得所有sections
    sections = config.sections()
    # 取得某section之所有items，返回格式為list
    linebot_access_token = config.get('common', 'linebot_access_token')
    linebot_secret = config.get('common', 'linebot_secret')
    device_list_str = config['common']['cups_id_list']
    return ([linebot_access_token , linebot_secret, device_list_str])

# 接收列印的檔案類型 
mimetype_list=['text/plain', 'text/csv', 'application/pdf',
     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
     'application/vnd.openxmlformats-officedocument.presentationml.presentation',
     'application/vnd.ms-powerpoint','application/msword','application/vnd.ms-excel']

iniContent = loadINI()
print(iniContent)

app = Flask(__name__)

@app.route('/',methods=['GET','POST'])    
def upload():
    if request.method=='GET':
      return render_template('index.html')
    else:        
        file=request.files['file']
        upload_path = os.path.join(basepath, 'static', file.filename) 
        file_type = mimetypes.guess_type(file.filename)[0]
        print(file_type)
        if file_type in mimetype_list:
            file.save(upload_path)
            print(file.filename)
            filepath=upload_path
            result = uploadfile_gdrive(filepath, file.filename)            
        else: 
            result = '檔案格式不支援...'                      
        return render_template("index.html", data = result)
     
@app.route('/register',methods=['GET','POST'])    
def register(): 
   cupspath = os.path.dirname(os.path.realpath(__file__))
   cfgpath = os.path.join(cupspath, 'linebot_cups.conf')
   # 創建對象
   config = configparser.ConfigParser()
   # 讀取INI
   config.read(cfgpath, encoding='utf-8')  
   if request.method=='GET':
      return render_template('register.html')
   else:
     device_input=request.form['deviceid']
     userid=request.form['userid']  
     device_list_str = iniContent[2]
     device_list = device_list_str.split(",") 
     print(device_list)
     
     device_opts_list = config.options("device")
     print('device_opts_list', device_opts_list)     
     #device_num = config.get('device', 'cups_id')
     for item in device_list:
      if item == device_input:
       print(item,device_input)
       result = '註冊成功....'       
       config.set('device', userid, device_input)      
       config.write(open(cfgpath, "w"))
       break 
      else:
       result = '列印裝置不存在....'               
     return render_template("register.html", data = result)       

@app.route('/goal',methods=['GET','POST'])    
def goal():
   return render_template("goal.html")

# 上傳檔案至 google drive            
def uploadfile_gdrive(filepath, filename): 
  userid=request.form['userid']  
  cupspath = os.path.dirname(os.path.realpath(__file__))  
  cfgpath = os.path.join(cupspath, 'linebot_cups.conf')
  print('cfgpath', cfgpath)
  # 創建對象
  config = configparser.ConfigParser()
  # 讀取INI
  config.read(cfgpath, encoding='utf-8')   
  gauth = GoogleAuth()
  #gauth.CommandLineAuth() #透過授權碼認證
  drive = GoogleDrive(gauth)
  mqtt_msg = config.get('device', userid) 
  print("mqtt_msg", mqtt_msg)
  try:
    folder_id = config.get('common', 'folder_id')
    #上傳檔案至指定目錄及設定檔名     
    gfile = drive.CreateFile({"parents":[{"kind": "drive#fileLink", "id": folder_id}], 'title': filename})
    #指定上傳檔案的內容    
    gfile.SetContentFile(filepath)
    gfile.Upload() # Upload the file.
    print("Uploading succeeded!")    
    if gfile.uploaded:
      os.remove(filepath)
      result = '檔案傳送完成...'
      client.publish("cups/"+mqtt_msg, "print", qos=1)
      #client.publish("cups/"+mqtt_msg, "", qos=1)               
  except:
    print("Uploading failed.")
    result = '檔案傳送失敗...'
  return result 
  
def delete_gdrive():
  gauth = GoogleAuth()
  #gauth.CommandLineAuth() #透過授權碼認證
  drive = GoogleDrive(gauth)
  # 取得 gdrive 檔案清單
  try:
    file_list1 = drive.ListFile({'q': "'135y-D-jDEh-Bub_WpjmhYxWxJkUyPmUr' in parents and trashed=false"}).GetList() 
    for file1 in file_list1:
     print('title: %s, id: %s' % (file1['title'],file1['id']))     
     print("刪除文件檔...")
     #刪除 gdrive 文件檔案  
     gauth = GoogleAuth()
     #gauth.CommandLineAuth() #透過授權碼認證
     drive = GoogleDrive(gauth)
     file1 = drive.CreateFile({'id': file1['id']})
     file1.Delete()
  except:
    print("Downloading failed.")               

# Channel Access Token
line_bot_api = LineBotApi(iniContent[0])
# Channel Secret
handler = WebhookHandler(iniContent[1]) 

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
   cupspath = os.path.dirname(os.path.realpath(__file__))
   cfgpath = os.path.join(cupspath, 'linebot_cups.conf')
     # 創建對象
   config = configparser.ConfigParser()
     # 讀取INI
   config.read(cfgpath, encoding='utf-8') 
   userid = event.source.user_id
   print('userid', userid )
   if config.has_option('device',userid): 
     device_num = config.get('device', userid)
   else:
     config.set('device', userid, " ")
     config.write(open("linebot_cups.conf", "w"))
     device_num = config.get('device', userid)     
   if event.message.text == 'register': 
     message = TextSendMessage(text = '請點選 https://liff.line.me/1654118646-kzqdwpx0')     
   elif event.message.text == 'print':         
     if device_num == '':
       message = TextSendMessage(text = '未註冊列印裝置....')
     else:  
       message = printer_template()     
   elif event.message.text == 'page':
      if device_num == '':
        message = TextSendMessage(text = '未註冊列印裝置....')
      else:
        message = TextSendMessage(text = 'https://liff.line.me/1654118646-GYvYL8WQ')      
   elif event.message.text == 'delete':
      if device_num == '':
        message = TextSendMessage(text = '未註冊列印裝置....')
      else:
        delete_gdrive()
        message = TextSendMessage(text = '檔案刪除完成')     
   else:
     message = TextSendMessage(text = '我不懂你的意思...')
   line_bot_api.reply_message(event.reply_token, message)
	
def printer_template():
    buttons_template_message = TemplateSendMessage(
         alt_text = '我是系統設定按鈕選單模板',
         template = ButtonsTemplate(
            thumbnail_image_url = 'https://i.imgur.com/oimUK1g.png', 
            title = '檔案列印選單',  # 你的標題名稱
            text = '開啟網頁連結，選擇要列印的檔案',  # 你要問的問題，或是文字敘述            
            actions = [ # action 最多只能4個喔！
                URIAction(
                    label = '網頁連結', # 在按鈕模板上顯示的名稱
                    uri = "https://liff.line.me/1654118646-GYvYL8WQ"  
                )   
            ]
         )
        )
    return buttons_template_message

# paho callbacks
def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

def on_message(client, userdata, msg): # 收到訂閱訊息的處理    
  print(msg.topic + " " + msg.payload.decode())       
  if msg.payload.decode() == 'finish': 
   print("receive finish message")      
   return render_template("index.html", data = "檔案列印完成....")   
  

if __name__ == "__main__":
  client = mqtt.Client()  
  client.on_connect = on_connect  
  client.on_message = on_message  
  client.connect("broker.mqttdashboard.com", 1883) 
  client.loop_start()    
  app.run(debug=True, host='0.0.0.0', port=5000)

     
