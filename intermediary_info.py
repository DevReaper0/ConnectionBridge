import requests
import socket

FIX_HOSTNAMES = True

url = "https://intermediary-server-cdn.darubyminer360.repl.co/"
result = requests.get(url).text

if FIX_HOSTNAMES and not result.split(":")[0].replace(".", "").isnumeric():
    result = socket.gethostbyname(result.split(":")[0]) + ":" + result.split(":")[1]
    requests.post(url, json={"ngrok_ip": result})

if __name__ == "__main__":
    print(result)
