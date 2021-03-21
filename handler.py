import json
from quantifin.equity import Stock
import os
from boto3 import client

def lambda_handler(event, context):
    s = Stock("D05.SI")
    print('writing to dir')
    print("Generating jupyter report")
    print(os.system("aws s3 ls s3://yueda-bucket"))
    run_jupyter("report.ipynb")
    print(os.system("ls /tmp"))
    upload_report_to_s3("/tmp/report.html", "yueda-bucket", "serverless-valuation/reports/report.html")
    return {
        "statusCode": 200,
        "body": "hello"
    }

def run_jupyter(file_path):
    os.system("jupyter nbconvert --output-dir '/tmp'  --to html report.ipynb")
    print("Finished writing to jupyter-notebook")

def upload_report_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    s3_client = client("s3")
    print(s3_client.list_objects(Bucket= bucket))
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except:
        print("ERROR UPLOADING!")

if __name__ == "__main__":
    print(lambda_handler("testing", "testing"))

#TODO:
#Create config file for container handler.py
#Config file for bin
#Provision DynamoDB for server