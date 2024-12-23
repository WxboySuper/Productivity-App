from flask import Flask

app = Flask(__name__)
app.config['PORT'] = 5000

if __name__ == '__main__': # pragma: no cover
    app.run(port=app.config['PORT']) # pragma: no cover
