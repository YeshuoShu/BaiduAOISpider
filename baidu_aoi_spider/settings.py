# ---------------------------------------------------------------------------- #
#                      Default settings, no changes needed                     #
# ---------------------------------------------------------------------------- #

BOT_NAME = "baidu_aoi_spider"
SPIDER_MODULES = ["baidu_aoi_spider.spiders"]
NEWSPIDER_MODULE = "baidu_aoi_spider.spiders"

# Disobey robots.txt rules
ROBOTSTXT_OBEY = False

# Enable cookies
COOKIES_ENABLED = True

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;"
    "q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddleware.useragent.UserAgentMiddleware": None,
    "scrapy_fake_useragent.middleware.RandomUserAgentMiddleware": 100,
    "baidu_aoi_spider.middlewares.BaiduAOIMiddleware": 200,
}

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403, 400, 302, 301]

# Log level settings
LOG_LEVEL = "WARNING"

# Settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# ---------------------------------------------------------------------------- #
#                                Custom Settings                               #
# ---------------------------------------------------------------------------- #

# ------------------------------ 1. Concurrency ------------------------------ #

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# Maximum for baidu map is 30 QPS
CONCURRENT_REQUESTS = 25

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 0.1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 10

# --------------------------------- 2. Basics -------------------------------- #

# File path settings
POI_CSV_PATH = "data/POI.csv"
AOI_SHP_PATH = "data/AOI/AOI.shp"

# Spider settings
PROXY_ENABLED = True
UPDATE_INTERVAL = 150  # how many AOI API calls before updating the output file
USE_FIRST_UID = False

# ---------------------- 3. Baidu Map uid API parameters --------------------- #

# Detailed information can be found at:
# https://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-placeapi

# In this project, circular area search is used instead of administrative area search,
# which finds POIs within a certain radius of the input coordinate point.
# The former is more efficient as regional information is not needed.
# However, it may leave out some POIs if the radius are not set appropriately.

API_PARAMS = {
    # 1. Primary/Secondary industry classification (Optional)
    # Please re-classify according to Baidu standard:
    # see https://lbsyun.baidu.com/index.php?title=open/poitags
    "prim_ind": "",  # (1) ''; (2) a string; (3) 'AS_VAR'
    "sec_ind": "",  # same as above
    # 2.1 Retrieval radius
    # To avoid missing out POIs, it is recommended to set it slightly higher, e.g. 2000.
    "radius": 2000,  # unit: meters
    # 2.2 Radius limit
    # It is said that only POIs within retrieval radius will be returned if set to 'true'.
    "radius_limit": "true",  # 'true' or 'false'
    # 3. Coordinate system
    "crs": "wgs84",  # 'gcj02', 'bd09' or 'wgs84'
}

# Baidu access key list, you can get it from https://lbsyun.baidu.com/apiconsole/key
# at least provide one access key
AK_LIST = [
    "your aks",
]

# ---------------------------- 4. AOI filter rules --------------------------- #

FILTER_RULES = {
    # 1. Upper and lower bound of AOI area, in square kilometers
    "min_aoi_area": 0,  # Set to 0 to disable
    "max_aoi_area": 10000,  # Set to a large number to disable, e.g. 10000
    # 2. Lowest name similarity between AOI and POI
    "min_similarity": 0,  # 0 to disable, maximum is 1
    # 3. AOI sorting rules, set to 0 to disable
    "sort_by_search_rank": 1,  # the higher the rank, the more relevant, the better
    "sort_by_area": 0,  # 1 for the smaller the better, -1 for the bigger the better
    "sort_by_distance": 1,  # the closer the AOI's geometry to POI, the better
    "sort_by_similarity": 1,  # the more similar the name of AOI to POI, the better
}
