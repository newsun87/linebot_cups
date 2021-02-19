#!/bin/bash
git config --global user.email "newsun87@mail.sju.edu.tw"
git config --global user.name "newsun87"
git init  # 本地端資料夾新增一個 .git 資料(這個資料夾變成 Git 可管理的倉庫)
git add . # 把該目錄下的所有檔案新增到倉庫
git commit -m "Init"  # 把專案提交到倉庫
git remote rm origin # 將之前的連結刪除
git remote add origin https://github.com/newsun87/linebot_cups.git # 把本地倉庫與Github 倉庫進行連結
git push origin master # 把本地庫的所有內容推送到遠端倉庫
