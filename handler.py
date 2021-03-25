from quantifin.equity import Stock
from quantifin.util import RiskFree
from quantifin.util.markets import Market
from quantifin.equity.valuation import *
from jinja2 import Environment, FileSystemLoader
import sys
import util
import logging
from datetime import datetime

def gordon_growth(stock, req_return, growth_rate, factor):
    if req_return < 0:
        req_return = 0.05
        logging.info("Required Rate Of Return Negative. Defaulting to 0.05")
    result = list()
    result.append(("Required Rate Of Return", f"{__convert_to_pct(req_return)}%"))
    result.append(("Assumption", f"Using a factor of {factor} to scale growth rate of {__convert_to_pct(growth_rate)}%"))
    growth_rate *= factor
    result.append(("Growth Rate", f"{__convert_to_pct(growth_rate)}%"))
    print(req_return)
    value = gordon_growth_valuation(stock.full_year_dividend(), req_return, growth_rate)
    result.append(("Valuation", value))
    return result

def gordon_growth_range(s, req_rate):
    result = dict()
    growth_rate = s.growth_rate()
    result["normal"] = gordon_growth(s, req_rate, growth_rate, 1)
    result["conservative"] = gordon_growth(s, req_rate, growth_rate, 0.5)
    result["optimistic"] = gordon_growth(s, req_rate, growth_rate, 1.2)
    return result

def fcf_growth_range(s,req_rate):
    logging.debug("Calculating FCF Growth")
    result = dict()
    result["req_rate"] =  __convert_to_pct(req_rate)
    result["fcf_history"] = s.get_fcf_history()
    no_shares = s.get_num_shares_outstanding()
    result["no_shares"] = no_shares
    result["normal"] = fcf_growth(s, req_rate, 0.1, no_shares)
    result["optimistic"] =  fcf_growth(s, req_rate, 0.3, no_shares)
    result["conservative"] =  fcf_growth(s, req_rate, 0.05, no_shares)
    return result

def fcf_growth(s, req_rate, factor, no_shares):
    if req_rate < 0:
        req_rate = 0.05
    result = list()
    fcf = s.get_fcf_history()
    result.append(("Assumption", f"Using a factor of {factor} to scale FCF growth rate of {__convert_to_pct(s.fcf_growth_rate())}%"))
    fcf_growth=s.fcf_growth_rate()*factor
    result.append(("FCF Growth Rate", f"{__convert_to_pct(fcf_growth)}%"))
    value = gordon_growth_valuation(__first_item_in_dict(fcf), req_rate, fcf_growth)
    result.append(("Valuation", round(value/ no_shares, 3)))
    return result

def __first_item_in_dict(d):
    return next(iter(d.values()))


def get_greeks(s, market, rf):
    logging.debug("Calculating Greeks")
    end = datetime.now()
    end_string = end.strftime("%Y-%m-%d")
    start = datetime(end.year - 1, end.month, end.day)
    start_string = start.strftime("%Y-%m-%d")  
    logging.debug(f"Calculating greeks using data from {start_string} to {end_string}")

    rf_history = rf.yield_history(start_string, end_string, "monthly")[1:] #Drop current spot yield
    sortino = s.get_sortino_ratio(start_string, end_string, "monthly", rf_history)
    sharpe = s.get_sharpe_ratio_ex_post(start_string, end_string, "monthly", rf_history)
    cv = s.get_coefficient_of_variation(1, "monthly")
    market_one_year_return = market.get_annualised_return(1)
    alpha = s.get_alpha(1, market_one_year_return, rf_history[0])
    return {"sortino": sortino, "sharpe": sharpe, "cv": cv, "alpha": alpha}


def __convert_to_pct(val):
    return round(val * 100, 3)

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
    ann_market_return = market.get_annualised_return(rf.year)
    if ann_market_return < 0:
        market = Market("S&P")
        logging.debug("Using S&P as market instead")
        ann_market_return = market.get_annualised_return(rf.year)

    req_rate = CAPM(rf.spot_yield, ann_market_return, s.beta)
    greeks = get_greeks(s, market, rf)

    gg_result = gordon_growth_range(s, req_rate)
    fcf_result = fcf_growth_range(s, req_rate)

    report_name = f"{s.stock_code}-report.html"
    
    template = util.get_template("report_template.html")
    template_vars = {"spot_yield": __convert_to_pct(rf.spot_yield), "market_ann_return": __convert_to_pct( market.get_annualised_return(rf.year)), "benchmark_year": rf.year, "req_rate": __convert_to_pct(req_rate),
                    "greeks": greeks, "gordon_growth": gg_result, "fcf_growth": fcf_result,
                    "timestamp": datetime.now().strftime("%Y:%m:%d")}

    html_out = template.render(template_vars, s = s)
    logging.debug("Generated report file")

    util.dump_report(html_out, f"/tmp/{report_name}")
    logging.debug("Created report file")

    #util.upload_report_to_s3("/tmp/" + report_name, s3_bucket, s3_report_dir + "/" + report_name)


#TODO:
#Config file for bin
#Provision DynamoDB for server