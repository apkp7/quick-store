exit
clear

clear
python3 -m venv env
apt-get install python3-venv
sudo apt-get install python3-venv
python3 -m venv env
source env/bin/activate
pip install Django==2.2
pip install djangorestframework
pip install resource
python manage.py migrate
ls
clear
sudo iptables -I INPUT -p tcp -s 0.0.0.0/0 --dport 8000 -j ACCEPT
sudo ufw allow 8000
sudo ufw reload 
clear
ifconfig
clear
ifconfig
clear
ls
python -V
python manage.py migrate
pip install coreapi
clear
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
clear
ls
vim FileSharingSystem/settings.py 
python manage.py runserver 0.0.0.0:8000
clear
python manage.py runserver 0.0.0.0:8000
clear
python manage.py runserver 0.0.0.0:8000
clear
python manage.py runserver 0.0.0.0:8000
