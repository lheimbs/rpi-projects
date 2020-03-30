# A place for my personal Projects on/including my Pi

## Setup
- Copy data.db file to folder
- If on raspberry: `sudo apt install python3-pip python3-numpy python3-pandas python3-matplotlib python3-scipy`
- Install required python packages `pip3 install -r requirements.txt`
- Test dashboard app `python app.py`
- Enable dashboard service `systemctl --user enable dashboard.service`
- Start dashboard service `systemctl start dashboard.service`
- Do the same with `mqtthandler.service`

