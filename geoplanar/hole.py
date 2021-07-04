#!/usr/bin/env python3
#
import pandas
import geopandas
from shapely.geometry import box


def holes(gdf):
    """Find holes in a geodataframe.

    A hole is also known as a sliver which contains a set of points that

    - are not contained by any of the geometries in the geoseries
    - are contained in the convex hull of the unary_union of the geoseries

    """


    # get box
    b = box(*gdf.total_bounds)

    # form unary union
    u = gdf.unary_union

    # diff of b and u
    dbu = geopandas.GeoDataFrame(geometry=[b.difference(u)])

    # explode
    _holes = dbu.explode()

    # hull
    hull = gdf.dissolve().convex_hull

    # return holes
    _holes =  _holes[_holes.within(hull.geometry[0])]

    return _holes


def fill_holes(gdf, largest=True, inplace=False):

    h = holes(gdf)
    if not inplace:
        gdf = gdf.copy()

    for index, row in h.iterrows():
        rdf = geopandas.GeoDataFrame(geometry=[row.geometry])
        neighbors = geopandas.sjoin(left_df=gdf, right_df=rdf, how='inner',
                                    op='intersects')
        if largest:
            left = neighbors[neighbors.area==neighbors.area.max()]
        else:
            left = neighbors[neighbors.area==neighbors.area.min()]
        tmpdf = pandas.concat([left, rdf]).dissolve()
        try:
            geom = tmpdf.loc[0, 'geometry']
            gdf.geometry[left.index] = geopandas.GeoDataFrame(geometry=[geom]).geometry.values
        except:
            print(index, tmpdf.shape)

    return gdf
def missing_interiors(gdf):
    contained = gdf.geometry.sindex.query_bulk(gdf.geometry,
                                               predicate="contains")
    pairs = []
    for pair in contained.T:
        i,j = pair
        if i != j:
            pairs.append((i,j))
    return pairs


def add_interiors(gdf, inplace=False):

    if not inplace:
        gdf = gdf.copy()

    contained = gdf.geometry.sindex.query_bulk(gdf.geometry,
                                               predicate="contains")
    a, k = contained.shape
    n = gdf.shape[0]
    if k > gdf.shape[0]:
        to_add = contained[:, contained[0] != contained[1]].T
        for add in to_add:
            i, j = add
            gdf.geometry[i] = gdf.geometry[i].difference(gdf.geometry[j])
    return gdf
