#!/bin/bash
sudo kill $(pidof ngrok)
ngrok http 5000 > /dev/null& 
sleep 3
#取得執行結果(位址)當變數
URL4040=$(curl -s localhost:4040/api/tunnels | awk -F"https" '{print $2}' | awk -F"//" '{print $2}' | awk -F'"' '{print $1}')
ACCESS_TOKEN="MMkiyW15qX19JAYquvr1pvET8As9lMEslY40P0C6QZ3" #Line Notify 的驗證碼
message="linebot_cups webhook url https://"$URL4040  #傳入影像檔的路徑
curl https://notify-api.line.me/api/notify -X POST \
   -H "Authorization: Bearer $ACCESS_TOKEN" \
   -F "message=$message"  
