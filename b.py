# This script will listen on port 80 to /metadata GET requests and provide a full metadata response including all nested keys

from http.server import BaseHTTPRequestHandler
import socketserver
import json
import requests

# Generic function to perform a GET request with a token
def get_request(url, token):
        return requests.get(url,
                            headers={
                                "X-aws-ec2-metadata-token": token
                            }
                            ).text

# Function which returns a response for IMDSv2 token
def get_token():
    print("inside get_token")
    return requests.put("http://169.254.169.254/latest/api/token",
                 headers={
                     "X-aws-ec2-metadata-token-ttl-seconds": "21600"
                 }).text

# Recursion of the metadata keys and nested keys in order to provide all the data available by EC2 metadata server.
def get_all_metadata_items(metadata_keys, url, token):
    metadata_object = {}
    for item in metadata_keys:
        result = get_request(f"{url}/{item}", token)
        print(f"item: {item}, result: {result}")
        if "/" in item:
            metadata_object[item.replace('/', '')] = get_all_metadata_items(result.split('\n'), f"{url}/{item}", token)
        else:
            metadata_object[item] = result
        
    return metadata_object

# Function which invokes the get_token() and the get_all_metadata_items() functions in order to provide the metadata.
def get_metadata():
    token = get_token()
    metadata_keys = list(filter(None, get_request("http://169.254.169.254/latest/meta-data/", token).split('\n')))
    metadata_object = get_all_metadata_items(metadata_keys, "http://169.254.169.254/latest/meta-data/", token)
    return metadata_object

# Custom handler for the /metadata location for the http server.
class CustomHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metadata":
            # Respond with custom metadata
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            metadata = get_metadata()
            self.wfile.write(json.dumps(metadata).encode())
        else:
            # Respond with a 404 error for other paths
            self.send_error(404, "Not Found")

port = 8081
httpd = socketserver.TCPServer(("", port), CustomHandler)
httpd.allow_reuse_address = True
print(f"Server is listening on {port}")
httpd.serve_forever()