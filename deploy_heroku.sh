git config --global user.email 'newsun87@mail.sju.edu.tw'
git config --global user.name 'newsun87'
git init
heroku git:remote -a cups-printer
git add .
git commit -m "init."
git push heroku master
