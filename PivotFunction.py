def build_PP(var):
    """returns pivot point and support/resistance levels"""
    high = float(var['inth'])
    low= float(var['intl'])
    close = float(var['intc'])
    pivot_median = (high + low + close)/3
    pivot_range = high - low
    R1 = round((pivot_median * 2 - low),2)
    R2 = round((pivot_median + 1 * pivot_range) ,2)
    R3 = round(pivot_median * 2 + (high - (2 * low)) ,2)
    R4 = round(pivot_median * 3 + (high - (3 * low)) ,2)
    R5 = round(pivot_median * 4 + (high - (4 * low)) ,2)
    S1 = round((pivot_median * 2 - high) ,2)
    S2 = round((pivot_median - 1 * pivot_range),2)
    S3 = round((pivot_median * 2 - (2 * high  - low)),2)
    S4 = round((pivot_median * 3 - (3 * high  - low)),2)
    S5 = round((pivot_median * 4 - (4 * high  - low)),2)
    P = round(pivot_median,2)
    pivotValues =  { "P":P, "R1":R1, "R2":R2, "R3":R3, "R4":R4, "R5":R5, "S1":S1, "S2":S2, "S3":S3, "S4":S4, "S5":S5}
    #pivotValues = json.dumps(pivotValues)
    return pivotValues


