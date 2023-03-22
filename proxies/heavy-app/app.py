from flask import Flask, jsonify
import sys

app = Flask(__name__)

@app.route('/')
def heavy():
    if len(sys.argv) < 2:
        return 'Error'
    x = 0

    for i in range(50000):
        for j in range(50000):
            x += i*j

    return 'Hello from ' + sys.argv[1] + ' in Heavy!. Computation result = \n' + str(x)

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0', port=5002)