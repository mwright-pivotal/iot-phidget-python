'''
Created on Mar 21, 2015

@author: mwright
'''
from flask import Flask
from flask import request, jsonify, abort
import os, logging, pika
import simplejson as json

if __name__ == '__main__':
    pass

app = Flask(__name__)

port = int(os.getenv("VCAP_APP_PORT"))

if 'VCAP_SERVICES' in os.environ:
    vcap_services = json.loads(os.environ['VCAP_SERVICES'])
    # XXX: avoid hardcoding here
    rabbit_srv = vcap_services['p-rabbitmq'][0]
    cred = rabbit_srv['credentials']

credentials = pika.PlainCredentials(cred['username'], cred['password'])
parameters = pika.ConnectionParameters(credentials=credentials,host=cred['hostname'],virtual_host=cred['vhost'])
    
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.exchange_declare(exchange='amqp.topic',
                         type='topic')
                                     
FORMAT = '%(asctime)-15s %(lineno)d %(message)s'
logging.basicConfig(format=FORMAT)

@app.route('/')
def hello_world():
    return 'Hello World! I am running on port ' + str(port)

@app.route('/api/acceleration/<int:deviceid>', methods=['POST'])
def accelaration_rvc(deviceid):
    if not request.json or not 'device' in request.json:
        logger = logging.getLogger('accel-synapse')
        logger.warning('Payload no good: %s', request.data)
        abort(400)
    point = {
        'type': request.json.get('type'),
        'rcvts': request.json.get('rcvts', ""),
        'x': request.json.get('x'),
        'y': request.json.get('y'),
        'z': request.json.get('z'),
        'done': False
    }
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    json_data = jsonify({'point': point})
    channel.basic_publish(exchange='amq.topic',
                      routing_key='phidget-stream-tap',
                      body=json.dumps(point))
    return json_data, 201
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)