import os
from boto3 import client
import yaml
from jinja2 import Environment, FileSystemLoader
import logging
from finnhub import Client

def get_template(template_path):
    env = Environment(loader=FileSystemLoader('.'))
    return env.get_template("report_template.html")

def dump_report(output_string, path):
    with open(path, "w") as f:
        f.write(output_string)


def upload_report_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    s3_client = client("s3")
    print(s3_client.list_objects(Bucket= bucket))
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except:
        print("ERROR UPLOADING!")
    logging.debug(f"Uploaded {file_name} to S3://{bucket}/{object_name}")

def load_configuration(path):
    with open(path) as config_file:
        return yaml.full_load(config_file)
        
def convert_to_pct(val):
    return round(val * 100, 3)

def login_finnhub(path):
    try:
        with open(path) as f:
            API_KEY = f.read()
        c = Client(api_key= API_KEY)
        c.country() #Test API KEY validity
    except Exception as e:
        raise Exception(f"Failed to login to Finnhub: {str(e)}")
    return c