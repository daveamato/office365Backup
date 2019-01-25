import os
import datetime
from datetime import timedelta
import eventlet
import re
import config
import adal
import logging
import requests
from anytree import Node, RenderTree, PostOrderIter
from anytree.search import findall
from azure.storage.blob import BlockBlobService, ContentSettings
from azure.storage.blob import PublicAccess


logger = logging.getLogger('Backup-MsGraph')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class Backup_Email(object):

    global NODE_TREE
    NODE_TREE = Node('root')
    global token
    def __init__(self, resource, tenant, authority, client_secret, client_id, username, password,
                                api_verstion, storage_account_name, storage_account_key, container_name):
        self.resource = resource
        self.tenant = tenant
        self.authority = authority
        self.client_secret = client_secret
        self.client_id = client_id
        self.username = username
        self.password = password
        self.api_verstion = api_verstion
        self.storage_account_name = storage_account_name
        self.storage_account_key = storage_account_key
        self.container_name = container_name
        self.token = self.generate_token()

    def generate_token(self):
        logger.info("Generating token for Usage of MS-Graph")
        Authority_with_tenant = self.authority + self.tenant
        context = adal.AuthenticationContext(Authority_with_tenant)
        token = context.acquire_token_with_username_password(self.resource, self.username, self.password, self.client_id);
        logger.info("Token Generated Successfully")
        return token

    def refresh_token(self):
        logger.info("Refreshing token for Usage of MS-Graph")
        Authority_with_tenant = self.authority + self.tenant
        context = adal.AuthenticationContext(Authority_with_tenant)
        token = context.acquire_token_with_refresh_token(self.token['refreshToken'], self.client_id,
                                                                 self.resource, client_secret=None);
        logger.info("Token Refreshed successfully")
        return token


    def api_call(self, end_point):
        #import ipdb; ipdb.set_trace()
        graph_api_endpoint = 'https://graph.microsoft.com/'+config.API_VERSION+'{0}'
        request_url = graph_api_endpoint.format(end_point)
        headers = {
                'User-Agent' : 'python_tutorial/1.0',
                'Authorization' : 'Bearer {0}'.format(self.token["accessToken"]),
                'Accept' : 'application/json',
                'Content-Type' : 'application/json'
             }
        response = requests.get(url = request_url, headers = headers)
        return response.json()

    def check_user_avilablity(self):
        user_list = []
        Users = self.api_call('/users/')
        logger.info("Fetching all Users from Tenant of Office365 using MS-Graph")
        for each_user in Users['value']:
            user_list.append(each_user["userPrincipalName"])
        return user_list
        user_list = self.access_users()
        if config.User in user_list:
            logger.info("User has avilable in the database")
            return True
        else:
             logger.error("User is not avilabel")
      
    def create_block_blob_service(self):
        logger.info("Authenticate Azure Blob Service")
        blob_service = BlockBlobService(self.storage_account_name, self.storage_account_key)
        exists = False
        count = 0
        while not exists:
            exists = blob_service.exists(self.container_name)
            if not exists:
                count += 1
                if count == 1:
                    logger.info("Creating new Tenant On Azure Blob storage as %s" %(self.container_name))
                blob_service.create_container(self.container_name, public_access=PublicAccess.Container)
            else:
                logger.info("Tenant with Name %s already present on Azure Blob storage" %(self.container_name))
        return blob_service
    
    #NODE_TREE = Node('root')

    def add_account_to_dict(self, parent_name, child_name):
        #import ipdb; ipdb.set_trace()
        global NODE_TREE
        p = findall(NODE_TREE, filter_=lambda node: node.name in (parent_name,))
        if p:
            Node(child_name, parent=p[0])
        else:
            Node(parent_name, parent=NODE_TREE)

    def recurs(self, parent_name, folders):
        response_data = self.api_call('/users/'+config.User+'/mailFolders/%s/childFolders?$count=true'
                                                   %(folders['id']))
        top = response_data['@odata.count']
        if top != 0:
            child_data = self.api_call('/users/'+config.User+'/mailFolders/%s/childFolders?$top=%d'
                                                     %(folders['id'], top))
            if len(child_data['value']) == 0:
                self.add_account_to_dict(parent_name, child_data['displayName'])

            elif folders['childFolderCount'] >= 1:
                for child in child_data['value']:
                    self.add_account_to_dict(folders['displayName'], child['displayName'])
                    self.recurs(child['displayName'], child)
        else:
            return

    def fetch_user_folder(self):
        if (self.check_user_avilablity()):
            logger.info("fetching mail folders of User:- %s" %(config.User))
            folder = self.api_call('/users/'+config.User+'/mailFolders?$count=true')
            top = folder['@odata.count' ]
            all_parent_folder = self.api_call('/users/'+config.User+'/mailFolders/?$top='+str(top)+'')
            for folders in all_parent_folder['value']:
                if folders['childFolderCount'] == 0:
                    Node(folders['displayName'], parent=NODE_TREE)
                else:
                    Node(folders['displayName'], parent=NODE_TREE)
                    recurse_info = self.recurs(folders['displayName'], folders)
 
            #print (RenderTree(NODE_TREE))
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

            #logger.info("Folder_list:- %s" %(folders_list))
            logger.info("Mail-box fetched successfully")
            return folders_list

    def get_id_by_recurse(self, folder_id):
        response = self.api_call('/users/'+config.User+'/mailFolders/'+folder_id+'/''childFolders/')
        return response

    def fetch_folders_id(self):
        #import ipdb; ipdb.set_trace()
        folder_with_id = {}
        folders = self.fetch_user_folder()
        logger.info("Fetching mailbox folders Id...")
        for each_folder in folders:
            split_folder = each_folder.split('/')
            if len(split_folder) == 1:
                parent_folder = split_folder[0].replace(" ", "")
                response = self.api_call('/users/'+config.User+'/mailFolders/'+parent_folder+'/')
                folder_with_id[each_folder] = response['id']
            else:
                response = self.api_call('/users/'+config.User+'/mailFolders/'+split_folder[0].replace(" ", "")+'/')
                folder_id = response['id']
                for index, split_each_folder in enumerate(split_folder):
                    if index == 0:
                        continue
                    else:
                        data = self.get_id_by_recurse(folder_id)
                        for child_folder in data['value']:
                            if child_folder['displayName'] == split_each_folder:
                                folder_id = child_folder['id']
                                break
                folder_with_id[each_folder] = folder_id
        logger.info("mailbox folders Id fetched successfully.")
        return folder_with_id

    def get_messages(self, folder_id, top, skip):
        with eventlet.Timeout(300):
            response = self.api_call('/users/'+config.User+'/mailFolders/'+folder_id+'/messages?$top='
                                                                           +str(top)+'&$skip='+str(skip)+'')
        return response


    def backup_process(self):
        #import ipdb; ipdb.set_trace()
        all_folders_with_id = self.fetch_folders_id()
        blob_service = self.create_block_blob_service()
        blob_name = re.sub('[^A-Za-z0-9]+', '-', config.User).lower()
        logger.info("Processing on taking backup...")
        for folder_name, folder_id in all_folders_with_id.iteritems():
            logger.info("Taking backup on folder:- %s" %(folder_name))
            response = self.api_call('/users/'+config.User+'/mailFolders/'+folder_id+'/')
            mail_count = response['totalItemCount']
            copy_count = 0
            msg = 0
            if mail_count == 0:
                blob_service.create_blob_from_text(self.container_name,''+blob_name+'/'+folder_name+'/None', b'folder is empty',
                                                                 content_settings=ContentSettings('text'))
            while copy_count < mail_count:
                try:
                    response = self.get_messages(folder_id, mail_count, copy_count)
                    for each_message in response['value']:
                        msg += 1
                        blob_service.create_blob_from_text(self.container_name,
                                                           ''+blob_name+'/'+folder_name+'/'+str(each_message['createdDateTime']+'-'+
                                                           each_message['id'])+'',b''+str(each_message)+'',
                                                           content_settings=ContentSettings('text'))
                        logger.info("copyed mail count:- %d" %(msg))
                    copy_count += 1000
                except Exception as e:
                    if response['error']['code'] == 'InvalidAuthenticationToken':
                        logger.info("Token gets expiered refreshing token...")
                        self.token = self.refresh_token()
                        logger.info("Token gets refreshed successfully.")
            logger.info("maibox %s backup completed" %(folder_name))

    def incremental_backup_process(self, user):
	#import ipdb; ipdb.set_trace()
        folders = {}
        all_folders_with_id = self.fetch_folders_id()
        blob_service = self.create_block_blob_service()
        blob_name = re.sub('[^A-Za-z0-9]+', '-', config.User).lower()
        folders_data = blob_service.list_blobs(self.container_name, delimiter = 'shubham-buzinessware-com/')
        for folder_name, folder_id in all_folders_with_id.iteritems():
            logger.info("Taking backup on folder:- %s" %(folder_name))
            response = self.api_call('/users/'+config.User+'/mailFolders/'+folder_id+'/')
            mail_count = response['totalItemCount']
            copy_count = 0
            msg = 0
            if mail_count == 0:
                blob_service.create_blob_from_text(self.container_name,''+blob_name+'/'+folder_name+'/None', b'folder is empty',
                                                                 content_settings=ContentSettings('text'))
            while (copy_count < mail_count):
                try:
                    response = self.get_messages(folder_id, mail_count, copy_count)
                    for each_message in response['value']:
                        msg += 1
                        yesteday = (datetime.datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
                        date = each_message['createdDateTime'].split('T')
                        #if date[0] >= yesteday:
                        #    import ipdb; ipdb.set_trace()
                        #    blob_service.create_blob_from_text(self.container_name,
                        #                                       ''+blob_name+'/'+folder_name+'/'+str(each_message['createdDateTime']+'-'+
                        #                                       each_message['id'])+'',b''+str(each_message)+'',
                        #
                        new_id = each_message['createdDateTime'] + '-' + each_message['id']
                        blob = blob_service.list_blobs(self.container_name,prefix=(('%s/%s/%s')
                                                           %(blob_name, folder_name, new_id)))
                        if len(blob.items) == 0:
                            import ipdb; ipdb.set_trace()
                            blob_service.create_blob_from_text(self.container_name,
                                              ''+blob_name+'/'+folder_name+'/'+str(each_message['createdDateTime']+'-'+
                                              each_message['id'])+'',b''+str(each_message)+'',
                                              content_settings=ContentSettings('text'))
                        else:
                            copy_count = mail_count + 1
                            break
                        logger.info("copyed mail count:- %d" %(msg))
                    copy_count += 1000
                except Exception as e:
                    if response['error']['code'] == 'InvalidAuthenticationToken':
                        logger.info("Token gets expiered refreshing token...")
                        self.token = self.refresh_token()
                        logger.info("Token gets refreshed successfully.")
            logger.info("maibox %s backup completed" %(folder_name))
             

    def check_user_on_azure_tenant(self):
        #import ipdb; ipdb.set_trace()
	logger.info("Identifying the user backup availability on Azure storage")
        user_already_exist = False
        blob_service = self.create_block_blob_service()
        generator = blob_service.list_blobs(self.container_name, delimiter='/')
        user = re.sub('[^A-Za-z0-9]+', '-', config.User).lower()
        logger.info("Identify %s user backup on Azure Blob" %(config.User))
        for user_name in generator:
            if user in user_name.name:
                user_already_exist = True
        
        if user_already_exist:
            self.incremental_backup_process(user)
        else:
            self.backup_process()
        
        
if __name__ == "__main__":
    #import ipdb; ipdb.set_trace()
    resource = config.RESOURCE
    tenant = config.TENANT
    authority = config.AUTHORITY_HOST_URL
    client_secret = config.CLIENT_SECRET
    client_id = config.CLIENT_ID
    username = config.USERNAME
    password = config.PASSWORD
    api_verstion = config.API_VERSION
    storage_account_name = config.STORAGE_ACCOUNT_NAME
    storage_account_key = config.STORAGE_ACCOUNT_KEY
    contener_name = config.TENENT
    org = Backup_Email(resource, tenant, authority, client_secret, client_id, username, password, api_verstion,
                       storage_account_name, storage_account_key, contener_name)
    org.check_user_on_azure_tenant()
