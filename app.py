from flask import Flask, render_template, request

# template_folder='.' keeps index.html side-by-side with app.py
app = Flask(__name__, template_folder='.')


@app.route('/pay')
def pay():
    # Capture the 'amt' parameter from the URL (e.g., /pay?amt=1500)
    # Default to '0.00' if it doesn't exist
    amount_due = request.args.get('amt', '0.00')

    # Pass the amount into your index.html template
    return render_template('login.html', amount_due=amount_due)

@app.route('/index')
def index():
    # Serves the index page when the JavaScript redirect triggers
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Using port 80 to match your QR URL structure