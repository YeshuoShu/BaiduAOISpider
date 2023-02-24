import scrapy
from scrapy.http import Request
from processor import Repo, Validator, Counter, Logger
from processor import FileOperator, APIHandler, AOIContainer

class BaiduAOISpider(scrapy.Spider):
    name = 'BaiduAOI'
    updating_settings = dict()
    allowed_domains = ['map.baidu.com', 'api.map.baidu.com']

    # ------------------------------ initialization ------------------------------ #

    @classmethod
    def from_crawler(cls, crawler):
        # bind a close_spider method
        spider = super(BaiduAOISpider, cls).from_crawler(
            crawler, crawler.settings.copy_to_dict()
        )
        crawler.signals.connect(spider.close_spider, signal=scrapy.signals.spider_closed)
        return spider

    def __init__(self, settings):
        settings = self.deep_update(settings, self.updating_settings)
        # import and validate settings
        Repo.import_settings(settings)
        Validator.validate_settings()
        # load file and validate it
        Repo.load_file()
        Validator.validate_file()
        # prepare file for writing
        FileOperator.add_cols()
        FileOperator.convert_crs_to_wgs84()
        # counter and AOI container initialization
        Counter.boot()
        AOIContainer.mold()
        
    # -------------------------------- main spider ------------------------------- #

    def start_requests(self):
        Logger.log_start()
        # idx_url_tuples is of the form [(idx1, url1), (idx2, url2), ...]
        idx_url_tuples = APIHandler.assemble_uid_urls()
        for idx, url in idx_url_tuples:
            yield self.request_uid(url, idx=idx)

    def parse_uid(self, response, idx):
        try:
            # uid_name_rank_triples is of the form:
            # [(uid_name1, uid1, search_rank1), (uid_name2, uid2, search_rank2), ...]
            uid_name_rank_triples = APIHandler.extract_uid_name_rank(idx, response)
            if uid_name_rank_triples:
                # record how many uids are available for this POI
                Counter.write_aoi_total_num(idx, len(uid_name_rank_triples))
                # if `USE_FIRST_UID` is on, only the first search result will be requested
                for uid_name, uid, rank in uid_name_rank_triples:
                    url = APIHandler.assemble_aoi_url(uid)
                    yield self.request_aoi(url, idx=idx, uid_name=uid_name, rank=rank)
            else:
                # no uid found, skip this POI
                Repo.file.loc[idx, 'status'] = 'No Uid'
                Logger.log_progress()
        except Exception as e:
            Logger.log_uid_fail(e, idx)

    def parse_aoi(self, response, idx, uid_name, rank):
        try:
            geometry = APIHandler.get_polygon_geometry(response)
            # if geometry exists and is valid,
            # append it to the AOI list of this POI
            if geometry:
                AOIContainer.append(idx, rank, uid_name, geometry)
        except Exception as e:
            Logger.log_aoi_fail(e, idx, uid_name)
        finally:
            # count that one AOI of this POI is called
            Counter.count_aoi_called(idx)
            # if all AOIs of this POI are called,
            # find the best AOI and record it if exists
            if Counter.all_aoi_called(idx):
                best_aoi = AOIContainer.get_best_aoi(idx)
                if best_aoi:
                    FileOperator.write_aoi_and_status(idx, best_aoi)
                else:
                    Repo.file.loc[idx, 'status'] = 'No Geometry'
                Logger.log_progress()
            # update file periodically
            if Counter.reach_update_interval():
                FileOperator.save_file()
                Logger.log_update()
    
    def close_spider(self):
        Logger.log_finish()
        FileOperator.save_file()
    
    # ---------------------------------- utility --------------------------------- #
            
    def request(self, url: str, **kwargs) -> Request:
        return scrapy.Request(url=url, **kwargs,
                              dont_filter=True,
                              meta={'proxy_enabled': Repo._proxy_enabled})
        
    def request_uid(self, url: str, **kwargs) -> Request:
        params = dict(
            callback=self.parse_uid,
            headers={'Host': 'api.map.baidu.com'},
            cb_kwargs=dict(**kwargs),
        )
        return self.request(url, **params)
    
    def request_aoi(self, url: str, **kwargs) -> Request:
        params = dict(
            callback=self.parse_aoi,
            headers={'Host': 'map.baidu.com'},
            cb_kwargs=dict(**kwargs),
        )
        return self.request(url, **params)
    
    def deep_update(self, base_dict: dict, updating_dict: dict) -> dict:
        updated_dict = base_dict.copy()
        for k, v in updating_dict.items():
            if isinstance(v, dict):
                updated_dict[k] = self.deep_update(updated_dict.get(k, {}), v)
            else:
                updated_dict[k] = v
        return updated_dict
