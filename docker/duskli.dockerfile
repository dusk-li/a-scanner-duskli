FROM selenium/selenium/standalone-chrome
RUN sudo apt update && sudo apt upgrade -y;\
 sudo apt install python3-pip;\
 python3 -m pip install -r requirements.txt