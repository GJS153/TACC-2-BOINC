#!/usr/bin/env python3

"""
BASICS

Cloud storage of files on the BOINC server for using local files
"""

import os, sys
from flask import Flask, request, jsonify, send_file
import preprocessing as pp
from werkzeug.utils import secure_filename
import redis
import requests



r = redis.Redis(host = '0.0.0.0', port = 6389, db =2)
app = Flask(__name__)
UPLOAD_FOLDER = "/root/project/api/sandbox_files"


# Checks if reef cloud storage is available
@app.route("/boincserver/v2/reef_status")
def api_operational():
    return 'reef cloud storage is available'


# Tutorial
@app.route("/boincserver/v2/reef_tutorial")
def tutorial():

    full = { 'Port': '5060',
             'Disaclaimer': 'API usage is restricted to those with an available token',
     'Steps': {'1': 'Create a sandbox directory (skip if already own one)',
               '2': 'Upload files one by one'
              },
     'Creating a directory': 'Use the following structure: curl -d token=TOKEN  http://SERVER_IP/boincserver/v2/create_sandbox',
     'Uploading files': 'Use syntax curl  -F file=@Example_multi_submit.txt http://SERVER_IP:5060/boincserver/v2/reef_upload/token=TOKEN'

    }
    return jsonify(full)
   

# Creates a sandbox directory, returns an error if the directory does not exist
@app.route('/boincserver/v2/create_sandbox', methods = ['GET', 'POST'])
def new_sandbox():
    
    
    if request.method != 'POST':
       return 'Invalid, provide a token'

    TOK = request.form['token']
    if pp.token_test(TOK) == False:
       return 'Invalid token'
    
    # Finds if the directory has already been created or not
    for sandir in os.listdir('/root/project/api/sandbox_files'):
        if TOK == sandir[4::]:
           return 'Sandbox already available'
    else:
        os.makedirs('/root/project/api/sandbox_files/DIR_'+str(TOK))
        os.makedirs('/root/project/api/sandbox_files/DIR_'+str(TOK)+'/___RESULTS')
        return 'reef cloud storage now available'


# Returns a string comma-separated, of all the files owned by a user
@app.route('/boincserver/v2/all_files/token=<toktok>')
def all_user_files(toktok):
    if pp.token_test(toktok) == False:
       return 'Invalid token'

    # Accounts for users without a sandbox yet
    try:
       AAA = []
       for afil in os.listdir('/root/project/api/sandbox_files/DIR_'+str(toktok)):

           AAA.append(afil)

       return ','.join(AAA)

    except:
       return 'Sandbox not set-up, create a sandbox first'


# Uploads one file, same syntax as for submitting batches of known commands
@app.route('/boincserver/v2/upload_reef/token=<toktok>', methods = ['GET', 'POST'])
def reef_upload(toktok):

   if pp.token_test(toktok) == False:
      return 'INVALID token'

   if request.method != 'POST':
      return 'INVALID, no file submitted'

   file = request.files['file']

   # Avoids errors with users with no sandbox assigned
   try:
      os.listdir('/root/project/api/sandbox_files/DIR_'+str(toktok))

   except:
   	  return 'INVALID, user sandbox is not set-up, create a sandbox first'

   # No user can have more than 2 Gb
   assigned_allocation = float(r.get(toktok).decode('UTF-8'))

   if pp.user_sandbox_size(str(toktok)) > (assigned_allocation*1073741824):
      return 'INVALID, User has exceded asssigned allocation. Max. available allocation is '+str(assigned_allocation)+' GB'

   # Avoids empty filenames and those with commas
   if file.filename == '':
      return 'INVALID, no file uploaded'
   if ',' in file.filename:
      return "INVALID, no ',' allowed in filenames"

   # Ensures no commands within the file
   new_name = secure_filename(file.filename)
   file.save(os.path.join(UPLOAD_FOLDER+'/DIR_'+str(toktok), new_name))
   return 'File succesfully uploaded to Reef'


# Allows to check the user's allocation status
@app.route('/boincserver/v2/reef_allocation_status/token=<toktok>')
def reef_allocation_status(toktok):
    if pp.token_test(toktok) == False:
       return 'Invalid token'
    used_space = pp.user_sandbox_size(str(toktok))/1073741824
    assigned_allocation = r.get(toktok).decode('UTF-8')
    all_info = {'Max. allocation': assigned_allocation+' GB',
                'Used space': str(used_space)+' GB', 
                'Space available left': str((1 - used_space/float(assigned_allocation))*100)+'% allocation available'}

    return jsonify(all_info)


# Deletes a file already present in the user
@app.route('/boincserver/v2/delete_file/token=<toktok>', methods = ['GET', 'POST'])
def delete_user_file(toktok):

   if pp.token_test(toktok) == False:
      return 'Invalid token'
   if request.method != 'POST':
      return 'Invalid, provide a file to be deleted'

   # Accounts for missing directories
   if str('DIR_'+toktok) not in os.listdir('/root/project/api/sandbox_files'):
      return 'User directory does not exist'
   try: 
      FILE = request.form['del']    
      if FILE == '':    
         return 'No file provided'     
      os.remove('/root/project/api/sandbox_files/DIR_'+str(toktok)+'/'+str(FILE))
      return 'File succesfully deleted from reef storage'

   except:
      return 'File is not present in Reef'


# Returns a file, able to be curl/wget
@app.route('/boincserver/v2/reef/<toktok>/<FIL>')
def obtain_file(FIL, toktok):

    if pp.token_test(toktok) == False:
       return 'Invalid token'
    if str('DIR_'+toktok) not in os.listdir('/root/project/api/sandbox_files'):
       return 'User directory does not exist'

    USER_DIR = '/root/project/api/sandbox_files/DIR_'+str(toktok)+'/'
    if str(FIL) not in os.listdir(USER_DIR):
       return 'File not available'

    return send_file(USER_DIR+str(FIL))


# Returns a list of all the files a user has in Reef results
@app.route("/boincserver/v2/reef_results_all/<toktok>")
def reef_results_all(toktok):
    if pp.token_test(toktok) == False:
       return 'Invalid token'
    if str('DIR_'+toktok) not in os.listdir('/root/project/api/sandbox_files'):
       return 'User directory does not exist'

    USER_DIR = '/root/project/api/sandbox_files/DIR_'+str(toktok)+'/___RESULTS'

    # Returns the results (space-separated)
    return ' '.join(os.listdir(USER_DIR))



# Returns an user's results file
@app.route('/boincserver/v2/reef/results/<toktok>/<FIL>')
def results_file(FIL, toktok):
    if pp.token_test(toktok) == False:
       return 'Invalid token'
    if str('DIR_'+toktok) not in os.listdir('/root/project/api/sandbox_files'):
       return 'User directory does not exist'

    USER_DIR = '/root/project/api/sandbox_files/DIR_'+str(toktok)+'/___RESULTS/'
    if str(FIL) not in os.listdir(USER_DIR):
       return 'File not available'

    return send_file(USER_DIR+str(FIL))


if __name__ == '__main__':
   app.run(host ='0.0.0.0', port = 5060)
