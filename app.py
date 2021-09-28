from flask import Flask ,render_template, Request, Response, request
from flask import stream_with_context
from werkzeug.utils import secure_filename
from AI_Yolo import yolo3
from AI_Yolo_webcam import yolo_webcam
import ssl
import pymysql
import os
import numpy as np
import cv2
import requests
from cctv.streamer import Streamer

app = Flask( __name__ )
streamer = Streamer()
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__) 
@app.route("/",methods=['GET','POST'])
def hello():
    return "HELLO WORD!"

@app.route("/webcam",methods=['GET','POST'])
def stream():
    
    src = request.args.get( 'src', default = 0, type = int )
    
    try :
        return Response(stream_with_context( stream_gen( src ) ),mimetype='multipart/x-mixed-replace; boundary=frame' )
        
    except Exception as e :
        print('[wandlab] ', 'stream error : ',str(e))

def stream_gen( src ):   
  
    try : 
        
        streamer.run( src )
        
        while True :
            
            frame = streamer.bytescode()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    
    except GeneratorExit :
        #print( '[wandlab]', 'disconnected stream' )
        streamer.stop()

@app.route("/test",methods=['GET','POST'])
def ai_ground():
    cap = cv2.VideoCapture(0)
    cap.set(3,640)
    cap.set(4,480)

    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)

    cv2.imwrite('worker_images/worker.jpg',frame)

    cap.release()
    cv2.destroyAllWindows() 

    message = yolo3('worker_images/worker.jpg')
    print("-----------------------------")
    print(message)
    print(request.form['kakaoid'])
    print("-----------------------------")

    result = message.split('|')
    result.pop()
    print(result)

    db= pymysql.connect(host=os.environ.get("DB_host"),
                port=int(os.environ.get("DB_port")),
                user=os.environ.get("DB_user"),
                passwd=os.environ.get("DB_password"),
                db=os.environ.get("DB_database"),
                charset='utf8')
    
    cursor = db.cursor()
    num = 0
    for i in result :
        if i == "no_goggles" :
            print('1')
            requests.post('https://grounda.hopto.org/manual/guide', data="no_goggles")
        elif i == "no_vest" :
            print("2")
            requests.post('https://grounda.hopto.org/manual/guide', data="no_vest")
        elif i == "no_helmet" :
            print("3")
            requests.post('https://grounda.hopto.org/manual/guide', data="no_helmet")
        elif i == "no_gloves" :
            print("4")
            requests.post('https://grounda.hopto.org/manual/guide', data="no_gloves")
        elif i ==  "helmet" or i=="vest" or i=="goggles":
            num = num + 1
            print(num)
        if num==3:
            requests.post('http://grounda.hopto.org:5001', data="success")
            requests.post('https://grounda.hopto.org/manual/guide', data="success")
            sql = "UPDATE Worker SET wEquipment = 'Success' where wid = '"+kakaoid+"'"
            print("5")
    cursor.execute(sql)
    db.commit()
    db.close()
    
    return request.form['kakaoid']
    

if __name__ == '__main__':
    ssl_context= ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_context.load_cert_chain(certfile='private.crt',keyfile='private.key',password='qwerty12')
    app.run(host='0.0.0.0',port=5000,debug=True,ssl_context=ssl_context)