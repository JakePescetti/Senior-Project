from flask import Flask
from flask import request
from flask import jsonify
import math
import pickle
#from datetime import *

app = Flask(__name__)


@app.route('/data', methods=['POST', 'GET'])
def names():
	
	if request.method == 'GET':
		timeToGrnFile = open("time.pkl","r")#debug was time.pkl
		time = pickle.load(timeToGrnFile)
		timeToGrnFile.close() #new
		return jsonify(time)

	if request.method == 'POST':
		content = request.get_json()
		if content is not None:
			fileObject = open("gps.pkl","wb") 
			pickle.dump(content,fileObject)   
			fileObject.close()
			return jsonify(content)

if __name__ == '__main__':
	app.run(host='0.0.0.0')