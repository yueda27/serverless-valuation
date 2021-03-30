import os
from boto3 import client, resource
import yaml
from jinja2 import Environment, FileSystemLoader
import logging
from finnhub import Client
from functools import total_ordering
import heapq
import copy

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
    logging.info("Successfully logged into finnhub")
    return c

def login_db(table_name):
    table = resource("dynamodb").Table(table_name)
    try:
        table.key_schema
    except Exception as e:
        raise Exception(f"Failed to connect to database: {str(e)}")
    logging.info(f"Successfully connected to database table:{table_name} ")
    return table

def rank_list_by_attr(table, attr, limit, max = True):
    resp = table.scan(Limit = limit)
    result = create_heap(resp.get("Items"), attr, max)
    expression = ">" if max else "<"

    while ("LastEvaluatedKey" in resp and resp.get("Count") >= 1):
        last_eval = resp.get("LastEvaluatedKey")
        cutoff = heapq.nsmallest(1, result)[0].get(attr)
        print(f"QUERY: {attr} {expression} {cutoff}" )
        resp = table.scan(FilterExpression = f"#attr {expression} :limit", ExpressionAttributeValues = {":limit" : cutoff}, ExpressionAttributeNames={"#attr": attr}, ExclusiveStartKey = last_eval)
        result = update_heap(result, resp["Items"], attr, max)
    return result
        

def create_heap(iterable, attr, max):
    result = []
    for i in iterable:
        heapq.heappush(result, CompareDict(attr, max,i))
    return result

def update_heap(result, new_iter, attr, max):
    result = copy.deepcopy(result)
    for i in new_iter:
        bottom = heapq.nsmallest(1, result)[0]
        i = CompareDict(attr, max, i)
        if (i > bottom) and (i not in result) :
            heapq.heappushpop(result, i)
    return result

@total_ordering
class CompareDict(dict):
    def __init__(self, key, max, *args, **kwargs):
        self.key = key
        self.max = max
        self.update(*args, **kwargs)
    
    def __eq__(self, other):
        return self.get("ticker") == other.get("ticker")
    
    def __lt__(self, other):
        if self.max:
            return self.get(self.key) < other.get(self.key)
        return self.get(self.key) > other.get(self.key)

#TODO:
# get most outdated stock from dynamodb to run valuation
# generic function to get list of stocks based on key
# dyanamodb client get