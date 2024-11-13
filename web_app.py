# app.py
from flask import Flask, request, jsonify, render_template
from web_chatbot import Chatbot  # Replace with your chatbot code
import os

app = Flask(__name__)
os.environ["TOGETHER_API_KEY"] = "61c3d30d6e3b2cc30504a65a11ddd0acb4d6e8912f32040d831c03285c51caa7"

# Initialize your chatbot with the API key
chatbot = Chatbot(api_key=os.environ["TOGETHER_API_KEY"])

# Route to serve the HTML page
@app.route("/")
def index():
    chatbot.clear_queue_and_prev_context()
    return render_template("index.html")  # Serves index.html from the templates folder

# Route to handle the chatbot API requests
@app.route("/chat", methods=["POST"])
def chat():
    user_query = request.json.get("message")
    response = chatbot.get_response(user_query)  
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)

