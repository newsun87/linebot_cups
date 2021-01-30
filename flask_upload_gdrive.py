# coding=utf-8
from flask import Flask, request, abort, render_template
import requests
import sys
import os
import mimetypes

#目前所在絕對路徑
basepath = os.path.dirname(__file__)
print(basepath)
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

mimetype_list=['text/plain', 'text/csv', 'application/pdf',
     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
     'application/vnd.openxmlformats-officedocument.presentationml.presentation',
     'application/vnd.ms-powerpoint','application/msword','application/vnd.ms-excel']

app = Flask(__name__) #name為目前所用的模組

@app.route('/',methods=['GET','POST'])    
def upload():
    if request.method=='GET':
      return render_template('upload.html')
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
        return render_template("upload.html", data = result)

# 上傳檔案至 google drive            
def uploadfile_gdrive(filepath, filename):
  gauth = GoogleAuth()
  #gauth.CommandLineAuth() #透過授權碼認證
  drive = GoogleDrive(gauth)
  try:
    folder_id = '135y-D-jDEh-Bub_WpjmhYxWxJkUyPmUr'
    #上傳檔案至指定目錄及設定檔名     
    gfile = drive.CreateFile({"parents":[{"kind": "drive#fileLink", "id": folder_id}], 'title': filename})
    #指定上傳檔案的內容    
    gfile.SetContentFile(filepath)
    gfile.Upload() # Upload the file.
    print("Uploading succeeded!")
    result = '檔案列印中...'
    if gfile.uploaded:
      os.remove(filepath)
  except:
    print("Uploading failed.")
    result = '檔案傳送失敗...'
  return result               

if __name__ == "__main__": #表示此段為主程式
    app.run(debug=True, host='0.0.0.0', port=8080)
