from waitress import serve
import app


_config = {
    "host": "127.0.0.1",
    "port": "5000"
}

print("Started a waitress server on host: {}, port: {}".format(_config["host"], _config["port"]))
serve(app.app, host=_config["host"], port=_config["port"])

