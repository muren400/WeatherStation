from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import os

hostName = "localhost"
serverPort = 13337
csvFormat = "{}, {}\n"
htmlTableRowFormat = "<tr><td>{}</td><td>{}</td></tr>"

def getHomePath():
    return os.path.dirname(os.path.realpath(__file__))

def getFilePath():
    return getHomePath() + "/data/data" + datetime.today().strftime('_%Y-%m-%d') + ".csv"

def getLogFilePath():
    return getHomePath() + "/server.log"

def logError(error):
    try:
        errorString = repr(error)
        print(errorString)

        dataFile = open(getLogFilePath(),'a+')
        dataFile.write(errorString)
        dataFile.write("\n")
        dataFile.close()
    except Exception as e:
        print(str(e.type))

def getFileContent(path):
    try:
        fileObject = open(path,'r')
        content = fileObject.read()
        fileObject.close()
        return content
    except Exception as error:
            logError(error)

def getIndexHtml():
    try:
        return getFileContent(getHomePath() + "/gui/index.html")
    except Exception as error:
            logError(error)

def queryData():
    try:
        return getFileContent(getFilePath())
    except Exception as error:
            logError(error)

def logTemperature(temperature):
    try:
        dataFile = open(getFilePath(),'a+')
        timestamp = int(datetime.now().timestamp())
        dataFile.write(csvFormat.format(timestamp, temperature))
        dataFile.close()
        print("Temperature %s" % temperature)
    except Exception as error:
            logError(error)

class MyServer(BaseHTTPRequestHandler):
    def do_GET(request):
        try:
            request.send_response(200)
            request.send_header("Content-type", "text/html")
            request.end_headers()

            parsedPath = urlparse(request.path)

            print("Path %s" % request.path)

            if parsedPath.path == "/":
                request.wfile.write(bytes(getIndexHtml(), "utf-8"))
            elif parsedPath.path == "/query":
                request.wfile.write(bytes(queryData(), "utf-8"))
            elif "/putTemperature?temp=" in request.path:
                query_components = parse_qs(parsedPath.query)
                temperature = query_components["temp"][0]

                request.wfile.write(bytes("<p>Temperature: %s</p>" % temperature, "utf-8"))

                logTemperature(temperature)
            else:
                request.wfile.write(bytes("<p>So nicht!</p>", "utf-8"))
        except Exception as error:
            logError(error)


if __name__ == "__main__":
    webServer = HTTPServer(('', serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
         pass

    webServer.server_close()
    print("Server stopped.")
