from quantifin.equity import Stock
from quantifin.util import RiskFree
from quantifin.util.markets import Market
from quantifin.equity.valuation import *
from jinja2 import Environment, FileSystemLoader
import sys
import util
import logging
from datetime import datetime

def gordon_growth(stock, req_return):
    if req_return < 0:
        req_return = 0.05
        logging.info("Required Rate Of Return Negative. Defaulting to 0.05")
    result = list()
    result.append(("Required Rate Of Return", round(req_return, 3)))
    growth_rate = stock.growth_rate()
    print(req_return)
    value = gordon_growth_valuation(stock.full_year_dividend(), req_return, growth_rate)
    result.append(("Valuation", value))
    return result



if __name__ == "__main__":
    logging.basicConfig(level = logging.DEBUG )
    try:
        config_path = sys.argv[1]
    except IndexError as e:
        raise IndexError("Configuration file not provided")

    config = util.load_configuration(config_path)
    report_template = config.get("report_template")
    s3_bucket = config.get("s3_bucket")
    s3_report_dir = config.get("s3_report_dir")
    logging.info(f"""Initialised application
    Using following configurations: S3 Bucket: {s3_bucket}  S3 Report Dir: {s3_report_dir} Report template: {report_template}""")
    
    s = Stock("C31.SI")
    rf = RiskFree(10)
    market = Market(s.get_stock_exchange())
    req_rate = CAPM(rf.spot_yield, market.get_annualised_return(rf.year), s.beta)

    gg_result = gordon_growth(s, req_rate)

    report_name = f"{s.stock_code}-report.html"
    
    template = util.get_template("report_template.html")
    template_vars = {"gordon_growth": gg_result, "timestamp": datetime.now().strftime("%Y:%m:%d")}

    html_out = template.render(template_vars, s = s)
    logging.debug("Generated report file")

    util.dump_report(html_out, f"/tmp/{report_name}")
    logging.debug("Created report file")

    util.upload_report_to_s3("/tmp/" + report_name, s3_bucket, s3_report_dir + "/" + report_name)


#TODO:
#Config file for bin
#Provision DynamoDB for server