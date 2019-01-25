"""Configuration settings for console app using device flow authentication
"""
RESOURCE = "https://graph.microsoft.com"
TENANT = "32e1d473-8f14-4bb4-acd6-f13a582ce37e"  # Enter the tenant_id
AUTHORITY_HOST_URL = "https://login.microsoftonline.com/" # Authority URL for Access point
#CLIENT_ID= 'bf4cb5e9-7764-4201-855f-f409542fcdd1'  # copy the Application ID of your app from your Azure portal
CLIENT_ID= '6d6b6560-feaa-44b0-8cfa-6a5017e7fe11'
CLIENT_SECRET = "36Iq5oXtGuYAkDIBUS0wU2igakUuHG8duNM99qByxxo=" # copy the value of key you generated when setting up the application
#USERNAME = "admin@buzinesswarecom.onmicrosoft.com"  # Admin user cedentials for accesing the all users data of organisaion
#PASSWORD = "ZH6m?2u?1"
USERNAME = "kaushalya@buzinessware.com"
PASSWORD = "Dubai20191"
#USERNAME = "logs@buzinessware.com"
#PASSWORD = "Dubai2019"
# These settings are for the Microsoft Graph API Call
API_VERSION = 'v1.0'

#blob structure details
STORAGE_ACCOUNT_NAME = 'backupoffice365storage'
STORAGE_ACCOUNT_KEY = 'QQE7DLL+28U9DOf078imWcV4223QcQOj/XAw+rIAzms0bUqUHcSPPECeI33wxENHsbnb070qEhZ90ybVg1v9dQ=='
TENENT = 'buzinessware'

#specific user name just for test
User = "shubham@buzinessware.com"
