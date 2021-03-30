from quantifin.equity import Stock
from quantifin.util import RiskFree
from quantifin.util.markets import Market
from quantifin.equity.valuation import *
from jinja2 import Environment, FileSystemLoader
import sys
import util
import logging
from datetime import datetime
from calculations import *

if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO )
    try:
        config_path = sys.argv[1]
    except IndexError as e:
        raise IndexError("Configuration file not provided")

    config = util.load_configuration(config_path)
    report_template = config.get("report_template")
    s3_bucket = config.get("s3_bucket")
    s3_report_dir = config.get("s3_report_dir")
    finnhub_key_path = config.get("finnhub_key_path")
    db_table_name = config.get("dynamo_table_name")
    logging.info(f"""Initialised application
Using following configurations: S3 Bucket: {s3_bucket}  S3 Report Dir: {s3_report_dir} Report template: {report_template} Database Table: {db_table_name}""")
    
    finnhub_client = util.login_finnhub(finnhub_key_path)
    db = util.login_db(db_table_name)

    stocks = util.rank_list_by_attr(db, "beta", 10, False)
    
    s = Stock("LULU")
    rf = RiskFree(10)
    market = Market(s.get_stock_exchange())
    ann_market_return = market.get_annualised_return(rf.year)
    if ann_market_return < 0:
        market = Market("S&P")
        logging.debug("Using S&P as market instead")
        ann_market_return = market.get_annualised_return(rf.year)

    req_rate = CAPM(rf.spot_yield, ann_market_return, s.beta)
    greeks = get_greeks(s, market, rf)

    gg_result = gordon_growth_range(s, req_rate)
    fcf_result = fcf_growth_range(s, req_rate)
    forward_pe_result = forward_pe_range(s, req_rate)

    report_name = f"{s.stock_code}-report.html"
    
    template = util.get_template("report_template.html")
    template_vars = {"spot_yield": util.convert_to_pct(rf.spot_yield), "market_ann_return": util.convert_to_pct( market.get_annualised_return(rf.year)), "benchmark_year": rf.year, "req_rate": util.convert_to_pct(req_rate),
                    "greeks": greeks, "gordon_growth": gg_result, "fcf_growth": fcf_result, "forward_pe": forward_pe_result,
                    "timestamp": datetime.now().strftime("%Y:%m:%d")}

    html_out = template.render(template_vars, s = s)
    logging.debug("Generated report file")

    util.dump_report(html_out, f"/tmp/{report_name}")
    logging.debug("Created report file")

    util.upload_report_to_s3("/tmp/" + report_name, s3_bucket, s3_report_dir + "/" + report_name)


#TODO:
#Config file for bin
#Provision DynamoDB for server