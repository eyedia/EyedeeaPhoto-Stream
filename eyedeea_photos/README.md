eyedeea_photos/
├── stream_server/
│   ├── __init__.py
│   ├── main.py
│   ├── requirements.txt
├── setup.py
├── README.md

***Not using installer/package*** 
pip install setuptools wheel
python setup.py sdist bdist_wheel

Prod Linux:
***1: Get the streamer code from git into the user home(/deb/home) directory***
mkdir eyedeea_photos_stream_server
cd eyedeea_photos_stream_server
git clone https://github.com/eyedia/EyedeeaPhoto-Stream.git

***2: Create other directories*** 
sudo mkdir /var/log/eyedeea_streamer
sudo chown deb:www-data /var/log/eyedeea_streamer
sudo chmod 755 /var/log/eyedeea_streamer

***3: Provide appropriate permissions***
sudo chmod 755 /home/deb/eyedeea_photos_stream_server
sudo chmod 755 /home/deb/eyedeea_photos_stream_server/EyedeeaPhoto-Stream
sudo chmod 755 /home/deb/eyedeea_photos_stream_server/EyedeeaPhoto-Stream/eyedeea_photos
sudo chown www-data:www-data /home/deb/eyedeea_photos_stream_server/EyedeeaPhoto-Stream/eyedeea_photos/eyedeea_photos.sock

***4: Prepare Python venv***
cd /home/deb/eyedeea_photos_stream_server/EyedeeaPhoto-Stream/eyedeea_photos
python -m venv /var/eyedeea_streamer/
sudo /var/eyedeea_streamer/bin/pip install -r ./requirements.txt
sudo /var/eyedeea_streamer/bin/pip install gunicorn
sudo /var/eyedeea_streamer/bin/pip install eventlet
sudo apt-get install ffmpeg

***5: Validate content and copy gunicorn.service ***
cp ../deploy/gunicorn.service /etc/systemd/system/

***Not required in prod server, for test only*** 
gunicorn -w 4 -b 0.0.0.0:9090 stream_server:app

***6: Start the service ***
sudo systemctl start gunicorn
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn

***7: Configure apache server***
000-default.conf should have (read ./deploy/000-default.conf):
ProxyPass /streamer unix:/home/deb/eyedeea_photos_stream_server/EyedeeaPhoto-Stream/eyedeea_photos/eyedeea_photos.sock|http://localhost/
ProxyPassReverse /streamer unix:/home/deb/eyedeea_photos_stream_server/EyedeeaPhoto-Stream/eyedeea_photos/eyedeea_photos.sock|http://localhost/

***8: Restart apache server***
sudo systemctl restart apache2





Prod Windows:
pip install waitress
waitress-serve --port 9090 wsgi:application

sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver