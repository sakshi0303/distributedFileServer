# to do-
# add try catch for each operation
# make the server multithreaded
# class SimpleThreaded
from ast import Pass
import base64
import shutil
from xmlrpc.server import SimpleXMLRPCServer
import os
import logging
from socketserver import ThreadingMixIn

#Multithreading
class SimpleThreadedXMLRPCServer(ThreadingMixIn,SimpleXMLRPCServer):
    pass

server = SimpleThreadedXMLRPCServer(
    ('localhost', 3000), logRequests=True, allow_none=True)
server_root = os.path.dirname(os.path.abspath(__file__))
server_folder = os.path.join(server_root, "server_side_files")

format = "SERVER:%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")


class FileServer:

    #----------------------------------------------------<PUBLIC FUNCTIONS>-----------------------------------------------------------------

    def list_directory1(self):
        serverFileList = []
        for root, directories, files in os.walk(server_folder, topdown=False):
            for name in files:
                # ignore hidden files for ex: .DS_Store
                if name.startswith('.'):
                    continue
                file_path = os.path.join(root, name)
                logging.info("file_path="+file_path)
                logging.info(f"server_folder{server_folder}")

                base_path = file_path[file_path.rindex(
                    'server_side_files')+len("server_side_files/"):]
                logging.info(base_path)
                logging.info(f"base_path : {base_path}")
                #logging.info("name:%s and base_path:%s and filepath: %s and isdirectory: %s ",name, base_path, file_path)
                serverFileList.append(base_path)
        return serverFileList


    def download(self, path):
        # return content of the server file
        try:
            src_download_path = os.path.join(server_folder, path)
            logging.info(
                f"Received a download request with path:{path} and src_download_path:{src_download_path}")
            content = self._get_contents(src_download_path)
            # take the content and return it
            return content
        except Exception as e:
            return "DownloadException"

    
    def rename(self, old_filename, new_filename):
        try:
            server_full_rename_old_filepath = os.path.join(
                server_folder, old_filename)
            server_full_rename_new_filepath = os.path.join(
                server_folder, new_filename)

            logging.info(
                f"Received an server rename request from {server_full_rename_old_filepath} to {server_full_rename_new_filepath}")

        
            os.rename(server_full_rename_old_filepath,
                      server_full_rename_new_filepath)
            logging.info("Source path renamed to destination path successfully.")
            return True
        except OSError as error:
            logging.info(error)
            return False



    def upload(self, file_obj, path):
        # create new file on the server
        try:
            target="client_side_files"
            if target in path:                
                upload_path = path.split("client_side_files/", 1)[1]
                full_upload_path = os.path.join(server_folder, upload_path)                
            else:
                full_upload_path = os.path.join(server_folder, path)

            logging.info(f"Received an upload request at path:{full_upload_path}")

            if (file_obj['Isdirectory']) and (not os.path.exists(full_upload_path)):
                os.makedirs(full_upload_path)
                logging.debug(
                    "Directory made without content at path: %s", full_upload_path)
                return False
            elif file_obj['Isdirectory']:
                logging.debug(
                    f"Directory already existed when the client started {full_upload_path}")
                return False
            self._createfile(file_obj, full_upload_path)
            return True
        except Exception as e:
            logging.info(f"exception occured {e}")
            return False


    def cleanup(self):        
        for filename in os.listdir(server_folder):
            file_path = os.path.join(server_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logging.info(f"failed to delete {file_path} with exception {e}")
                return False
        return True                

    def delete(self, path):
        try:
            substring="client_side_files"

            if(substring in path):
                delete_path = path.split("client_side_files/", 1)[1]
            else:
                delete_path = path

            full_delete_path = os.path.join(server_folder, delete_path)
            logging.info(
                f"Received an delete request at path:{full_delete_path}")
        
            if os.path.isfile(full_delete_path):
                os.remove(full_delete_path)
            else:
                logging.info(
                    f"Deleting directories at full path: {full_delete_path} and path: {path}")                
                shutil.rmtree(full_delete_path)
            logging.info("# deleted at path:%s", full_delete_path)
            return True
        except OSError as e:
            logging.info("Error: %s : %s" % (full_delete_path, e.strerror))
            return False

#----------------------------------------------------<PRIVATE FUNCTIONS>-----------------------------------------------------------------


    def _createfile(self, file_obj, full_upload_path):
        base_path = full_upload_path[:full_upload_path.rindex('/')]
        content = file_obj['content']
        if (not os.path.exists(base_path)):
            os.makedirs(os.path.dirname(full_upload_path), exist_ok=True)

        with open(full_upload_path, 'wb') as temp_file:
            temp_file.write(base64.b64decode(content.data))
        return True

    def _get_contents(self, path):
        text_file = open(path, "rb")
        data = text_file.read()
        text_file.close()
        return base64.b64encode(data)


server.register_instance(FileServer())

#----------------------------------------------------<MAIN FUNCTION>-----------------------------------------------------------------

if __name__ == '__main__':

    try:
        logging.info('Serving ..')
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Exiting')
