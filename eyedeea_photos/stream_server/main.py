# eyedeea_photos_stream_server.py
import asyncio
import subprocess
import threading
from flask import Flask, Response, render_template
from flask_socketio import SocketIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import cv2
import numpy as np
import time
import os
import argparse
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class WebsiteStreamer:
    def __init__(self):
        self.website_url = config.get('settings', 'website_url')
        self.process = None
        self.driver = None
        self.streaming = False
        print("Starting Eyedeea Photos streaming server...")
        print(f"Accessing Eyedeea Photos website at: {self.website_url}")
        self.setup_browser()
    
    def start_ffmpeg_conversion(self, input_url):
        """Start FFmpeg to convert MJPEG to MP4"""
        if self.process:
            self.process.terminate()

        try:
            self.process = subprocess.Popen([
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', input_url,           # Input MJPEG stream
                '-c:v', 'libx264',         # Video codec: H.264
                '-preset', 'ultrafast',    # Fast encoding
                '-tune', 'zerolatency',    # Low latency
                '-f', 'mp4',               # Output format: MP4
                '-movflags', 'frag_keyframe+empty_moov',  # Streaming-friendly MP4
                'pipe:1'                   # Output to stdout
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            print("✅ FFmpeg conversion started")
        except Exception as e:
            print(f"❌ FFmpeg error: {e}")

    def setup_browser(self):
        """Setup headless Chrome browser"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--hide-scrollbars")
        
        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        #self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(self.website_url)
        print(f"Browser loaded: {self.website_url}")
    
    def capture_frame(self):
        """Capture screenshot as numpy array"""
        try:
            # Take screenshot
            screenshot = self.driver.get_screenshot_as_png()
            
            # Convert to numpy array
            nparr = np.frombuffer(screenshot, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return frame
        except Exception as e:
            print(f"Capture error: {e}")
            return None
    
    def generate_frames(self):
        """Generate video frames from website screenshots"""
        while self.streaming:
            frame = self.capture_frame()
            if frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [
                    cv2.IMWRITE_JPEG_QUALITY, 80
                ])
                frame_bytes = buffer.tobytes()
                
                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS

# Initialize streamer
streamer = WebsiteStreamer()

@app.route('/')
def index():
    return render_template('stream_player.html')

@app.route('/video_feed')
def video_feed():
    """MJPEG stream endpoint"""
    streamer.streaming = True
    return Response(streamer.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_mp4')
def mp4_stream():
    """MP4 stream endpoint (for Chromecast)"""
    mjpeg_url = 'http://localhost:9090/video_feed'  # Your MJPEG source
    
    streamer.streaming = True
    streamer.start_ffmpeg_conversion(mjpeg_url)
    
    response = Response(
        streamer.generate_frames(),
        mimetype='video/mp4'
    )
    return response

@app.route('/streamer/video_feed_hls')
def hls_stream():
    """HLS stream endpoint (best for Chromecast)"""
    mjpeg_url = 'http://localhost:9090/video_feed'
    
    # FFmpeg to HLS conversion
    process = subprocess.Popen([
        'ffmpeg',
        '-i', mjpeg_url,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-f', 'hls',
        '-hls_time', '2',
        '-hls_list_size', '3',
        '-hls_flags', 'delete_segments',
        'pipe:1'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return Response(process.stdout, mimetype='application/vnd.apple.mpegurl')

@app.route('/stream')
def stream_page():
    """HTML page with embedded video stream"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Eyedeea Photos Stream Server</title>
        <style>
            body { margin: 0; padding: 20px; background: #000; }
            #video-stream { 
                width: 100%; 
                max-width: 1920px; 
                height: auto;
                border: 2px solid #333;
            }
            .controls {
                margin: 10px 0;
                text-align: center;
            }
            button {
                padding: 10px 20px;
                margin: 0 5px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="controls">
            <button onclick="refreshStream()">Refresh Stream</button>
            <button onclick="toggleFullscreen()">Fullscreen</button>
        </div>
        <img id="video-stream" src="/streamer/video_feed" alt="Live Stream">
        
        <script>
            function refreshStream() {
                const img = document.getElementById('video-stream');
                img.src = '/streamer/video_feed?t=' + new Date().getTime();
            }
            
            function toggleFullscreen() {
                const elem = document.getElementById('video-stream');
                if (!document.fullscreenElement) {
                    elem.requestFullscreen().catch(err => {
                        console.log(`Error attempting full-screen mode: ${err.message}`);
                    });
                } else {
                    document.exitFullscreen();
                }
            }
            
            // Auto-refresh on connection issues
            setInterval(() => {
                const img = document.getElementById('video-stream');
                if (img.naturalWidth === 0) {
                    refreshStream();
                }
            }, 5000);
        </script>
    </body>
    </html>
    '''

@socketio.on('connect')
def handle_connect():
    print('Client connected to stream')
    streamer.streaming = True

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from stream')

def parse_args():
    parser = argparse.ArgumentParser(description='Website Streamer.')
    parser.add_argument('--url', type=str, default='http://127.0.0.1:8080',
                        help='URL of the website to stream')
    return parser.parse_args()

# if __name__ == '__main__':
#     args = parse_args()
#     #streamer = WebsiteStreamer(website_url=args.url) 
#     print("Starting website streaming server...")
#     print("Access streams at:")
#     print("  http://127.0.0.1:9090/stream - Video stream page")
#     print("  http://127.0.0.1:9090/video_feed - Raw MJPEG stream")
    
#     socketio.run(app, host='0.0.0.0', port=9090, debug=True)
