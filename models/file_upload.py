from werkzeug.utils import secure_filename
from flask import redirect, render_template
import os

class FileUpload(object):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    
    def __init__(self, folder, request):
        self.request = request
        self.upload_folder = folder
        
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def handle_file_request(self):
        # check if the post request has the file part
        if 'file' not in self.request.files:
            return {
                "error": "No file part, does your form contain a files part?"
            }
        upload_file = self.request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if upload_file.filename == '':
            return {
                "error": "No file selected, have you selected a file?"
            }
        if not self.allowed_file(upload_file.filename):
            return {
                "error": "{} doesn't have an allowed filetype. Allowed types are: {}".format(upload_file.filename, ", ".join(list(self.ALLOWED_EXTENSIONS)))
            }
        if upload_file:
            filename = secure_filename(upload_file.filename)
            upload_file.save(os.path.join(self.upload_folder, filename))
            return { "msg": "File is successfully uploaded." }
        return redirect(self.request.url)

            