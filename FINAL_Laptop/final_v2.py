import cv2 as cv
import numpy as np
import face_recognition
import os
from datetime import datetime
import time
from PIL import Image
import math

from send_message import send_message
from alarm_sound import play_sound
from linux_brightness import brightness_adjust


from cvzone.FaceMeshModule import FaceMeshDetector
import pickle

import dlib
from imutils import face_utils
from scipy.spatial import distance as dist


user_id=0
time_to_check_new_face=0 #initial

# import pictures from photos folder
path = 'photos'
images = []
classNames = []
mylist = os.listdir(path)
print(mylist)
for cl in mylist:
    currImg = cv.imread(f'{path}/{cl}')
    images.append(currImg)
    classNames.append(os.path.splitext(cl)[0])

print(classNames)


# convert them into embeddings
def findEncodings(images):
    encodings = []
    for img in images:
        img = cv.cvtColor(img,cv.COLOR_BGR2RGB)
        enc = face_recognition.face_encodings(img)[0]
        encodings.append(enc)
    return encodings


# initialize timer to zero
face_detected_timer={}
for i in classNames:
    face_detected_timer[i.upper()]=0

print(face_detected_timer)

# useful if only in one frame a person is not shown
face_not_detected_timer={}
for i in classNames:
    face_not_detected_timer[i.upper()]=0

print(face_not_detected_timer)

# check if person is detected in every frame 
bool_person_detected={}
for i in classNames:
    bool_person_detected[i.upper()]=False

print(bool_person_detected)


timer_to_send_notification_for_2_min=0


encodeListKnown = findEncodings(images)
print('Encoding Complete')


def FacePresent(name):
    
    # face is detected after gap
    if(face_detected_timer[name]==0):
        # print("HERE.............................................")
        face_detected_timer[name]=time.time()

    
    
    else:
        # face_not_detected_timer[name]=0

        elapsed_time_mark = time.time() - face_detected_timer[name]
        print(name,"...",elapsed_time)
        if elapsed_time_mark > 20:  # If face is not detected for more than 20 seconds
            # print(math.ceil(elapsed_time_mark),"..........................................")
            
            if math.ceil(elapsed_time)%10==0:
                send_message("Please Take A Break")
                play_sound()
                print(name,"Please Take A Break")
                # face_detected_timer[name]=0



cap = cv.VideoCapture(0)


img = cap.read()
known_faces = []



# yawn detection
penalty=0

def calculate_lip(lips):
    dist1 = dist.euclidean(lips[2], lips[6]) 
    dist2 = dist.euclidean(lips[0], lips[4]) 

    LAR = float(dist1/dist2)

    return LAR

counter = 0
lip_LAR = 0.4
lip_per_frame = 30



temp=0

min_brightness=20
max_brightness=90

while True:
    #Timer 20-20-20
    for i in classNames:
        name=i.upper()
        bool_person_detected[name]=False
    
    success,img = cap.read()
    imgS = cv.resize(img,(0,0),None,0.25,0.25)
    imgS = cv.cvtColor(imgS,cv.COLOR_BGR2RGB)
    facesCurFrame = face_recognition.face_locations(imgS)
    encCurFrame = face_recognition.face_encodings(imgS,facesCurFrame)
    
    for encodeFace,faceLoc in zip(encCurFrame,facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown,encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown,encodeFace)
        matchIndex = np.argmin(faceDis)
        
        
        if matches[matchIndex]:
            name = classNames[matchIndex].upper()
            bool_person_detected[name]=True
            # print(name)
            y1,x2,y2,x1 = faceLoc
            y1,x2,y2,x1= y1*4,x2*4,y2*4,x1*4
            cv.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
            cv.rectangle(img,(x1,y2-35),(x2,y2),(0,255,0),cv.FILLED)
            cv.putText(img,name,(x1+6,y2-6),cv.FONT_HERSHEY_PLAIN,1,(255,255,255),2)
            # face detected
            FacePresent(name)

        else:
            print("ELSE")
            elapsed_time = time.time() - time_to_check_new_face

            if elapsed_time > 3*60 or time_to_check_new_face==0:  # If face is not detected for more than 20 seconds

                time_to_check_new_face=time.time()
                is_new_face = all(face_recognition.face_distance(known_face, encodeListKnown) > 0.6 for known_face in known_faces)
                if is_new_face:
                    encodeListKnown.append(encodeFace)
                    img_name = f'opencv_frame_.png'
                    cv.imwrite(img_name, img)

                    img_save = Image.open(img_name)
                    img2 = img_save.crop(box=[faceLoc[3]*4,faceLoc[0]*4,faceLoc[1]*4,faceLoc[2]*4])
                    output_path = os.path.join('photos', f'USER_{user_id}.jpg')
                    # img2.save(f'USER_{user_id}.jpg')
                    img2.save(output_path)

                    classNames.append(f"USER_{user_id}")
                    face_detected_timer[f'USER_{user_id}']=0
                    face_not_detected_timer[f'USER_{user_id}']=0
                    bool_person_detected[f'USER_{user_id}']=0

                    user_id+=1


    # Timer
    for i in classNames:
        name=i.upper()

        if not bool_person_detected[name]:
            # Call your function here when the person is not detected
            # face is detected after gap
            if(face_not_detected_timer[name]==0):
                #  print("HERE.............................................")
                face_not_detected_timer[name]=time.time()


            else:
                elapsed_time = time.time() - face_not_detected_timer[name]
                # print(name,elapsed_time)
                if elapsed_time > 10:  # If face is not detected for more than 20 seconds
                    face_not_detected_timer[name]=0
                    face_detected_timer[name]=0


    
    
    # Face distance
    detector = FaceMeshDetector(maxFaces=5)
    img,faces = detector.findFaceMesh(img,draw=False)
    if faces:
        for face in faces:
            if temp==0:
                # filename = os.path.join("detected_faces", f"face{temp}.pkl")
                with open(f"face{temp}.pkl", "wb") as fp:   #Pickling
                    pickle.dump(face, fp)
                
                with open(f"face{temp}.pkl", "rb") as fp:   #Pickling
                    temp_list=pickle.load(fp)

                
                temp=1
            
            pointLeft = face[145]
            pointRight = face[374]

            w, _ = detector.findDistance(pointLeft, pointRight)
            W = 6.3
            f = 840
            d = (W * f) / w
            
            # For Mobiles
            # if d < 15:

            # For Laptops
            if d < 40:
                if timer_to_send_notification_for_2_min==0:
                    # play_sound()
                    send_message("You are very near to screen.")
                    print("go back ")

                    timer_to_send_notification_for_2_min=time.time()
                
                elif time.time()-timer_to_send_notification_for_2_min>2*60:
                    send_message("You are very near to screen.")
                    print("go back ")
                    
                    timer_to_send_notification_for_2_min=0

            else:
                timer_to_send_notification_for_2_min=0


    # Yawn detection
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    

    _, frame = cap.read()
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    faces = detector(gray)
    for (i, face) in enumerate(faces):
        lips = [60,61,62,63,64,65,66,67]
        point = predictor(gray, face)
        points = face_utils.shape_to_np(point)
        lip_point = points[lips]
        LAR = calculate_lip(lip_point) 

        lip_hull = cv.convexHull(lip_point)
        cv.drawContours(frame, [lip_hull], -1, (0, 255, 0), 1)

        if LAR > lip_LAR:
            counter += 1
            print(counter,penalty)
            # if counter > lip_per_frame:
            penalty+=1
            if(penalty>10):
                send_message("Please Take A Coffee Break")
                print("Take A coffee break")
                play_sound()
                
                penalty=0
                # cv.putText(frame, "DROWSINESS ALERT!", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            counter = 0

    # AutoBrightness
    ret, frame = cap.read()
    average_brightness = np.mean(frame)
    brightness_percent = np.interp(average_brightness, [0, 255], [min_brightness, max_brightness])
    brightness = int((brightness_percent / 100) * 100)  # Scale to 0-100

    brightness_adjust(brightness)
    print("brightness adjusted to: ",brightness)
    
    
    
    cv.imshow('webcam',img)    
    
    
    
    if cv.waitKey(1)==ord("q"):
        break

    # time.sleep(1)

cap.release()





