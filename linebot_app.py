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

mimetype_list=['text/plain', 'text/csv', 'application/pdf',
     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
     'application/vnd.openxmlformats-officedocument.presentationml.presentation',
     'application/vnd.ms-powerpoint','application/msword','application/vnd.ms-excel']


config = configparser.ConfigParser()
config.read('linebot_cups.conf')

# 接收列印的檔案類型 
mimetype_list=['text/plain', 'text/csv', 'application/pdf',
     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
     'application/vnd.openxmlformats-officedocument.presentationml.presentation',
     'application/vnd.ms-powerpoint','application/msword','application/vnd.ms-excel']

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
        
@app.route('/goal',methods=['GET','POST'])    
def goal():
   return render_template("goal.html")

# 上傳檔案至 google drive            
def uploadfile_gdrive(filepath, filename):  
  gauth = GoogleAuth()
  #gauth.CommandLineAuth() #透過授權碼認證
  drive = GoogleDrive(gauth)
  try:
    folder_id = config.get('gdrive', 'folder_id')
    #folder_id = '135y-D-jDEh-Bub_WpjmhYxWxJkUyPmUr'
    #上傳檔案至指定目錄及設定檔名     
    gfile = drive.CreateFile({"parents":[{"kind": "drive#fileLink", "id": folder_id}], 'title': filename})
    #指定上傳檔案的內容    
    gfile.SetContentFile(filepath)
    gfile.Upload() # Upload the file.
    print("Uploading succeeded!")    
    if gfile.uploaded:
      os.remove(filepath)
      result = '檔案傳送完成...'
      client.publish("cups/cups0001", "print", qos=1)              
  except:
    print("Uploading failed.")
    result = '檔案傳送失敗...'
  return result               

linebot_access_token = config.get('linebot', 'linebot_access_token')
linebot_secret = config.get('linebot', 'linebot_secret')
# Channel Access Token
line_bot_api = LineBotApi(linebot_access_token)
# Channel Secret
handler = WebhookHandler(linebot_secret) 

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
   if event.message.text == 'print':
      buttons_template_message = printer_template()
      line_bot_api.reply_message(event.reply_token, buttons_template_message)
   elif event.message.text == 'page':
      message = TextSendMessage(text = 'https://liff.line.me/1654118646-GYvYL8WQ')
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
  
client = mqtt.Client()  
client.on_connect = on_connect  
#client.on_message = on_message  
client.connect("broker.mqttdashboard.com", 1883) 
client.loop_start()

if __name__ == "__main__":    
  app.run(debug=True, host='0.0.0.0', port=5000)

     
