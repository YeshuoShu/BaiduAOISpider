import time, logging
from typing import Tuple
from processor.repository import Repo


class Counter(object):
    @classmethod
    def boot(cls) -> None:
        cls._poi_num = len(Repo.file)
        cls._init_status = cls._count_status()
        cls._status = ()
        cls._df = Repo.file.reindex(
            columns=['poi_aoi_total', 'poi_aoi_called'],
            fill_value=0
        )
        cls._init_time = time.time()
        cls._time = cls._init_time
        cls._poi_to_crawl = cls._poi_num - sum(cls._init_status)
        logging.warning('(5/6) Counter booted.')

    @classmethod
    def write_aoi_total_num(cls, idx: int, total_num: int) -> None:
        """
        Write the total number of AOIs of a POI into the `Counter`.
        """
        cls._df.loc[idx, 'poi_aoi_total'] = total_num

    @classmethod
    def count_aoi_called(cls, idx: int) -> None:
        """
        Count when an AOI url of a POI is called.
        """
        cls._df.loc[idx, 'poi_aoi_called'] += 1

    @classmethod
    def all_aoi_called(cls, idx: int) -> None:
        """
        Determine if all AOIs of a POI are called.
        """
        total_num = cls._df.loc[idx, 'poi_aoi_total']
        called_num = cls._df.loc[idx, 'poi_aoi_called']
        return called_num == total_num

    @classmethod
    def reach_update_interval(cls) -> None:
        """
        Determine if the `UPDATE_INTERVAL` is reached.
        """
        total_called_times = cls._df.poi_aoi_called.sum()
        if total_called_times % Repo._update_interval == 0:
            cls._time = time.time()
            return True

    @staticmethod
    def _count_status() -> Tuple[int, int, int]:
        def count(status: str) -> int:
            return Repo.file.status.eq(status).sum()
        crawled = count('Crawled')
        no_uid = count('No Uid Available')
        no_geometry = count('No Geometry Accepted')
        return crawled, no_uid, no_geometry

    @classmethod
    def _count_missing(cls) -> int:
        total = cls._poi_num
        crawled, no_uid, no_geometry = cls._count_status()
        cls.missing = total - crawled - no_uid - no_geometry
        return cls.missing

    @classmethod
    def _cal_speed_xTime(cls) -> Tuple[str, str]:
        # average crawling speed
        poi_crawled = cls._status[0] - cls._init_status[0]
        time_elapsed = cls._time - cls._init_time
        if time_elapsed == 0:
            return 'nan/s (nan/h)', 'nan'
        else:
            avg_speed = poi_crawled / time_elapsed
        # expected remaining time
        poi_remaining = Counter._poi_to_crawl - poi_crawled
        if avg_speed == 0:
            xTime = 'Inf'
        else:
            xTime = cls._format_time(poi_remaining / avg_speed)
        # format average speed
        avg_speed = f'{avg_speed:.2f}/s ({avg_speed*3600:.0f}/h)'
        return avg_speed, xTime
    
    @classmethod
    def _total_time(cls) -> str:
        return cls._format_time(cls._time - cls._init_time)
    
    @staticmethod
    def _format_time(time: float) -> str:
        if time > 24*60*60:
            time = f'>24h'
        elif time > 60*60:
            time = f'{time // 3600:.0f}h{time % 3600 // 60:.0f}min'
        elif time > 60:
            time = f'{time // 60:.0f}min{time % 60:.0f}s'
        else:
            time = f'{time:.0f}s'
        return time
