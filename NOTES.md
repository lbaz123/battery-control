# Notes

This is just to show my thought process, I wouldn't normally commit this or anything. 

## Approach

- Review the task data, check for anomalies etc
- Define optimisation 
- Set up repo (linting, auto testing with unit and smoke, UV, logging, dotenv)
- Build data ingestion / loading 
- Build battery model, assume starting SOC 50% or something reasonable (and assume we have to end on same to avoid false profit / loss)
- Use Scipy (linprog? will it deal with not allowing simultaneous charge and discharge?) to build opitmisation
- Build results
- Build CLI with printed logs 
- Write up docs instructions for running etc

## Initial findings

- Prices seem low to me but I think that's as expected for 2018-2020, politics! 
- General pattern of cheap overnight, high day makes sense
- Both markets same range and expected number of data points (Market 2 half of Market 1)
- Daylight savings issues in Market 1 - assume it's local time and convert to UTC(?) OR could just pick a month or so for initial task where the timestamps are aligned
- Negative prices! Sell sell sell 
- Round timestamps to seconds. WAIT. A lot of market 2 has 59:59... times, are they interval ending? Is market 1 the same?
- Overall downward trend in prices 

> Decision: Incorporating the degradation info is a stretch goal. Too much for now.

Data questions I would ask the provider: 
- Are the timestamps local? 
- Are the prices at the end or start of interval?

> Decision: Just use January 2018 initially and merge just on index of data point (but considering 2:1 ratio). Can expand as a stretch goal.

## Optimisation