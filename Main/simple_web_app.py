from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Traffic System Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; background: #1e3c72; color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; }
            .success { color: #4CAF50; }
            .info { color: #2196F3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚦 Smart Traffic Light Control System</h1>
            <div class="status">
                <h2 class="success">✅ Web Server is Running!</h2>
                <p>The Flask application is successfully serving on localhost.</p>
                <p class="info">Current URL: <script>document.write(window.location.href)</script></p>
            </div>
            
            <div class="status">
                <h3>System Information:</h3>
                <ul>
                    <li>Server: Flask</li>
                    <li>Port: 5000</li>
                    <li>Status: Active</li>
                </ul>
            </div>
            
            <div class="status">
                <h3>Next Steps:</h3>
                <p>1. The basic web server is working</p>
                <p>2. We'll now add the full traffic analysis features</p>
                <p>3. Check console for any error messages</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    """Test endpoint"""
    return jsonify({'status': 'success', 'message': 'Server is working!'})

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Open your browser and go to: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
