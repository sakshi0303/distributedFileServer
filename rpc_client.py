# XML-Remote Procedure call
import base64
from genericpath import isfile
import os
import argparse
import time
import threading
import logging
from xmlrpc.client import ServerProxy
from os.path import exists

# log setup
format = "CLIENT:%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

# proxy setup
proxy = ServerProxy('http://localhost:3000', verbose=False)
root_directory = os.path.dirname(os.path.abspath(__file__))
client_side_files_path = os.path.join(root_directory, "client_side_files")
polling_count = 0

# error messages
INVALID_FILETYPE_MSG = "Error: Invalid file format. %s must be a .txt file."
INVALID_PATH_MSG = "Error: Invalid file path/name. Path %s does not exist."

#----------------------------------------------------<PUBLIC FUNCTIONS>-----------------------------------------------------------------

def client_list_directory():
        clientFileList = []
        for root, directories, files in os.walk(client_side_files_path, topdown=False):
            for name in files:
                # ignore hidden files for ex: .DS_Store
                if name.startswith('.'):
                    continue
                file_path = os.path.join(root, name)
                base_path = file_path[file_path.rindex(
                    'client_side_files')+len("client_side_files/"):]
                clientFileList.append(base_path)
        return clientFileList

def list(args):
    # logging.infos all the files in the root server directory
    target = args.list[0]
    if target == "server":
        serverFileList = proxy.list_directory1()
        logging.info(serverFileList)
    elif target == "client":
        clientFileList = client_list_directory()
        logging.info(clientFileList)
    else:
        logging.info("Please pass correrct path type server/client")

def download(args):
    src = args.download[0]
    dst = args.download[1]
    logging.info(f"Received a download request for src:{src} and dst:{dst}")
    content = proxy.download(src)
    if(content == 'DownloadException'):
        logging.info("File not found on server side.")
    else:
        if(_createfile(content, dst)):
            logging.info(f"File successfully created on client side")
    
def upload(args):
    src = args.upload[0]
    dst = args.upload[1]
    logging.info(f"Received a upload request for src:{src} and dst:{dst}")

    src_full_path = os.path.join(client_side_files_path, src)
    if exists(src_full_path):
        file_src_obj = _buildMetaData(root_directory, src_full_path, False)
        file_src= _get_contents(src_full_path,file_src_obj)
        isUploadSuccessful = proxy.upload(file_src, dst)
        if isUploadSuccessful:
            print("upload successfull")
        else:
            print("upload un-successful. check source and destination path correctly")
    else:
        logging.info(f" File not found at {src_full_path} ")

def rename(args):
    old_filename = args.rename[0]
    new_filename = args.rename[1]
    if proxy.rename(old_filename, new_filename):
        logging.info(f"Successfully renamed {old_filename} to {new_filename}.")
    else:
        logging.info(f"File not found on server side at {old_filename} to {new_filename}.")
    
def delete(args):
    target_path = args.delete[0]
    if proxy.delete(target_path):        
        logging.info(f"Delete successfully on server side at {target_path}")
    else:
        logging.info(f"Delete failed. File not found on server side at {target_path}")
    

def sync(args):

    if not proxy.cleanup():
        logging.info("Server side cleanup didn't happened")

    sync_thread=threading.Thread(target=_startPollingThread)
    sync_thread.start()
    while(sync_thread.is_alive()):
        time.sleep(30)
        logging.info("Sync in progress")
    logging.info("Thread stopped, restart to create another thread")


#----------------------------------------------------<PRIVATE FUNCTIONS>-----------------------------------------------------------------

def _startPollingThread():
    global polling_count
    global proxy
    global client_side_files_path
    # the map in the previous polling
    currentDirectoryMap = {}

    path = client_side_files_path
    while True:
        polling_count += 1
        threadID = threading.current_thread().ident
        logging.debug("Thread ID : %s starting", threadID)
        
        newDirectoryMap = _buildMapOfDirectoryStructure(path)
        _synchronizeDirectories(currentDirectoryMap, newDirectoryMap)
        currentDirectoryMap = newDirectoryMap.copy()
        time.sleep(5)
        logging.debug("Thread ID : %s finishing", threadID)
        

def _buildMapOfDirectoryStructure(path):
    newDirectoryMap = {}
    for root, directories, files in os.walk(path, topdown=False):
        for name in files:
            # ignore hidden files for ex: .DS_Store
            if name.startswith('.'):
                continue            
            file_obj = _buildMetaData(root,name,False)
            file_path = os.path.join(root, name)
            newDirectoryMap[file_path] = file_obj

        for name in directories:
            file_obj = _buildMetaData(root,name,True)
            file_path = os.path.join(root, name)
            newDirectoryMap[file_path] = file_obj
    return newDirectoryMap


def _buildMetaData(root, name, isDirectory):
    file_obj = {
        'file_path': os.path.join(root, name),
        'filesize': os.path.getsize(os.path.join(root, name)),
        'file_created_timestamp': os.path.getctime(os.path.join(root, name)),
        'file_modified_timestamp': os.path.getmtime(os.path.join(root, name)),
        'Isdirectory': isDirectory
    }
    return file_obj

# scenario 1: look for keys which dont exits in the old map i.e new files
# scenerio 2: look for keys which exits in the old map and new map i.e no change to file path or name
# scenerio 3: look for keys which do not exists in new map and exits in old map i.e deleted files
def _synchronizeDirectories(currentDirectoryMap, newDirectoryMap):    
    for key in newDirectoryMap:
        if key not in currentDirectoryMap:            
            file_obj = _get_contents(key, newDirectoryMap[key])
            isUploadSuccessful = proxy.upload(file_obj, key)
            if isUploadSuccessful:
                logging.info(
                "new file uploaded with key : %s", key )            
        else:
            # remove matching keys from the old map since we only care about new or deleted files            
            # ignore folders with modified timestamps since we care about files only
            if not os.path.isfile(key):
                currentDirectoryMap.pop(key)
                continue

            currentTime = currentDirectoryMap[key]['file_modified_timestamp']
            newTime = newDirectoryMap[key]['file_modified_timestamp']
            time_delta = newTime - currentTime
            if (time_delta > 1):                                
                # delete the old file
                _get_contents(key, currentDirectoryMap[key])
                isDeleteSuccessful = proxy.delete(key)
                logging.info(f"Server side file deleted: {isDeleteSuccessful} with key : {key}", )

                # upload the new file
                file_objNew = _get_contents(key, newDirectoryMap[key])
                if isDeleteSuccessful:
                    isUploadSuccessful = proxy.upload(file_objNew, key)
                    logging.info(f"Server side file uploaded: {isUploadSuccessful} with key : {key}", )
            # these are files which are present in both the maps                     
            currentDirectoryMap.pop(key)

    # files present in the old map but not in new map i.e. deleted files
    for key in currentDirectoryMap:      
        isDeleteSuccessful = proxy.delete(key)
        logging.info(
            f"Server side file deleted with key : {key} ")


# this will work for small files ,need to improve for large files
def _get_contents(path, file_obj):
    if file_obj['Isdirectory']:
        return file_obj
    else:        
        text_file = open(path, "rb")
        data = text_file.read()
        text_file.close()
        file_obj['content'] = base64.b64encode(data)
        return file_obj


def _createfile(content, path):
    try:
        path = os.path.join(client_side_files_path, path)    
        if (not os.path.exists(path)):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as temp_file:
            temp_file.write(base64.b64decode(content.data))    
        return True
    except Exception as e:
        logging.info(f"Exception occured {e}")
        return False

#----------------------------------------------------<MAIN FUNCTION>-----------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A text file manager!")

    parser.add_argument("-l", "--list", type=str, nargs=1, metavar=('target'),help="\nList all contents of directory where target is server or client. Example: python3 rpc_client.py -l server")
    parser.add_argument("-s", "--sync", action="store_true",help="\nOne way Synchronize between client side folder to server side folder. Example: python3 rpc_client.py -s ")
    parser.add_argument("-r", "--rename", type=str, nargs=2,metavar=('old_name', 'new_name'), help="Renames the server specified file to a new name.Example: python3 rpc_client.py -r Folderrightnow/new1.txt Folderrightnow/new2.txt")
    parser.add_argument("-d", "--download", type=str, nargs=2,metavar=('src', 'dst'), help="download server side root content to client side.Example: python3 rpc_client.py -d Folderrightnow/new2.txt FolderXYZ/newxyz.txt  ")
    parser.add_argument("-del", "--delete", type=str, nargs=1,metavar=('target'), help=" delete server side file or folder.Example: python3 rpc_client.py -del Folderrightnow/new2.txt ")
    parser.add_argument("-u", "--upload", type=str, nargs=2,metavar=('src', 'dst'), help="upload files from client side to server side.Example: python3 rpc_client.py -u Folderrightnow/FolderX/sakshiupload.txt Folderrightnow/file1.py")
    
    args = parser.parse_args()
    
    # calling functions depending on type of argument
    if args.download is not None:
        download(args)
    elif args.rename is not None:
        rename(args)
    elif args.delete is not None:
        delete(args)
    elif args.upload is not None:
        upload(args)
    elif args.sync:
        sync(args)
    elif args.list is not None:
        list(args)
