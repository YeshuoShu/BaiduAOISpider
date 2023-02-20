import json, random, pandas as pd
from typing import List, Tuple
from scrapy.http import Response
from shapely.geometry import Polygon
from processor.repository import Repo
from spatial.coords import bd09ll_to_wgs84, bd09mc_to_wgs84
from spatial.geometry import within_distance, points_to_polygon


class APIHandler(object):
    @classmethod
    def assemble_uid_urls(cls) -> List[Tuple[int, str]]:
        """
        Construct `Baidu uid` circular area search urls (POIs that are already queried are skipped) using following parameters, and return a list of `(DataFrame_idx, url)` tuples:
            - ak (str): a random Baidu API key
            - name (str): POI's name
            - lng/lat (float): POI's longitude/latitude (wgs84 CRS)
            - radius (int): area search radius, in meters
            - radius_limit (str): 'true' or 'false', whether to limit the search radius
            - prim_ind (str): primary industry category
            - sec_ind (str): secondary industry category
            - scope (int): search scope, equals 2 if `prim_ind` and `sec_ind` are specified, otherwise equals 1
        """
        urls = []
        df = Repo.file.copy()
        # store industry parameter in a column
        if Repo._prim_ind != 'AS_VAR':
            df['prim_ind'] = Repo._prim_ind
        if Repo._sec_ind != 'AS_VAR':
            df['sec_ind'] = Repo._sec_ind
        # concatenate urls
        for idx in df.index:
            # skip POIs that are already queried
            if not pd.isna(df.loc[idx, 'status']):
                continue
            name = df.loc[idx, 'name']
            lng, lat = df.loc[idx, 'lng_wgs84'], df.loc[idx, 'lat_wgs84']
            prim_ind, sec_ind = df.loc[idx, 'prim_ind'], df.loc[idx, 'sec_ind']
            url = f'http://api.map.baidu.com/place/v2/search?'\
                  f'query={name}'\
                  f'&location={lat},{lng}'\
                  f'&radius={Repo._radius}'\
                  f'&radius_limit={Repo._radius_limit}'\
                  f'&ak={random.choice(Repo._ak_list)}'\
                  f'&output=json&coord_type=1'
            url += cls._industry_url_segment(prim_ind, sec_ind)
            urls.append((idx, url))
        return urls

    @classmethod
    def extract_uid_name_rank(
        cls,
        idx: int,
        response: Response
    ) -> (Exception | List[Tuple[str, str, int]]):
        """
        Parse the `Baidu uid` response, filter the results,
        and return a list of `(uid_name, uid, search_rank)` triples.
        If `USE_FIRST_UID` is on, only the first result is returned.

        Filter Rules:
        -----
        1. `name`, `uid`, and `geo-location` must exist.
        2. The search result must be within the radius.
        3. (Optional, if any of `prim_ind` and `sec_ind` are specified) The industry category must be consistent.

        Json Response Example
        -----
        ```
        # Suppose we search Peking University, the list extracted is of the form:
        # [('北京大学', 'ddfd7c2d8db36cf39ee3219e', 1), ...]
        {
            # some information
            # ...
            "results": [
                {
                    "name": "北京大学",
                    "location": {
                        "lat": 39.998877,
                        "lng": 116.316833,
                    },
                    "address": "北京市海淀区颐和园路5号",
                    "province": "北京市",
                    "city": "北京市",
                    "area": "海淀区",
                    "telephone": "(010)62752114",
                    "detail": 1,
                    "uid": "ddfd7c2d8db36cf39ee3219e"
                    "detail_info":{
                        "tag":"教育培训;高等院校",
                        # ...
                    },
                    # more information
                    # ...
                },
                # more uids
                # ...
            ]
        }
        ```
        """
        name_uid_rank = []
        status = json.loads(response.text).get('status')
        results = json.loads(response.text).get('results')
        # check status
        cls._check_status(status)
        # background POI property
        p_property = cls._get_p_property(Repo.file, idx)
        # filter results
        if results:
            for rank, result in enumerate(results):
                # extract uid's property
                u_property = cls._get_u_property(result)
                # keep the result if it passes all the rules
                if cls._pass_filter_rules(**p_property, **u_property):
                    name_uid_rank.append(
                        (result['name'], result['uid'], rank + 1)
                    )
                if Repo._use_first_uid and name_uid_rank:
                    break
        return name_uid_rank

    @staticmethod
    def assemble_aoi_url(uid: str) -> str:
        """
        Construct a `Baidu AOI` url with this AOI's `uid`.
        """
        return f'https://map.baidu.com/?newmap=1&qt=ext&'\
               f'uid={uid}&ext_ver=new&ie=utf-8&l=11'

    @staticmethod
    def get_polygon_geometry(response: Response) -> Polygon | None:
        """
        Parse the `Baidu AOI` response, extract the polygon geometry.

        Json Response Example
        -----
        Geo data from json response conforms to the following format:
        `4|some_other_x, some_other_y...|1-x1, y1, x2, y2,..., xn, yn;`,
        what needs to be extracted is the part of `x1, y1,..., xn, yn`

        ```
        # Suppose we search the uid of Peking University,
        # the json response is like:
        {
            # some information
            # ...
            "content": {
                "geo": "4|12946839.266068,4837125.446178;12949751.777560,4839020.969541|1-12948599.7094790,4837127.8547043,...,12948599.7094790,4837127.8547043;",
                "uid": "ddfd7c2d8db36cf39ee3219e"
            },
            # some information
            # ...
        }
        ```
        """
        response = json.loads(response.text)
        geo = response.get('content', {}).get('geo')
        if geo:
            xys = geo.split('|')[2][2:-1].split(',')
            # xys now looks like [x1, y1, x2, y2, ..., xn, yn]
            # convert it into the format [(x1, y1), (x2, y2), ..., (xn, yn)]
            points = [bd09mc_to_wgs84(float(x), float(y))
                      for x, y in zip(xys[::2], xys[1::2])]
            return points_to_polygon(points)

    @staticmethod
    def _industry_url_segment(prim_ind: str, sec_ind: str) -> str:
        if prim_ind and sec_ind:
            return f'&tag={prim_ind};{sec_ind}&scope=2'
        elif prim_ind or sec_ind:
            return f'&tag={prim_ind + sec_ind}&scope=2'
        return '&scope=1'

    @staticmethod
    def _check_status(status: int) -> None:
        """
        For more status code information, please refer to
        https://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-placeapi
        """
        if status == 0:
            return
        elif status // 100 == 2:
            raise Exception(f'API Parameter Invalid: {status}.')
        elif status // 100 == 3:
            raise Exception(f'API Verify Failure: {status}.')
        elif status // 100 == 4:
            raise Exception(f'API Quota Failure: {status}.')
        elif status // 100 == 5:
            raise Exception(f'API AK Failure: {status}.')
        else:
            raise Exception(f'API Error: {status}.')

    @staticmethod
    def _get_p_property(df: pd.DataFrame, idx: int) -> dict:
        radius = Repo._radius / 1000  # convert to km
        p_lng, p_lat = df.loc[idx, 'lng_wgs84'], df.loc[idx, 'lat_wgs84']
        if Repo._prim_ind == 'AS_VAR':
            p_prim_ind = df.loc[idx, 'prim_ind']
        else:
            p_prim_ind = Repo._prim_ind
        if Repo._sec_ind == 'AS_VAR':
            p_sec_ind = df.loc[idx, 'sec_ind']
        else:
            p_sec_ind = Repo._sec_ind
        return dict(
            p_lng=p_lng,
            p_lat=p_lat,
            radius=radius,
            p_prim_ind=p_prim_ind,
            p_sec_ind=p_sec_ind,
        )

    @staticmethod
    def _get_u_property(result: dict) -> dict:
        return dict(
            uid=result.get('uid'),
            uid_name=result.get('name'),
            u_lng=result.get('location', {}).get('lng'),  # of bd09ll CRS
            u_lat=result.get('location', {}).get('lat'),
            u_tag=result.get('detail_info', {}).get('tag'),
        )

    @staticmethod
    def _pass_filter_rules(
        p_lng: float,
        p_lat: float,
        radius: float,
        p_prim_ind: str,
        p_sec_ind: str,
        uid: str,
        uid_name: str,
        u_lng: float,
        u_lat: float,
        u_tag: str | None,
    ) -> bool:
        # 1. check if key information exists
        if not (uid and uid_name and u_lng and u_lat):
            return False
        # 2. should not be outside the radius
        u_lng, u_lat = bd09ll_to_wgs84(u_lng, u_lat)  # re-project to wgs84 CRS
        if not within_distance(u_lng, u_lat, p_lng, p_lat, distance=radius):
            return False
        # 3. check if industry category is consistent
        if p_prim_ind and p_sec_ind:
            p_tag = f'{p_prim_ind};{p_sec_ind}'
        else:
            p_tag = p_prim_ind + p_sec_ind
        if p_tag and (p_tag not in u_tag):
            return False
        return True
