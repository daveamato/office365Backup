from msrestazure.azure_active_directory import AADTokenCredentials
from azure.mgmt.datalake.analytics.job import DataLakeAnalyticsJobManagementClient
from azure.mgmt.datalake.analytics.job.models import JobInformation, JobState, USqlJobProperties
import adal, uuid, time

import ipdb; ipdb.set_trace()

authority_host_uri = 'https://login.microsoftonline.com'

username = 'admin@buzinesswarecom.onmicrosoft.com'

password = 'ZH6m?2u?1'

tenant = '8fc29e84-727f-4c5d-adbd-f5d4eab792a0'

#tenant = '32e1d473-8f14-4bb4-acd6-f13a582ce37e'

authority_uri = authority_host_uri + '/' + tenant

resource_uri = 'https://graph.microsoft.com'

client_id = 'bf4cb5e9-7764-4201-855f-f409542fcdd1'

context = adal.AuthenticationContext(authority_uri, api_version=None)

token = context.acquire_token_with_username_password(resource_uri, username, password, client_id);

