import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# 각 카테고리별 이미지 경로
outputImage_path = '/home/kimym/disabled_parking_system/outputImage'
savedImage_path = '/home/kimym/disabled_parking_system/savedImage'

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/illegal')
def illegal_page():
    image_files = os.listdir(outputImage_path)
    return render_template('illegal.html', images=image_files, folder='outputImage')

@app.route('/disabled')
def disabled_page():
    image_files = os.listdir(savedImage_path)
    return render_template('disabled.html', images=image_files, folder='savedImage')

@app.route('/view/<folder>/<filename>')
def view_image(folder, filename):
    return render_template('view.html', folder=folder, filename=filename)

@app.route('/images/<folder>/<path:filename>')
def images(folder, filename):
    if folder == 'savedImage':
        return send_from_directory(savedImage_path, filename)
    elif folder == 'outputImage':
        return send_from_directory(outputImage_path, filename)
    else:
        return "Invalid folder", 404

if __name__ == '__main__':
    app.run(debug=True)
