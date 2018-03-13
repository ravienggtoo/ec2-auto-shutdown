from __future__ import print_function
import boto3
import time
from datetime import datetime

def lambda_handler(event, context):

    ec2_client = boto3.client('ec2')
    ec2_response = ec2_client.describe_instances(Filters=[{'Name': 'tag:Product','Values': ['productname']},{'Name': 'instance-state-name','Values': ['running']}])
    print (ec2_response)
    for r in (ec2_response['Reservations']):
        for i in (r['Instances']):
            for t in  (i['Tags']):
                if (t['Key']=='role' and t['Value']=='proxy'):
                    proxy_server_id=(i['InstanceId'])
                elif (t['Key']=='role' and t['Value']=='app'):     
                    app_server_id=(i['InstanceId'])
    
    ssm_client = boto3.client('ssm')
    ssm_response = ssm_client.send_command(InstanceIds=[proxy_server_id],DocumentName='AWS-RunShellScript',Parameters={'commands': ["sed -n '/app/{s/\\(.*\\) localhost.*HTTP.*/\\1/;p}' /var/log/haproxy.log |tail -1"]})
    ssm_response_command_id = (ssm_response['Command']['CommandId'])
    print (ssm_response_command_id)
    time.sleep(5)
    ssm_response_command_output = ssm_client.get_command_invocation(CommandId=ssm_response_command_id,InstanceId=proxy_server_id)
    print (ssm_response_command_output['StandardOutputContent'])
    last_request = ssm_response_command_output['StandardOutputContent']
    print (last_request)
    last_request_time = datetime.strptime(last_request+str(datetime.now().year), "%b %d %H:%M:%S %Y")
    print (last_request_time)
    print ( datetime.now())
    
    time_diff = datetime.now() - last_request_time
    minutes_diff = ((time_diff.seconds)/60 )
    print ( minutes_diff ) 
    if (minutes_diff > 5):
        ssm_client.start_automation_execution(DocumentName='AWS-StopEC2Instance',Parameters={'InstanceId': [app_server_id]})
