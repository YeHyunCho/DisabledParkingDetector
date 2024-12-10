import RPi.GPIO as GPIO
import time
from picamera2 import Picamera2, Preview
from datetime import datetime
import pygame
import os
import cv2
import torch
from PIL import Image
import numpy as np
from paddleocr import PaddleOCR
import pyttsx3
import deeplearning
import threading
import cf5202 # sudo pip3 install crcmod
import codecs
import app

engine = pyttsx3.init()

#model_path2 = './best.pt'
#img = './6.jpg'


# GPIO 핀 번호 설정 (BCM 모드)
TRIG_PIN = 18
ECHO_PIN = 24

# GPIO 초기화
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Picamera2 초기화
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
picam2.start()


def display_camera():
    while True:
        frame = picam2.capture_array()  # 실시간 프레임 가져오기
        
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_resized = cv2.resize(frame_bgr, (640, 480))
        
        cv2.imshow("Camera Preview", frame_resized)  # 화면에 표시

        # 'q'를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    picam2.stop()

def play_announcment(file_path) :

    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy() :
        pass

# 거리 측정 함수
def measure_distance():
    # 트리거 핀을 LOW로 설정하고 잠시 대기
    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.1)

    # 초음파 발사 (TRIG 핀을 HIGH로 10μs 동안 유지)
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # ECHO 핀이 HIGH가 될 때까지 시간 측정
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        pulse_start = time.time()

    # ECHO 핀이 LOW로 돌아올 때까지 시간 측정
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        pulse_end = time.time()

    # 시간 차 계산
    pulse_duration = pulse_end - pulse_start

    # 거리 계산 (소리 속도 34300 cm/s)
    distance = pulse_duration * 34300 / 2

    return round(distance, 2)

# 사진 촬영 함수
def capture_image():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_path = f'/home/kimym/disabled_parking_system/savedImage/captured_{timestamp}.jpg'
    picam2.capture_file(image_path)
    print(f"사진 저장 완료. 객체 인식을 시작합니다 ----------")
    return image_path

if __name__ == '__main__':
    reader = cf5202.RU5202()
    # 스레드로 카메라 화면 표시 실행
    camera_thread = threading.Thread(target=display_camera)
    camera_thread.daemon = True
    camera_thread.start()
    
    try:
        while True:
            # 거리 측정
            distance = measure_distance()
            print(f"Measured Distance: {distance} cm")

            # 특정 거리 이내일 때 사진 촬영 (80cm 이하)
            if distance <= 105:
                print("새로운 물체가 감지 구역 내로 들어왔습니다.")
                
                # RFID 리더기로 태그 인식 시도
                tag = '' 
                for x in range(20):
                    if(tag == ''): # 인식 안 된 상태
                        tag = cf5202.check_tag(reader)
                    time.sleep(0.4)
                if (tag == '') :  # 태그 인식이 되지 않았을 때
                    print("장애인 주차 태그가 인식되지 않습니다. 사진을 촬영합니다.")
                    image_path = capture_image()
                    
                    if image_path : # 사진 촬영이 잘 되었다면 번호판 인식 라이브러리 임포트
                        license_yolo = deeplearning.yolo(image_path)
                        if license_yolo and license_yolo != 2 :   # 자동차로 인식이 되었다면
                            result_ocr = deeplearning.ocr(license_yolo)
                            car_number_path = deeplearning.tts(result_ocr)

                            files = [car_number_path, "warning.mp3"]
                            for file in files :
                                play_announcment(file)
                                time.sleep(0.8)
                            
                        elif license_yolo == 2 :
                            print("자동차 이외의 물체로 인식됩니다.")
                            
                        else :
                            # play_announcment("warning.mp3")
                            print("번호판 인식안됨")
                            
                else :  # 태그 인식 되었을 때
                    print('장애인 주차 태그가 인식되었습니다.')
            # 1초 대기
            time.sleep(1)

    except KeyboardInterrupt:
        print("프로그램 종료 중...")

    finally:
        # 리소스 정리
        picam2.stop()
        GPIO.cleanup()
