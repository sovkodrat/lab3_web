from flask import Flask, render_template, request, abort, send_from_directory
# Импортируем необходимые модули из библиотеки Flask для создания веб-приложения
import uvicorn
from PIL import Image, ImageDraw, ImageEnhance, ImageOps
# Импортируем модули из библиотеки PIL (Python Imaging Library) для работы с изображениями

import matplotlib.pyplot as plt
import numpy as np
import requests
import os
import base64
# Импортируем необходимые модули для работы с графиками, массивами, отправкой запросов, операционной системой и кодированием Base64

import matplotlib
matplotlib.use('agg')

app = Flask(__name__)
# Создаем экземпляр класса Flask для создания веб-приложения

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB limit for uploaded files
# Устанавливаем ограничение размера загружаемых файлов в 1 МБ

UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Устанавливаем папку для сохранения загруженных файлов

RECAPTCHA_SITE_KEY = '6LdlLBAmAAAAADEkPEp1BIl_lbDYwzeE_n6lkhBt'
# Устанавливаем ключ сайта reCAPTCHA

@app.route('/mywork', methods=['POST'])
# Создаем маршрут для обработки POST-запроса на /mywork
def transform():
    file = request.files.get('file')
    new_size = (int(request.form.get('cross_x')), int(request.form.get('cross_y')))
    # Получаем загруженный файл и новый размер из параметров POST-запроса

    if not file:
        abort(400, 'No file was uploaded')
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        abort(400, 'File is not an image')
    # Проверяем, был ли загружен файл, и является ли он изображением (форматы PNG, JPG, JPEG или GIF)

    recaptcha_response = request.form.get('g-recaptcha-response')
    if not recaptcha_response:
        abort(400, 'reCAPTCHA verification failed')
    payload = {
        'secret': '6LdlLBAmAAAAABbqK-N4kGXshV9m_96TNR9Ka6ER',
        'response': recaptcha_response
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', payload).json()
    if not response['success']:
        abort(400, 'reCAPTCHA verification failed')
    # Проверяем результаты reCAPTCHA, чтобы удостовериться, что пользователь не является ботом

    img = Image.open(file)
    transformed_img = img.resize(new_size)
    # Открываем изображение и изменяем его размер

    img_width, img_height = img.size
    # Получаем ширину и высоту исходного изображения

    orig_colors = get_color_distribution(img)
    transformed_colors = get_color_distribution(transformed_img)
    # Получаем данные о распределении цветов в исходном и измененном изображениях

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Color Distribution')
    # Создаем график с двумя подграфиками для отображения распределения цветов

    ax1.plot(np.arange(len(orig_colors)), [c[0] / 255 for c in orig_colors], color='blue')
    ax1.set_xticks(np.arange(len(orig_colors)))
    ax1.set_xticklabels([c[1] for c in orig_colors], rotation=45)
    ax1.set_title('Original Image')
    # Создаем график для исходного изображения

    ax2.plot(np.arange(len(transformed_colors)), [c[0] / 255 for c in transformed_colors], color='red')
    ax2.set_xticks(np.arange(len(transformed_colors)))
    ax2.set_xticklabels([c[1] for c in transformed_colors], rotation=45)
    ax2.set_title('Transformed Image')
    # Создаем график для измененного изображения

    plt.tight_layout()
    plot_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
    plt.savefig(plot_filename)
    transformed_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'transformed.png')
    transformed_img.save(transformed_filename)
    orig_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'orig.png')
    img.save(orig_filename)
    # Сохраняем график и оба изображения на сервере

    result_filename = os.path.basename(plot_filename)
    with open(plot_filename, 'rb') as f:
        plot_bytes = f.read()

    plot_base64 = base64.b64encode(plot_bytes).decode('utf-8')
    # Кодируем график в формат Base64 для встраивания в HTML-страницу

    return render_template('result.html', orig=orig_filename, plot=plot_base64, result_filename=result_filename,
                           width=img_width, height=img_height)
    # Отправляем HTML-страницу с результатами обработки изображения

@app.route('/', methods=['GET'])
# Создаем маршрут для обработки GET-запроса на корневой URL
def index():
    return render_template('index.html', sitekey=RECAPTCHA_SITE_KEY)
    # Отправляем HTML-страницу с формой загрузки файла и reCAPTCHA

def get_color_distribution(img):
    colors = img.getcolors(img.size[0] * img.size[1])
    return sorted(colors, key=lambda x: x[0], reverse=True)[:10]
    # Получаем распределение цветов на изображении и возвращаем наиболее популярные 10 цветов

@app.route('/uploads/<filename>')
# Создаем маршрут для обработки запроса на получение загруженного файла
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    # Отправляем загруженный файл из папки uploads

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
    # Запускаем веб-приложение на локальном сервере