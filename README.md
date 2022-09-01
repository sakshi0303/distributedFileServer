Please follow the testing steps with screenshots in the report for Part 2 and 3. 
The below instructions are purely supplementary

Execution Steps after you have gone through the report:

> cd ProjectPart1           // run the below commands inside the project root directory
// Make sure "server_side_files" folder exists with same naming convention
// Make sure "client_side_files" folder exists with same naming convention
// Create sub Folders and files inside "client_side_files" folder manually
> python3 rpc_server.py              // it will say “Serving….” in the Terminal1
> python3 rpc_client.py -h           //  run this command on Terminal2
> python3 rpc_client.py -l client  
> python3 rpc_client.py -l server
> python3 rpc_client.py -u folder1/File1.txt File1upload.txt 
> python3 rpc_client.py -d File1upload.txt clientFile1upload.txt
> python3 rpc_client.py -r File1upload.txt File1uploadrename.txt
> python3 rpc_client.py -del File1uploadrename.txt
> python3 rpc_client.py -s