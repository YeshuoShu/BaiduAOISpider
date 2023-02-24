import logging, pandas as pd, geopandas as gpd
from processor.repository import Repo
from spatial.geometry import wkt_to_geometry
from spatial.coords import gcj02_to_wgs84, bd09ll_to_wgs84
from processor.aoi_container import AOI


class FileOperator(object):
    @staticmethod
    def add_cols() -> None:
        """
        In the output `AOI csv`, five additional columns will be added:
            - status (str): 'Matched', 'No Uid' or 'No Geometry'
            - uid_name (str): name of the uid whose geometry is chosen
            - lng_wgs84 (float)/lat_wgs84 (float): longitude/latitude in wgs84 CRS
            - geometry (`wkt`, well known text): AOI polygon geometry
        """
        for col in ['status', 'uid_name', 'lng_wgs84', 'lat_wgs84', 'geometry']:
            if col not in Repo.file.columns:
                Repo.file[col] = None
        # the 'geometry' column will be saved as wkt in csv
        # convert it to shapely geometry when re-crawling
        Repo.file.geometry = Repo.file.geometry.apply(
            lambda x: wkt_to_geometry(x) if isinstance(x, str) else x
        )
        logging.warning('(3/6) Additional columns appended.')

    @classmethod
    def convert_crs_to_wgs84(cls) -> None:
        """
        Convert longitude and latitude columns
        from `gcj02` or `bd09ll` CRS to `wgs84`,
        and save as new columns: `lng_wgs84` and `lat_wgs84`.
        """
        if Repo._crs != 'wgs84':
            # only support gcj02 and bd09ll conversion
            if Repo._crs == 'gc02':
                cls._transform_crs(gcj02_to_wgs84)
            elif Repo._crs == 'bd09':
                cls._transform_crs(bd09ll_to_wgs84)
            logging.warning('(4/6) CRS converted to wgs84.')
        # if the CRS is already wgs84, copy the original columns
        elif Repo._crs == 'wgs84':
            cls._transform_crs(lambda x, y: (x, y))
            logging.warning('(4/6) CRS is already wgs84.')

    @staticmethod
    def write_aoi_and_status(idx: int, best_aoi: AOI) -> None:
        """
        Write the best AOI geometry and crawling status into the file.
        """
        Repo.file.loc[idx,'status'] = 'Matched'
        Repo.file.loc[idx, 'geometry'] = best_aoi.geometry
        Repo.file.loc[idx, 'uid_name'] = best_aoi.uid_name

    @classmethod
    def save_file(cls) -> None:
        """
        Save the file as csv and shp (if any geometry exists).
        """
        cls._save_as_csv()
        cls._save_as_shp()

    @staticmethod
    def _transform_crs(func: callable) -> pd.DataFrame:
        Repo.file[['lng_wgs84', 'lat_wgs84']] = pd.DataFrame(
            Repo.file.apply(lambda x: func(x.lng, x.lat), axis=1).tolist(),
            index=Repo.file.index
        )

    @staticmethod
    def _save_as_csv() -> None:
        Repo.file.to_csv(
            Repo._poi_csv_path,
            encoding='utf-8',
            index=False
        )

    @staticmethod
    def _save_as_shp() -> None:
        df = Repo.file.dropna(subset=['geometry'])
        # export to shp only when there is at least one geometry
        if len(df):
            gdf = gpd.GeoDataFrame(
                df,
                geometry='geometry',
                crs='epsg:4326'
            )
            gdf.to_file(Repo._aoi_shp_path, encoding='utf-8')
