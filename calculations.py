
from quantifin.equity import Stock
from quantifin.util import RiskFree
from quantifin.util.markets import Market
from quantifin.equity.valuation import *
import logging
from datetime import datetime, timedelta
from util import convert_to_pct

def gordon_growth(stock, req_return, growth_rate, factor):
    if req_return < 0:
        req_return = 0.05
        logging.info("Required Rate Of Return Negative. Defaulting to 0.05")
    result = list()
    result.append(("Required Rate Of Return", f"{convert_to_pct(req_return)}%"))
    result.append(("Assumption", f"Using a factor of {factor} to scale growth rate of {convert_to_pct(growth_rate)}%"))
    growth_rate *= factor
    result.append(("Growth Rate", f"{convert_to_pct(growth_rate)}%"))
    try:
        value = gordon_growth_valuation(stock.full_year_dividend(), req_return, growth_rate)
        result.append(("Valuation", value))
    except ValueError as e:
        result.append(("Valuation Error", str(e)))
        logging.debug(f"Error calculating gordon growth: {str(e)}")
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
    result["req_rate"] =  convert_to_pct(req_rate)
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
    result.append(("Assumption", f"Using a factor of {factor} to scale FCF growth rate of {convert_to_pct(s.fcf_growth_rate())}%"))
    fcf_growth=s.fcf_growth_rate()*factor
    result.append(("FCF Growth Rate", f"{convert_to_pct(fcf_growth)}%"))
    logging.debug(f"req_rate = {req_rate} growth_rate= {fcf_growth}")
    try:
        value = gordon_growth_valuation(__first_item_in_dict(fcf), req_rate, fcf_growth)
        result.append(("Valuation", round(value/ no_shares, 3)))
    except ValueError as e:
        result.append(("Valuation Error", str(e)))
        logging.debug(f"Error calculating FCF growth: {str(e)}")
    return result

def forward_pe_range(s, req_rate):
    logging.debug("Calculating Forward PE Valuation")
    result = dict()
    result["req_rate"] = req_rate
    growth_rate = s.growth_rate()
    result['growth_rate'] = growth_rate
    ratio_hist = s.get_dividend_payout_ratio_history()
    result['ratio_hist'] = ratio_hist
    payout = s.average_dividend_payout_ratio(ratio_hist)
    result['payout'] = payout
    eps = s.get_key_statistics_data()[s.stock_code]['trailingEps']
    result['eps'] = eps
    result['normal'] = forward_pe_calc(payout, req_rate, growth_rate, eps, 1)
    result['conservative'] = forward_pe_calc(payout, req_rate, growth_rate, eps, 0.5)
    result['optimistic'] = forward_pe_calc(payout, req_rate, growth_rate, eps, 1.2)
    return result

def forward_pe_calc(avg_payout_ratio, req_rate, growth_rate, eps, factor):
    if req_rate < 0:
        req_rate = 0.05
    result = list()
    result.append(("Assumptions", f"Using a growth rate of {convert_to_pct(growth_rate)}% and a factor of {factor} "))
    growth_rate *= factor
    result.append(("Growth Rate", f"{convert_to_pct(growth_rate)}%"))
    try:
        value = forward_pe(avg_payout_ratio, growth_rate, req_rate, eps)
        result.append(("Valuation", value))
    except (ValueError, Warning) as e:
        result.append(("Valuation Error", str(e)))
        logging.debug(f"Error calculating FCF growth: {str(e)}")
    return result

def __first_item_in_dict(d):
    return next(iter(d.values()))


def get_greeks(s, market, rf):
    logging.debug("Calculating Greeks")
    end = datetime.now()
    end = datetime.now() - timedelta(days=1)
    end_string = end.strftime("%Y-%m-%d")
    start = end - timedelta(weeks=52)
    start_string = start.strftime("%Y-%m-%d")  
    logging.debug(f"Calculating greeks using data from {start_string} to {end_string}")

    rf_history = rf.yield_history(start_string, end_string, "monthly")[1:] #Drop current spot yield
    try:
        sortino = s.get_sortino_ratio(start_string, end_string, "monthly", rf_history)
        sharpe = s.get_sharpe_ratio_ex_post(start_string, end_string, "monthly", rf_history)
    except ValueError as e:
        rf_history = rf.yield_history(start_string, end_string, "monthly")
        sortino = s.get_sortino_ratio(start_string, end_string, "monthly", rf_history)
        sharpe = s.get_sharpe_ratio_ex_post(start_string, end_string, "monthly", rf_history)
    try:
        cv = s.get_coefficient_of_variation(1, "daily")
        market_one_year_return = market.get_annualised_return(1)
        alpha = s.get_alpha(1, market_one_year_return, rf_history[0])
    except TypeError as e:
        logging.error("Failed to calculate coefficient of variation")
        cv = "N/A"
        alpha = "N/A"
    return {"sortino": sortino, "sharpe": sharpe, "cv": cv, "alpha": alpha}


