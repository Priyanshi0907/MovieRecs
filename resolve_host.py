import socket

try:
    ip = socket.gethostbyname("api.themoviedb.org")
    print("Resolved IP of api.themoviedb.org:", ip)
except Exception as e:
    print("Failed to resolve:", e)
