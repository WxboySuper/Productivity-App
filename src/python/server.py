from flask import Flask

app = Flask(__name__)
app.config['PORT'] = 5000

def run_server():
    """Run the Flask server."""
    app.run(port=app.config['PORT'])

if __name__ == '__main__':
    run_server()
