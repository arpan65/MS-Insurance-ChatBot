from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

@app.route('/filenote/', methods=['GET', 'POST'])
def create_filenote():
    claimId = request.args.get('claimId')
    return jsonify({
    "fileNoteId": "571905A779222880",
    "noteId": "D6F11BBF2FE27286",
    "action": [
        {
            "id": "Act",
            "description": "Action",
            "caption": "Action",
            "contentType": "application/json",
            "methods": [
                {
                    "type": "GET",
                    "uri": "api/v1/fileNotes/571905A779222880/notes/D6F11BBF2FE27286"
                }
            ]
        }
    ]
    })
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=105)