from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('enhanced_coordinated_index.html')

@app.route('/test')
def test():
    return """
    <h1>Enhanced Template Test</h1>
    <p>If you can see this, the server is working.</p>
    <p>Check the main page at: <a href="/">Enhanced Traffic Control</a></p>
    """

if __name__ == '__main__':
    print("🚦 Test Server Running...")
    print("📱 Open browser to: http://127.0.0.1:5001")
    print("🔧 Test page: http://127.0.0.1:5001/test")
    app.run(host='127.0.0.1', port=5001, debug=False)
