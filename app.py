from flask import Flask ,render_template, request
from werkzeug.utils import secure_filename
from AI_Yolo import yolo3
import ssl
import pymysql
import os
import numpy as np
import cv2
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__) 
@app.route("/",methods=['GET','POST'])
def hello():
    return "HELLO WORD!"

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
    print("-----------------------------")

    result = message.split('\n')
    print(result)

    db= pymysql.connect(host=os.environ.get("DB_host"),
                port=int(os.environ.get("DB_port")),
                user=os.environ.get("DB_user"),
                passwd=os.environ.get("DB_password"),
                db=os.environ.get("DB_database"),
                charset='utf8')
    
    cursor = db.cursor()

    for i in result :
        if i == "no_goggles" :
            print('1')
        elif i == "no_vest" :
            print("2")
        elif i == "no_helmet" :
            sql = "UPDATE Worker SET wEquipment = 'nohelmet' where wid = '1760690698'"
        elif i == "no_gloves" :
            print("4")
        else :
            print("5")
    cursor.execute(sql)
    db.commit()
    db.close()

    return result

@app.route('/ai_post',methods=['GET','POST'])
def post():
        path_dir = "../tamjiat_web/public/upload"
        file_list = os.listdir(path_dir)
        name = ""
        print(request.form['file_name'])
        print(request.form['cduuid'])
        
        lists = request.form['file_name']
        uuid = request.form['cduuid']

        for i in file_list:
            if i == lists:
                name = i
        result = AI_Test(path_dir+"/"+ name)
        db= pymysql.connect(host=os.environ.get("DB_host"),
                     port=int(os.environ.get("DB_port")),
                     user=os.environ.get("DB_user"),
                     passwd=os.environ.get("DB_password"),
                     db=os.environ.get("DB_database"),
                     charset='utf8')
        cursor = db.cursor()
        if result=="정상":
            sql = "UPDATE userDcrop SET AICheck = '완료' , cdName = '"+result+"', iscdCheck='false' where cduuid = '"+uuid+"'"
        else:
            sql = "UPDATE userDcrop SET AICheck = '완료' , cdName = '"+result+"', iscdCheck='true' where cduuid = '"+uuid+"'"
        cursor.execute(sql)
        db.commit()
        db.close()
        return result
    

if __name__ == '__main__':
    ssl_context= ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_context.load_cert_chain(certfile='server.crt',keyfile='private.key',password='qwerty12')
    app.run(host='localhost',port=5000,debug=True,ssl_context=ssl_context)