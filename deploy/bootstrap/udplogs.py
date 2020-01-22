import socketserver

class LogHandler(socketserver.BaseRequestHandler):

    def handle(self):
        client = self.client_address[0]
        data = self.request[0].strip()
        print(client,"|",data.decode(errors='ignore'))

if __name__ == "__main__":
    print('Starting a UDP listener on port 9000')
    with socketserver.UDPServer(("0.0.0.0", 9000), LogHandler) as server:
        server.serve_forever()
