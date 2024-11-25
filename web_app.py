# app.py
from flask import Flask, request, jsonify, render_template
from web_chatbot_v4 import Chatbot 
import os

app = Flask(__name__)
os.environ["TOGETHER_API_KEY"] = "30cde163d78fa4c02d653ab94957386b6dcfb1c370e2a04c8678dc17197794e1"

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

