import adal
import requests
from anytree import Node, RenderTree, PostOrderIter
from anytree.search import findall

tenant = "32e1d473-8f14-4bb4-acd6-f13a582ce37e"
#client_id = "fc7a0d8b-9049-4041-97b3-305805023667"
#client_secret = "LsYT4HBORWzz76wJdmvTvUy4iWuViEUvr+h2TTugvUY="
client_secret = "R3WCplXoznu9Q9gQ0XbaRdCJ7ijeCT3w7iTujPnu7v4="
client_id = '47303655-6171-431d-953c-877999219cc3'

username = "kaushalya@buzinessware.com"
password = "Dubai2018!"

authority = "https://login.microsoftonline.com/" + tenant
RESOURCE = "https://graph.microsoft.com"

#import ipdb; ipdb.set_trace()

context = adal.AuthenticationContext(authority)

# Use this for Client Credentials
token = context.acquire_token_with_client_credentials(RESOURCE, client_id, client_secret)


# Use this for Resource Owner Password Credentials (ROPC)
#token = context.acquire_token_with_username_password(RESOURCE, username, password, client_id);

graph_api_endpoint = 'https://graph.microsoft.com/v1.0{0}'

request_url = graph_api_endpoint.format('/users/shubham@buzinessware.com/mailFolders/?$top=10')
headers = {
    'User-Agent' : 'python_tutorial/1.0',
    'Authorization' : 'Bearer {0}'.format(token["accessToken"]),
    'Accept' : 'application/json',
    'Content-Type' : 'application/json'
}

response = requests.get(url = request_url, headers = headers)

mail_folders = response.json()

NODE_TREE = Node('root')

def add_account_to_dict(parent_name, child_name):
    global NODE_TREE
    p = findall(NODE_TREE, filter_=lambda node: node.name in (parent_name,))
    if p:
        Node(child_name, parent=p[0])
    else:
        Node(parent_name, parent=NODE_TREE)


def recuse(parent_name, folders):
    request_url = graph_api_endpoint.format('/users/shubham@buzinessware.com/mailFolders/%s/childFolders?$count=true' %(folders['id']))
    response = requests.get(url = request_url, headers = headers)
    response_data = response.json()
    top = response_data['@odata.count']
    if top != 0:
        request_url = graph_api_endpoint.format('/users/shubham@buzinessware.com/mailFolders/%s/childFolders?$top=%d' %(folders['id'], top))
        response = requests.get(url = request_url, headers = headers)
        child_data = response.json()

        if len(child_data['value']) ==0:
            add_account_to_dict(parent_name, child_data['displayName'])

        elif folders['childFolderCount'] >= 1 :
            for child in child_data['value']:
                #print('>>>>>>>>>>>>>>>child_data:  ', folders)
                #print('>>>>>>>>child::', child)
                add_account_to_dict(folders['displayName'], child['displayName'])
                recuse(child['displayName'], child)
    else:
        return


for folders in mail_folders['value']:
    #import ipdb; ipdb.set_trace()
    if folders['childFolderCount'] == 0:
        Node(folders['displayName'], parent=NODE_TREE)
    else:
        Node(folders['displayName'], parent=NODE_TREE)
        recurse_info = recuse(folders['displayName'], folders)
        #print("Recurse info:- ", recurse_info)

#import ipdb; ipdb.set_trace()
folders_list = []
for node in RenderTree(NODE_TREE):
    node_data =  str(node[2])
    split_node_data = node_data[5:-1]
    folder = split_node_data.strip("'")
    folder_list = folder.split('/')
    if len(folder_list) == 2 and folder_list[1] == 'root':
        continue
    else:
        folder_path = ('/').join(folder_list[2:])
        folders_list.append(folder_path)

for each in folders_list:
    print each
    print "\n"
#print(RenderTree(NODE_TREE))
