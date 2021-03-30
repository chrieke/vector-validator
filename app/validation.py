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
        is_single_ring=None,
        is_no_selfintersection=None,
        is_no_holes=None,
        is_ccw=None,
    ):
        self.df = df
        self.valid_by_citeria = False
        self.valid_all = False
        self.is_single_ring = False
        self.is_no_selfintersection = False
        self.is_no_holes = False
        self.is_ccw = False

    def run_validation_checks(self, selected_validations: List[str]) -> None:
        """
        Checks all validity conditions.
        """
        self.check_is_no_selfintersection()
        self.check_is_single_ring()
        self.check_is_no_holes()
        self.check_is_ccw()

        self.valid_all = False
        if all([self.is_no_selfintersection, self.is_no_holes, self.is_ccw]):
            self.valid_all = True

        self.valid_by_citeria = False
        # if "No Self-Intersection" in selected_validations and self.is_no_selfintersection

    # todo

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
