from flask import Flask, render_template

# template_folder='.' tells Flask to look in the current folder instead of /templates
app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
