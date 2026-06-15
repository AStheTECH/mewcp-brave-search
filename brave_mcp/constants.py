RATE_LIMIT = {
    # brave_local_search fires 3 HTTP requests per tool call (web + pois + descriptions);
    # set to 3 so a single tool invocation never self-trips the limiter.
    "per_second": 3,
    "per_month": 15000,
}
 
