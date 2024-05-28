from flask import Flask, request, jsonify
import re
import requests
from flask_cors import CORS
from nltk.stem import PorterStemmer

app = Flask(__name__)
CORS(app)

# Initialize the stemmer
stemmer = PorterStemmer()

# Preprocess mapping values for easier matching
def preprocess_mapping(mapping):
    stemmed_mapping = {}
    for key, values in mapping.items():
        stemmed_mapping[key] = set(stemmer.stem(word) for word in values)
    return stemmed_mapping

mapping = {
    "title": ["Profit","interview", "preparation", "negotiation", "selling", "convincing", "opportunities","business"],
    "language": ["english", "hindi"],
    "content type": ["video", "course", "article", "book"]
}
# Preprocess the mapping to stem the keywords
stemmed_mapping = preprocess_mapping(mapping)

def extract_keywords(query):
    print("Extracting keywords from query:", query)
    query = query.lower()
    
    output = {
        "title": None,
        "language": None,
        "content type": None
    }
    
    words = re.findall(r'\w+', query)
    
    for word in words:
        stemmed_word = stemmer.stem(word)
        for key, values in stemmed_mapping.items():
            if stemmed_word in values:
                output[key] = word
    
    # Remove keys with None values
    output = {k: v for k, v in output.items() if v is not None}
    
    print("Extracted keywords:", output)
    return output

@app.route('/process', methods=['POST'])
def process_query():
    print("Received request to /process endpoint")
    data = request.json
    print("Request data:", data)
    query = data.get('query', '')
    extracted_keywords = extract_keywords(query)
    
    # Ensure there is something to send to the Node.js server
    if not extracted_keywords:
        return jsonify({
            "status": "error",
            "message": "No valid keywords extracted"
        }), 400

    # Send the extracted keywords to the Node.js server
    node_server_url = "http://127.0.0.1:3000/search"  # Update this URL to match your Node.js server
    try:
        response = requests.post(node_server_url, json=extracted_keywords)
        response.raise_for_status()  # Raise an HTTPError on bad status
        node_response = response.json()
        print("Response from Node.js server:", node_response)
    except requests.exceptions.RequestException as e:
        node_response = {"error": str(e)}
        print("Error communicating with Node.js server:", e)
    
    return jsonify({
        "status": "success" if "error" not in node_response else "error",
        "data": extracted_keywords,
        "node_response": node_response
    })

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)
