from typing import List

from geopandas import GeoDataFrame


class Vector:
    """
    Class handling the checks and geometry validation.
    """
    def __init__(
        self,
        df: GeoDataFrame,
        fixable_valid=None,
        all_valid=None,
        is_single_feature=None,
        is_polygon=None,
        is_single_ring=None,
        is_4326=None,
        is_no_selfintersection=None,
        is_no_holes=None,
        is_ccw=None,
    ):
        self.df = df
        self.fixable_valid = False
        self.all_valid = False
        self.is_single_feature = False
        self.is_polygon = False
        self.is_single_ring = False
        self.is_4326 = False
        self.is_no_selfintersection = False
        self.is_no_holes = False
        self.is_ccw = False

    def run_validity_checks(self, valiation_selection: List[str]) -> None:
        """
        Checks all validity conditions, sets self.fixable_valid and self.all_valid.
        """
        if "Single Feature" in valiation_selection:
            self.check_is_single_feature()
        if "Is Polygon" in valiation_selection:
            self.check_is_polygon()
        if "Is 4326" in valiation_selection:
            self.check_is_4326()
        if "No Holes" in valiation_selection:
            self.check_is_single_ring()
            self.check_is_no_holes()
        if "No Self-intersection" in valiation_selection:
            self.check_is_no_selfintersection()
        if "Counterclockwise" in valiation_selection:
            self.check_is_ccw()

        self.fixable_valid = False
        self.all_valid = False

        if all([self.is_no_selfintersection, self.is_no_holes, self.is_ccw]):
            self.fixable_valid = True

        if self.fixable_valid:
            #         and all(
            #     [
            #         self.is_single_feature,
            #         self.is_polygon,
            #         self.is_single_ring,
            #     ]
            # ):
            self.all_valid = True

    def check_is_single_feature(self) -> None:
        self.is_single_feature = self.df.shape[0] == 1

    def check_is_polygon(self) -> None:
        self.is_polygon = all(
            [t == "Polygon" for t in self.df.geometry.geom_type.unique()]
        )

    def check_is_single_ring(self) -> None:
        self.is_single_ring = (
            len(self.df.iloc[0].geometry.__geo_interface__["coordinates"]) == 1
        )

    def check_is_4326(self) -> None:
        self.is_4326 = self.df.crs == "EPSG:4326"

    def check_is_no_selfintersection(self) -> None:
        self.is_no_selfintersection = all(
            self.df.geometry.apply(lambda x: x.is_valid).to_list()
        )

    def check_is_no_holes(self) -> None:
        if not any(
            [
                row.geometry.geom_type == "Polygon" and row.geometry.interiors
                for _, row in self.df.iterrows()
            ]
        ):
            self.is_no_holes = True

    def check_is_ccw(self) -> None:
        if all(
            [
                row.geometry.exterior.is_ccw
                for _, row in self.df.iterrows()
                if row.geometry.geom_type == "Polygon"
            ]
        ):
            self.is_ccw = True
