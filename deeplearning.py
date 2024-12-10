import os
import cv2
import sys
import torch
from PIL import Image
import numpy as np
from paddleocr import PaddleOCR
import pyttsx3
from datetime import datetime
import time

engine = pyttsx3.init()
plate = 1

model_path2 = './best.pt'
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = torch.hub.load('./yolov7', 'custom', model_path2, source = 'local')
model = model.to(device)


def yolo(img_path) :
    img = cv2.imread(img_path)
    img - cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    result = model(img)
    detections = result.xyxy[0].cpu().numpy()

    
    if len(detections) == 0 :
        # print("탐지된 객체가 없습니다.")
        # print("물체가 감지되었습니다.")
        return 2
    
    
    for detection in detections :
        x_min, y_min, x_max, y_max, conf, class_id = detection
        x_min, y_min, x_max, y_max, class_id = int(x_min), int(y_min), int(x_max), int(y_max), int(class_id)
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)  # 빨간색 박스
        cv2.putText(img, f"Class {int(class_id)}: {conf:.2f}", 
                    (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, (255, 0, 0), 2)  # 텍스트 추가
        # print("clss_id:", class_id)
        
        output_path = f"./outputImage/{os.path.basename(img_path)}_result.jpg"
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # OpenCV 형식으로 변환
        cv2.imwrite(output_path, img_bgr)

        # print(f"결과 이미지가 {output_path}에 저장되었습니다.")
    
        if class_id == plate :
            cropped_object = img[y_min:y_max, x_min:x_max] 
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            crop_output_path = f"./cropOutputImage/{timestamp}.jpg"
            cv2.imwrite(crop_output_path, cropped_object)
            print(f"Save {crop_output_path}")

            return crop_output_path
    return 2
        

def ocr(license_path) :
    if license_path :
        ocr = PaddleOCR(lang="korean")
        img_path = license_path

        result = ocr.ocr(img_path, cls=False)
        ocr_result = result[0]
        license_ocr = ''.join([item[1][0] for item in ocr_result])

        return license_ocr
    
    else :
        sys.exit(1)

def tts(voice_text) :
    if voice_text :
        result = []

        engine.setProperty('rate', 100) 
        engine.setProperty('volume', 1.0)  
        num_to_korean = {
            '0': '공', '1': '일', '2': '이', '3': '삼', '4': '사',
            '5': '오', '6': '육', '7': '칠', '8': '팔', '9': '구'
        }

        for i in voice_text :
            if i.isdigit():
                result.append(num_to_korean[i])
            else:  
                result.append(i)

        text = ''.join(result)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = f"/home/kimym/disabled_parking_system/savedNumber/carNumber_{timestamp}.mp3"
        # engine.save_to_file(text, path)
        try:
            engine.save_to_file(text, path)
            engine.runAndWait()
            print(f"파일이 성공적으로 저장되었습니다: {path}")
        except Exception as e:
            print(f"오류 발생: {e}")
        return path

    else :
        sys.exit(1)
