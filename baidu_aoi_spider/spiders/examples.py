from baidu_aoi_spider.spiders.baidu_aoi import BaiduAOISpider

class Example1(BaiduAOISpider):
    name = 'example1'
    updating_settings = dict(
        POI_CSV_PATH = 'data/POI_example1.csv',
        AOI_SHP_PATH = 'data/AOI_example1/AOI_example1.shp',
        PROXY_ENABLED = False,
        UPDATE_INTERVAL = 20,
        API_PARAMS = {
            'prim_ind': '房地产',
            'sec_ind': '住宅区',
        },
        FILTER_RULES = {
            'max_aoi_area': 1,
            'min_similarity': 0.1,
        },
    )

class Example2(BaiduAOISpider):
    name = 'example2'
    updating_settings = dict(
        POI_CSV_PATH = 'data/POI_example2.csv',
        AOI_SHP_PATH = 'data/AOI_example2/AOI_example2.shp',
        PROXY_ENABLED = False,
        UPDATE_INTERVAL = 20,
        API_PARAMS = {
            'prim_ind': 'AS_VAR',
            'sec_ind': 'AS_VAR',
            'crs': 'bd09',
        },
        FILTER_RULES = {
            'min_aoi_area': 0.02,
            'sort_by_area': -1,
        }
    )
