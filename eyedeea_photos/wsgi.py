import os
if os.name == 'posix':
    import fcntl
    
from stream_server.main import app as application