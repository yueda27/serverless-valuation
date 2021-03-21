import json
#from quantifin.equity import Stock
import os
from boto3 import client
import yaml
import sys

def lambda_handler(event, context):
    s = Stock("D05.SI")
    print('writing to dir')
    print("Generating jupyter report")
    # print(os.system("aws s3 ls s3://yueda-bucket"))
    # run_jupyter("report.ipynb")
    # print(os.system("ls /tmp"))
    # upload_report_to_s3("/tmp/report.html", "yueda-bucket", "serverless-valuation/reports/report.html")
    return {
        "statusCode": 200,
        "body": "hello"
    }

def run_jupyter(file_path, format, target_name):
    os.system(f"jupyter nbconvert --output-dir '/tmp'  --to {format} {file_path}")
    file_name = file_path.split("/")[-1].split(".")[0]
    os.system(f"mv /tmp/{file_name}.{format} /tmp/{target_name}")
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

def load_configuration(path):
    with open(path) as config_file:
        return yaml.full_load(config_file)

if __name__ == "__main__":
    try:
        config_path = sys.argv[1]
    except IndexError as e:
        raise IndexError("Configuration file not provided")

    config = load_configuration(config_path)
    jupyter_notebook = config.get("jupyter_notebook")
    report_format = config.get("report_format")
    report_name =config.get("jupyter_report_name")
    s3_bucket = config.get("s3_bucket")
    s3_report_dir = config.get("s3_report_dir")
    run_jupyter(jupyter_notebook, report_format, report_name)
    upload_report_to_s3("/tmp/" + report_name, s3_bucket, s3_report_dir + "/" + report_name)


#TODO:
#Create config file for container handler.py
#Config file for bin
#Provision DynamoDB for server