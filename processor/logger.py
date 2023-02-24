import logging
from processor.counter import Counter


class Logger(object):
    @staticmethod
    def log_progress() -> None:
        status = Counter._count_status()
        # log only when status changes
        if Counter._status != status:
            Counter._status = status
            crawled, no_uid, no_geometry = status
            logging.warning(
                f'C/N_Uid/N_Geo/Total: '\
                f'{crawled}/{no_uid}/{no_geometry}/{Counter._poi_num}'
            )

    @classmethod
    def log_start(cls) -> None:
        logging.warning(f'# ---------- Crawling Started ---------- #')
        logging.warning(f'-- POI total number: {Counter._poi_num}.')
        logging.warning(f'-- POIs to be crawled: {Counter._poi_to_crawl}.')
        cls.log_progress()

    @staticmethod
    def log_uid_fail(exception: Exception, idx: int) -> None:
        logging.error(f'POI index {idx} failed to parse uid. Reason: {exception}')

    @staticmethod
    def log_aoi_fail(exception: Exception, idx: int, uid_name: str) -> None:
        logging.error(f'{uid_name} of POI index {idx} failed to parse AOI. Reason: {exception}')

    @staticmethod
    def log_update() -> None:
        avg_speed, xTime = Counter._cal_speed_xTime()
        logging.warning(f'-- Updated. Avg speed: {avg_speed}. Time remaining: {xTime}.')

    @staticmethod
    def log_finish() -> None:
        avg_speed, _ = Counter._cal_speed_xTime()
        total_time = Counter._total_time()
        poi_missing = Counter._count_missing()
        crawled_prop = Counter._count_status()[0] / Counter._poi_num
        logging.warning('# ---------- Crawling Ended ---------- #')
        logging.warning(f'Avg speed: {avg_speed}. Total crawling time: {total_time}.')
        logging.warning(f'{poi_missing} POIs missing. {crawled_prop:.2%} POIs crawled.')
