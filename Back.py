from PyDictionary import PyDictionary
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
dictionary = PyDictionary()

@app.route('/')
def index():
    """Connect"""
    return render_template('.html')

class InitGame:
    #

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
