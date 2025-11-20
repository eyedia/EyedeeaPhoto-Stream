eyedeea_photos/
├── stream_server/
│   ├── __init__.py
│   ├── main.py
│   ├── requirements.txt
├── setup.py
├── README.md

pip install setuptools wheel
python setup.py sdist bdist_wheel

Prod Linux:
sudo mkdir /var/log/eyedeea_streamer
sudo /var/eyedeea_streamer/bin/pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9090 stream_server:app

Prod Windows:
pip install waitress
waitress-serve --port 9090 wsgi:application

sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver