from flask import Flask, request, render_template
import os

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/upload', methods=['POST'])
def file_upload():
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(app.instance_path, 'upload', f.filename))


@app.route('/download')
def result_download():
    pass


if __name__ == '__main__':
    app.run()
