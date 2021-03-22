import os
from boto3 import client
import yaml
from jinja2 import Environment, FileSystemLoader

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

def load_configuration(path):
    with open(path) as config_file:
        return yaml.full_load(config_file)