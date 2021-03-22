from quantifin.equity import Stock
from jinja2 import Environment, FileSystemLoader
import sys
import util

if __name__ == "__main__":
    try:
        config_path = sys.argv[1]
    except IndexError as e:
        raise IndexError("Configuration file not provided")

    config = util.load_configuration(config_path)
    report_format = config.get("report_format")
    report_template = config.get("report_template")
    report_name =config.get("jupyter_report_name")
    s3_bucket = config.get("s3_bucket")
    s3_report_dir = config.get("s3_report_dir")
    
    s = Stock("D05.SI")

    report_name = f"{s.stock_code}-report.html"
    
    template = util.get_template("report_template.html")
    template_vars = {"title": "D05 REPORT", "stock_beta": s.beta}
    html_out = template.render(template_vars)
    util.dump_report(html_out, f"/tmp/{report_name}")

    util.upload_report_to_s3("/tmp/" + report_name, s3_bucket, s3_report_dir + "/" + report_name)


#TODO:
#Create config file for container handler.py
#Config file for bin
#Provision DynamoDB for server