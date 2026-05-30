cd ~
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip
python3 -m pip install -r scripts/requirements.txt 
cd scripts/
ls
python3 scanner.py 
