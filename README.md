Please follow the testing steps with screenshots in the report for Part 2 and 3. <br/>
The below instructions are purely supplementary <br/>

Execution Steps after you have gone through the report: <br/>

> cd ProjectPart1           // run the below commands inside the project root directory <br/>
// Make sure "server_side_files" folder exists with same naming convention <br/>
// Make sure "client_side_files" folder exists with same naming convention <br/>
// Create sub Folders and files inside "client_side_files" folder manually <br/>
> python3 rpc_server.py              // it will say “Serving….” in the Terminal1 <br/>
> python3 rpc_client.py -h           //  run this command on Terminal2 <br/>
> python3 rpc_client.py -l client  <br/>
> python3 rpc_client.py -l server   <br/>
> python3 rpc_client.py -u folder1/File1.txt File1upload.txt  <br/>
> python3 rpc_client.py -d File1upload.txt clientFile1upload.txt <br/>
> python3 rpc_client.py -r File1upload.txt File1uploadrename.txt <br/>
> python3 rpc_client.py -del File1uploadrename.txt <br/>
> python3 rpc_client.py -s <br/>
