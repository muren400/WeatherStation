from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import os

hostName = "localhost"
serverPort = 13337
csvFormat = "{}, {}\n"
htmlTableRowFormat = "<tr><td>{}</td><td>{}</td></tr>"

def getFilePath():
    return os.path.dirname(os.path.realpath(__file__)) + "/data/data" + datetime.today().strftime('_%Y-%m-%d') + ".csv"

def getLogFilePath():
    return os.path.dirname(os.path.realpath(__file__)) + "/server.log"

def logError(error):
    try:
        dataFile = open(getLogFilePath(),'a+')
        dataFile.write(repr(error))
        dataFile.write("\n")
        dataFile.close()
    except Exception as e:
        print(str(e.type))

def queryData():
    try:
        dataFile = open(getFilePath(),'r')
        data = dataFile.read()
        dataFile.close()
        return data
    except Exception as error:
            logError(error)

def queryDataHtml():
    htmlData = "<style>table, th, td {border: 1px solid black;}</style><table><tr><th>date and time</th><th>temperature</th>"
    try:
        dataFile = open(getFilePath(),'r')
        for line in dataFile:
            print(line)
            cols = line.split(",")

            try:
                dateAsString = datetime.fromtimestamp(int(cols[0]))
                htmlData += htmlTableRowFormat.format(dateAsString, cols[1])
            except ValueError as e:
                print(e)

        htmlData += "</table>"

    except Exception as error:
            logError(error)

    return htmlData

def queryDataHtmlPlotted():
    try:
        htmlData = '''<!DOCTYPE html>
        <html>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js"></script>
        <body>
        <canvas id="myChart" style="width:100%;"></canvas>
        <script>'''

        dateValues = []
        temperatureValues = []

        dataFile = open(getFilePath(),'r')
        for line in dataFile:
            print(line)
            cols = line.split(",")

            try:
                dateValues.append(str(datetime.fromtimestamp(int(cols[0]))))
                temperatureValues.append(float(cols[1]))
            except ValueError as e:
                print(e)

        htmlData += 'const xValues = ' + str(dateValues) + ';'
        htmlData += 'const yValues = ' + str(temperatureValues) + ';'

        htmlData += '''new Chart("myChart", {
            type: "line",
            data: {
                labels: xValues,
                datasets: [{
                    fill: false,
                    borderColor: "rgba(0,0,255)",
                    data: yValues
                }]
            },
            options: {
                legend: {display: false},
                scales: {
                    yAxes: [{ticks: {min: ''' + str(min(temperatureValues) - 1) + ',  max:' + str(max(temperatureValues) + 1) + '''}}],
                }
            }
        });
        </script>
        </body>
        </html>'''

        return htmlData
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

            if parsedPath.path == "/query":
                request.wfile.write(bytes(queryData(), "utf-8"))
            elif parsedPath.path == "/queryHtml":
                request.wfile.write(bytes(queryDataHtml(), "utf-8"))
            elif parsedPath.path == "/queryHtmlPlotted":
                request.wfile.write(bytes(queryDataHtmlPlotted(), "utf-8"))
            elif "?temp=" in request.path:
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
