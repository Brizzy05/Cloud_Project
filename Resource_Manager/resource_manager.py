from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def cloud():
    if request.method == 'GET':
        print('A client says hello')
        response = 'Cloud says hello!'
        return jsonify({'response': response})

@app.route('/cloud/nodes/<name>')
def cloud_register(name):
    if request.method == 'GET':
        print('Request to register new node: ' + str(name))
        #TODO: call proxy to register node
        result = 'success'
        return jsonify({'result': result, 'node_name': str(name)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
