"""Sales Volumes, Costs & Price Data Frame Resource."""


from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from functools import cache, cached_property
from typing import ClassVar

from pandas import concat, DataFrame, MultiIndex, Series


__all__: tuple[str] = ('QueryableData', 'DF_VIEWS_CACHE', 'SalesVolCostPriceDF')


class QueryableData(StrEnum):
    """Queryable Data Content about Sales Volumes, Costs, Prices & metrics derivable from them."""

    SALES_VOL: str = 'sales-vol'

    AVG_COST: str = 'avg-cost'
    COGS: str = 'cogs'

    AVG_PRICE: str = 'avg-price'
    REV: str = 'rev'

    GROSS_PROFIT: str = 'gross-profit'
    GROSS_MARGIN: str = 'gross-margin'

    YOY_PCT_CHG_SALES_VOL: str = 'yoy-pct-chg-sales-vol'
    YOY_PCT_CHG_AVG_COST: str = 'yoy-pct-chg-avg-cost'
    YOY_PCT_CHG_AVG_PRICE: str = 'yoy-pct-chg-avg-price'
    YOY_ABS_CHG_REV: str = 'yoy-abs-chg-rev'
    YOY_PCT_CHG_REV: str = 'yoy-pct-chg-rev'
    YOY_PCTPT_CHG_GROSS_MARGIN: str = 'yoy-pctpt-chg-gross-margin'


class _DFViewsCache(dict):
    """Data frame views cache."""

    def record(self, view_df: DataFrame):
        """Record the view data frame in the cache."""
        self[id(view_df)] = view_df

DF_VIEWS_CACHE = _DFViewsCache()


@dataclass(init=True, repr=True, eq=True, order=False,
           unsafe_hash=False, frozen=False,
           match_args=True, kw_only=True,
           slots=False, weakref_slot=False)
class SalesVolCostPriceDF:
    """Sales Volume, Cost and Price Data Frame."""

    df: DataFrame

    biz_hierarchical_indexes: tuple[str]
    geo_hierarchical_indexes: tuple[str]

    prev_yr_sales_vol_col: str
    prev_yr_avg_cost_col: str
    prev_yr_avg_price_col: str

    curr_yr_sales_vol_col: str
    curr_yr_avg_cost_col: str
    curr_yr_avg_price_col: str

    PREV_YR_COGS_COL: ClassVar[str] = 'PrevYr_COGS'
    PREV_YR_REV_COL: ClassVar[str] = 'PrevYr_Rev'
    PREV_YR_GROSS_PROFIT_COL: ClassVar[str] = 'PrevYr_GrossProfit'
    PREV_YR_GROSS_MARGIN_COL: ClassVar[str] = 'PrevYr_GrossMargin'

    CURR_YR_COGS_COL: ClassVar[str] = 'CurrYr_COGS'
    CURR_YR_REV_COL: ClassVar[str] = 'CurrYr_Rev'
    CURR_YR_GROSS_PROFIT_COL: ClassVar[str] = 'CurrYr_GrossProfit'
    CURR_YR_GROSS_MARGIN_COL: ClassVar[str] = 'CurrYr_GrossMargin'

    PREV_YR_REV_PCT_COL: ClassVar[str] = 'PrevYr_RevPct'
    PREV_YR_GROSS_PROFIT_PCT_COL: ClassVar[str] = 'PrevYr_GrossProfitPct'

    CURR_YR_REV_PCT_COL: ClassVar[str] = 'CurrYr_RevPct'
    CURR_YR_GROSS_PROFIT_PCT_COL: ClassVar[str] = 'CurrYr_GrossProfitPct'

    YOY_PCT_CHG_SALES_VOL_COL: ClassVar[str] = 'YoY_PctChg_SalesVol'
    YOY_PCT_CHG_AVG_COST_COL: ClassVar[str] = 'YoY_PctChg_AvgCost'
    YOY_PCT_CHG_AVG_PRICE_COL: ClassVar[str] = 'YoY_PctChg_AvgPrice'
    YOY_ABS_CHG_REV_COL: ClassVar[str] = 'YoY_AbsChg_Rev'
    YOY_PCT_CHG_REV_COL: ClassVar[str] = 'YoY_PctChg_Rev'
    YOY_PCTPT_CHG_GROSS_MARGIN_COL: ClassVar[str] = 'YoY_PctPtChg_GrossMargin'

    _ROW_TYPE_INDEX_NAME: ClassVar[str] = 'RowType'
    _DETAIL_ROW_TYPE: ClassVar[str] = 'detail'
    _TOTAL_ROW_TYPE: ClassVar[str] = 'TOTAL'

    _ALL_FILTER_VALUE: ClassVar[str] = '__all__'

    def __post_init__(self):
        """Post-initialization: sort index & rearrange columns in logical order.
        And also build the business & geographical hierarchies."""
        # verify index names in precise order
        assert self.df.index.names == (index_level_names := list(self.biz_hierarchical_indexes) + list(self.geo_hierarchical_indexes)), \
            ValueError(f"Index names mismatch: {self.df.index.names} != {index_level_names}")

        # sort index & rearrange columns in logical order
        self.df: DataFrame = self.df.sort_index(axis='index',
                                                level=None,
                                                ascending=True,
                                                inplace=False,
                                                kind='quicksort',
                                                na_position='last',
                                                sort_remaining=True,
                                                ignore_index=False,
                                                key=None)[[self.prev_yr_sales_vol_col,
                                                           self.prev_yr_avg_cost_col,
                                                           self.prev_yr_avg_price_col,
                                                           self.curr_yr_sales_vol_col,
                                                           self.curr_yr_avg_cost_col,
                                                           self.curr_yr_avg_price_col]]

        # populate hierarchical parent dictionaries
        # by calling `biz_hierarchy` and `geo_hierarchy` once to cache
        self._n_biz_hierarchical_indexes: int = len(self.biz_hierarchical_indexes)
        self._biz_hierarchical_index_start: int = 0
        self._biz_hierarchical_index_end: int = self._n_biz_hierarchical_indexes
        self._biz_hierarchical_parent_dicts: list[dict[str, str | None]] = [{} for _ in range(self._n_biz_hierarchical_indexes)]
        self.biz_hierarchy  # noqa: B018

        self._n_geo_hierarchical_indexes: int = len(self.geo_hierarchical_indexes)
        self._geo_hierarchical_index_start: int = self._biz_hierarchical_index_end
        self._geo_hierarchical_index_end: int = self._geo_hierarchical_index_start + self._n_geo_hierarchical_indexes
        self._geo_hierarchical_parent_dicts: list[dict[str, str | None]] = [{} for _ in range(self._n_geo_hierarchical_indexes)]
        self.geo_hierarchy  # noqa: B018

    def __hash__(self) -> int:
        """Return hash from key attributes."""
        return hash((self.biz_hierarchical_indexes, self.geo_hierarchical_indexes,
                     self.prev_yr_sales_vol_col, self.prev_yr_avg_cost_col, self.prev_yr_avg_price_col,
                     self.curr_yr_sales_vol_col, self.curr_yr_avg_cost_col, self.curr_yr_avg_price_col))

    def _build_hierarchy(self,
                         hierarchical_index_level_names: tuple[str, ...],
                         hierarchical_parent_dicts: list[dict[str, str]]) -> dict[str, dict | list[str]] | list[str] | None:
        """Build nested dictionary for any hierarchy dynamically."""
        # get index start and end
        if hierarchical_index_level_names == self.biz_hierarchical_indexes:
            if not (n_indexes := self._n_biz_hierarchical_indexes):
                return

            index_start: int = self._biz_hierarchical_index_start
            index_end: int = self._biz_hierarchical_index_end

        else:
            assert hierarchical_index_level_names == self.geo_hierarchical_indexes

            if not (n_indexes := self._n_geo_hierarchical_indexes):
                return

            index_start: int = self._geo_hierarchical_index_start
            index_end: int = self._geo_hierarchical_index_end

        if n_indexes > 1:
            hierarchy: dict[str, dict | list[str]] = {}
        else:
            hierarchy: list[str] = []

        # build hierarchy
        for idx in self.df.index:
            # get the relevant levels for this hierarchy
            index_levels: tuple[str, ...] = idx[index_start:index_end]

            # build nested structure dynamically
            current_level: dict[str, dict | list[str]] | list[str] = hierarchy

            for i, index_level_value in enumerate(index_levels):
                if index_level_value not in current_level:
                    if i:
                        hierarchical_parent_index_level_value: str = index_levels[i - 1]
                    else:
                        hierarchical_parent_index_level_value = None
                    hierarchical_parent_dicts[i][index_level_value] = hierarchical_parent_index_level_value

                    if i < n_indexes - 2:
                        current_level[index_level_value] = {}

                    elif i == n_indexes - 2:
                        current_level[index_level_value] = []

                    else:
                        current_level.append(index_level_value)

                if i < n_indexes - 1:
                    current_level: dict[str, dict | list[str]] | list[str] = current_level[index_level_value]

        # sort the leaf lists
        self._sort_hierarchy_leaves(hierarchy)

        return hierarchy

    @staticmethod
    def _sort_hierarchy_leaves(hierarchy: dict | list):
        """Recursively sort leaf lists in hierarchy."""
        if isinstance(hierarchy, dict):
            for value in hierarchy.values():
                if isinstance(value, dict | list):
                    SalesVolCostPriceDF._sort_hierarchy_leaves(value)

        elif isinstance(hierarchy, list):
            hierarchy.sort()

    def _build_hierarchy_tuple(self,
                               hierarchical_index_level_names: tuple[str, ...],
                               hierarchical_parent_dicts: list[dict[str, str | None]],
                               filters: dict[str, str]) -> tuple[str, ...]:
        """Build tuple for any hierarchy dynamically."""
        result: list[str] = []

        # process from most specific to least specific level
        for i, hierarchical_index_level_name, hierarchical_parent_dict in zip(
                reversed(range(len(hierarchical_index_level_names))),
                reversed(hierarchical_index_level_names),
                reversed(hierarchical_parent_dicts), strict=True):
            if (index_filter_value := filters.get(hierarchical_index_level_name)) and (index_filter_value != self._ALL_FILTER_VALUE):
                result.insert(0, index_filter_value)

                if i:
                    filters[hierarchical_index_level_names[i - 1]] = hierarchical_parent_dict[index_filter_value]

            else:
                result.insert(0, self._ALL_FILTER_VALUE)

        return tuple(result)

    @cached_property
    def biz_hierarchy(self) -> dict:
        """Build nested dictionary for business hierarchy dynamically."""
        return self._build_hierarchy(hierarchical_index_level_names=self.biz_hierarchical_indexes,
                                     hierarchical_parent_dicts=self._biz_hierarchical_parent_dicts)

    def _biz_hierarchy_tuple(self, filters: dict[str, str]) -> tuple[str, ...]:
        """Build tuple for business hierarchy dynamically based on biz_hierarchical_indexes."""
        return self._build_hierarchy_tuple(hierarchical_index_level_names=self.biz_hierarchical_indexes,
                                           hierarchical_parent_dicts=self._biz_hierarchical_parent_dicts,
                                           filters=filters)

    @cached_property
    def geo_hierarchy(self) -> dict:
        """Build nested dictionary for geographical hierarchy dynamically."""
        return self._build_hierarchy(hierarchical_index_level_names=self.geo_hierarchical_indexes,
                                     hierarchical_parent_dicts=self._geo_hierarchical_parent_dicts)

    def _geo_hierarchy_tuple(self, filters: dict[str, str]) -> tuple[str, ...]:
        """Build tuple for geographical hierarchy dynamically based on geo_hierarchical_indexes."""
        return self._build_hierarchy_tuple(hierarchical_index_level_names=self.geo_hierarchical_indexes,
                                           hierarchical_parent_dicts=self._geo_hierarchical_parent_dicts,
                                           filters=filters)

    @cache
    def get_index_level_values(self, index_level_name: str, /) -> list[str]:
        """Get unique names for any hierarchy level by its name."""
        if index_level_name in self.biz_hierarchical_indexes:
            return sorted(self._biz_hierarchical_parent_dicts[self.biz_hierarchical_indexes.index(index_level_name)])

        if index_level_name in self.geo_hierarchical_indexes:
            return sorted(self._geo_hierarchical_parent_dicts[self.geo_hierarchical_indexes.index(index_level_name)])

        raise ValueError(f'Index level name "{index_level_name}" not found in hierarchy levels')

    @cache
    def view(self,
             biz_and_geo_filters: tuple[tuple[str, str], ...] | None = None,
             **other_biz_and_geo_filters: str) -> DataFrame:
        """View data with optional business & geographical filters."""
        # merge filters
        all_biz_and_geo_filters: dict[str, str] = other_biz_and_geo_filters
        if biz_and_geo_filters:
            all_biz_and_geo_filters.update(biz_and_geo_filters)

        bool_mask: Series | None = None

        for index_level_name in set(self.biz_hierarchical_indexes + self.geo_hierarchical_indexes).intersection(all_biz_and_geo_filters):
            if (index_filter_value := all_biz_and_geo_filters[index_level_name]):
                cond: Series = (self.df.index.get_level_values(level=index_level_name) == index_filter_value)

                if bool_mask is None:
                    bool_mask = cond
                else:
                    bool_mask &= cond

        view_df: DataFrame = self.df if bool_mask is None else self.df[bool_mask]

        # calculate COGS & Revenue columns
        view_df.loc[:, self.PREV_YR_COGS_COL] = (view_df[self.prev_yr_sales_vol_col] *
                                                 view_df[self.prev_yr_avg_cost_col])
        view_df.loc[:, self.PREV_YR_REV_COL] = (view_df[self.prev_yr_sales_vol_col] *
                                                view_df[self.prev_yr_avg_price_col])

        view_df.loc[:, self.CURR_YR_COGS_COL] = (view_df[self.curr_yr_sales_vol_col] *
                                                 view_df[self.curr_yr_avg_cost_col])
        view_df.loc[:, self.CURR_YR_REV_COL] = (view_df[self.curr_yr_sales_vol_col] *
                                                view_df[self.curr_yr_avg_price_col])

        # Create total row data frame with summary values
        total_row_df: DataFrame = DataFrame(
            data=[self._calc_sales_vol_cogs_cost_rev_price_cols(view_df)],
            index=MultiIndex.from_tuples(
                tuples=[self._biz_hierarchy_tuple(filters={index_name: all_biz_and_geo_filters[index_name]
                                                           for index_name in set(self.biz_hierarchical_indexes).intersection(all_biz_and_geo_filters)}) +
                        self._geo_hierarchy_tuple(filters={index_name: all_biz_and_geo_filters[index_name]
                                                           for index_name in set(self.geo_hierarchical_indexes).intersection(all_biz_and_geo_filters)})],
                sortorder=None, names=view_df.index.names),
            columns=view_df.columns,
            dtype=None, copy=None)

        # Create composite data frame with `RowType` as level-0 index column
        view_df: DataFrame = concat(objs=[total_row_df, view_df],
                                    axis='index',
                                    join='outer',
                                    ignore_index=False,
                                    keys=[self._TOTAL_ROW_TYPE, self._DETAIL_ROW_TYPE],
                                    levels=None,
                                    names=[self._ROW_TYPE_INDEX_NAME] + list(view_df.index.names),
                                    verify_integrity=True,
                                    sort=False,
                                    copy=False)

        self._complete_df(view_df)

        return view_df

    def _calc_sales_vol_cogs_cost_rev_price_cols(self, df: DataFrame, /) -> Series:
        """Calculate COGS, Average Cost per Unit, Revenue, and Average Price per Unit columns."""
        prev_yr_sales_vol: int = df[self.prev_yr_sales_vol_col].sum()
        prev_yr_cogs: float = df[self.PREV_YR_COGS_COL].sum()
        prev_yr_avg_cost: float = prev_yr_cogs / prev_yr_sales_vol
        prev_yr_rev: float = df[self.PREV_YR_REV_COL].sum()
        prev_yr_avg_price: float = prev_yr_rev / prev_yr_sales_vol

        curr_yr_sales_vol: int = df[self.curr_yr_sales_vol_col].sum()
        curr_yr_cogs: float = df[self.CURR_YR_COGS_COL].sum()
        curr_yr_avg_cost: float = curr_yr_cogs / curr_yr_sales_vol
        curr_yr_rev: float = df[self.CURR_YR_REV_COL].sum()
        curr_yr_avg_price: float = curr_yr_rev / curr_yr_sales_vol

        return Series(data={self.prev_yr_sales_vol_col: prev_yr_sales_vol,
                            self.prev_yr_avg_cost_col: prev_yr_avg_cost,
                            self.PREV_YR_COGS_COL: prev_yr_cogs,
                            self.prev_yr_avg_price_col: prev_yr_avg_price,
                            self.PREV_YR_REV_COL: prev_yr_rev,

                            self.curr_yr_sales_vol_col: curr_yr_sales_vol,
                            self.curr_yr_avg_cost_col: curr_yr_avg_cost,
                            self.CURR_YR_COGS_COL: curr_yr_cogs,
                            self.curr_yr_avg_price_col: curr_yr_avg_price,
                            self.CURR_YR_REV_COL: curr_yr_rev},

                      index=None, dtype=None, name=None, copy=None)

    def _complete_df(self, df: DataFrame, /):
        """Complete data frame with additional columns."""
        df.loc[:, self.PREV_YR_REV_PCT_COL] = 100 * (df[self.PREV_YR_REV_COL] /
                                                     df.loc[self._TOTAL_ROW_TYPE][self.PREV_YR_REV_COL].iloc[0])

        df.loc[:, self.PREV_YR_GROSS_PROFIT_COL] = (df[self.PREV_YR_REV_COL] -
                                                    df[self.PREV_YR_COGS_COL])
        df.loc[:, self.PREV_YR_GROSS_PROFIT_PCT_COL] = 100 * (df[self.PREV_YR_GROSS_PROFIT_COL] /
                                                              df.loc[self._TOTAL_ROW_TYPE][self.PREV_YR_GROSS_PROFIT_COL].iloc[0])

        df.loc[:, self.PREV_YR_GROSS_MARGIN_COL] = (df[self.PREV_YR_GROSS_PROFIT_COL] /
                                                    df[self.PREV_YR_REV_COL])

        df.loc[:, self.CURR_YR_REV_PCT_COL] = 100 * (df[self.CURR_YR_REV_COL] /
                                                     df.loc[self._TOTAL_ROW_TYPE][self.CURR_YR_REV_COL].iloc[0])

        df.loc[:, self.CURR_YR_GROSS_PROFIT_COL] = (df[self.CURR_YR_REV_COL] -
                                                    df[self.CURR_YR_COGS_COL])
        df.loc[:, self.CURR_YR_GROSS_PROFIT_PCT_COL] = 100 * (df[self.CURR_YR_GROSS_PROFIT_COL] /
                                                              df.loc[self._TOTAL_ROW_TYPE][self.CURR_YR_GROSS_PROFIT_COL].iloc[0])

        df.loc[:, self.CURR_YR_GROSS_MARGIN_COL] = (df[self.CURR_YR_GROSS_PROFIT_COL] /
                                                    df[self.CURR_YR_REV_COL])

        df.loc[:, self.YOY_PCT_CHG_SALES_VOL_COL] = 100 * ((df[self.curr_yr_sales_vol_col] /
                                                            df[self.prev_yr_sales_vol_col]) - 1)
        df.loc[:, self.YOY_PCT_CHG_AVG_COST_COL] = 100 * ((df[self.curr_yr_avg_cost_col] /
                                                           df[self.prev_yr_avg_cost_col]) - 1)
        df.loc[:, self.YOY_PCT_CHG_AVG_PRICE_COL] = 100 * ((df[self.curr_yr_avg_price_col] /
                                                            df[self.prev_yr_avg_price_col]) - 1)
        df.loc[:, self.YOY_ABS_CHG_REV_COL] = (df[self.CURR_YR_REV_COL] -
                                               df[self.PREV_YR_REV_COL])
        df.loc[:, self.YOY_PCT_CHG_REV_COL] = 100 * ((df[self.CURR_YR_REV_COL] /
                                                      df[self.PREV_YR_REV_COL]) - 1)
        df.loc[:, self.YOY_PCTPT_CHG_GROSS_MARGIN_COL] = (df[self.CURR_YR_GROSS_MARGIN_COL] -
                                                          df[self.PREV_YR_GROSS_MARGIN_COL])

    @cache
    def query_single_data_point(self, queryable_data: QueryableData, /, *,
                                prev_yr: bool = False,
                                biz_and_geo_filters: tuple[tuple[str, str], ...] | None = None,
                                **other_biz_and_geo_filters: str) -> int | float:
        """Query a single data point."""
        total_row_df: Series = self.view(biz_and_geo_filters=biz_and_geo_filters,
                                         **other_biz_and_geo_filters).loc[self._TOTAL_ROW_TYPE]
        DF_VIEWS_CACHE.record(total_row_df)

        total_row: Series = total_row_df.iloc[0]

        match queryable_data:
            case QueryableData.SALES_VOL:
                return total_row[self.prev_yr_sales_vol_col
                                 if prev_yr
                                 else self.curr_yr_sales_vol_col]

            case QueryableData.AVG_COST:
                return total_row[self.prev_yr_avg_cost_col
                                 if prev_yr
                                 else self.curr_yr_avg_cost_col]

            case QueryableData.COGS:
                return total_row[self.PREV_YR_COGS_COL
                                 if prev_yr
                                 else self.CURR_YR_COGS_COL]

            case QueryableData.AVG_PRICE:
                return total_row[self.prev_yr_avg_price_col
                                 if prev_yr
                                 else self.curr_yr_avg_price_col]

            case QueryableData.REV:
                return total_row[self.PREV_YR_REV_COL
                                 if prev_yr
                                 else self.CURR_YR_REV_COL]

            case QueryableData.GROSS_PROFIT:
                return total_row[self.PREV_YR_GROSS_PROFIT_COL
                                 if prev_yr
                                 else self.CURR_YR_GROSS_PROFIT_COL]

            case QueryableData.GROSS_MARGIN:
                return total_row[self.PREV_YR_GROSS_MARGIN_COL
                                 if prev_yr
                                 else self.CURR_YR_GROSS_MARGIN_COL]

            case QueryableData.YOY_PCT_CHG_SALES_VOL:
                return total_row[self.YOY_PCT_CHG_SALES_VOL_COL]

            case QueryableData.YOY_PCT_CHG_AVG_COST:
                return total_row[self.YOY_PCT_CHG_AVG_COST_COL]

            case QueryableData.YOY_PCT_CHG_AVG_PRICE:
                return total_row[self.YOY_PCT_CHG_AVG_PRICE_COL]

            case QueryableData.YOY_ABS_CHG_REV:
                return total_row[self.YOY_ABS_CHG_REV_COL]

            case QueryableData.YOY_PCT_CHG_REV:
                return total_row[self.YOY_PCT_CHG_REV_COL]

            case QueryableData.YOY_PCTPT_CHG_GROSS_MARGIN:
                return total_row[self.YOY_PCTPT_CHG_GROSS_MARGIN_COL]

            case _:
                raise ValueError(f'Invalid `QueryableData`: {queryable_data}')

    @cache
    def highlight_good_and_bad_performers(self, n: int = 3,
                                          biz_and_geo_filters: tuple[tuple[str, str], ...] | None = None,
                                          **other_biz_and_geo_filters: str) -> DataFrame:
        """Highlight `n` best and `n` worst financial performers per dimension applicable for drill-down analyses."""
        # get filtered view and its total row and detail rows
        view_df: DataFrame = self.view(biz_and_geo_filters=biz_and_geo_filters, **other_biz_and_geo_filters)

        total_row_df: DataFrame = view_df.loc[self._TOTAL_ROW_TYPE]
        total_row_index_names: list[str] = total_row_df.index.names
        total_row_index_values: tuple[str, ...] = total_row_df.index[0]

        detail_df: DataFrame = view_df.loc[self._DETAIL_ROW_TYPE]

        # collect all highlight rows
        highlight_rows: list[Series] = []

        # identify dimensions for drill-down analyses
        dimensions_for_drilldown: Iterable[str] = (index_name
                                                   for index_name, index_filter_value
                                                   in zip(total_row_df.index.names, total_row_df.index[0], strict=True)
                                                   if index_filter_value == self._ALL_FILTER_VALUE)

        for dimension in dimensions_for_drilldown:
            # group by the dimension and calculate summary statistics
            grouped_df: DataFrame = detail_df.groupby(
                level=dimension,
                as_index=True,
                sort=False,
                group_keys=True,
                dropna=True).apply(func=self._calc_sales_vol_cogs_cost_rev_price_cols,
                                   include_groups=True)

            if (n_for_dimension := min(n, len(grouped_df) // 2)):  # if worth drilling down
                # enhance grouped data frame index
                # to match structure of total row data frame index
                grouped_df_index_name: str = grouped_df.index.name
                grouped_df.index: MultiIndex = MultiIndex.from_tuples(
                    tuples=[tuple((grouped_df_index_value
                                   if total_row_index_name == grouped_df_index_name
                                   else total_row_index_value)
                                  for total_row_index_name, total_row_index_value
                                  in zip(total_row_index_names, total_row_index_values, strict=True))
                            for grouped_df_index_value in grouped_df.index],
                    sortorder=None,
                    names=total_row_df.index.names)

                # add total row to the grouped data frame
                summary_by_dimension_row_type: str = f'by-{dimension}'

                summary_view_df: DataFrame = concat(objs=[total_row_df[grouped_df.columns], grouped_df],
                                                    axis='index',
                                                    join='outer',
                                                    ignore_index=False,
                                                    keys=[self._TOTAL_ROW_TYPE, summary_by_dimension_row_type],
                                                    levels=None,
                                                    names=[self._ROW_TYPE_INDEX_NAME] + list(total_row_df.index.names),
                                                    verify_integrity=True,
                                                    sort=False,
                                                    copy=False)

                # complete the grouped data frame
                self._complete_df(summary_view_df)

                summary_view_df_without_total_row: DataFrame = \
                    summary_view_df.loc[summary_by_dimension_row_type]

                # Precompute grouped label prefix and dimension position
                label_prefix: str = summary_by_dimension_row_type
                index_names_for_dim: list[str] = list(summary_view_df_without_total_row.index.names)
                grouped_dim_pos: int = index_names_for_dim.index(grouped_df_index_name)

                # highest and lowest revenue amount contributors (current year)
                highlight_rows.extend(self._get_highest_and_lowest_rev_contributors(
                    summary_view_df_without_total_row=summary_view_df_without_total_row,
                    label_prefix=label_prefix,
                    grouped_dim_pos=grouped_dim_pos,
                    n_for_dimension=n_for_dimension))

                # highest and lowest revenue percentage growers
                highlight_rows.extend(self._get_highest_and_lowest_rev_growers(
                    summary_view_df_without_total_row=summary_view_df_without_total_row,
                    label_prefix=label_prefix,
                    grouped_dim_pos=grouped_dim_pos,
                    n_for_dimension=n_for_dimension))

                # highest and lowest gross profit contributors
                highlight_rows.extend(self._get_highest_and_lowest_gross_profit_contributors(
                    summary_view_df_without_total_row=summary_view_df_without_total_row,
                    label_prefix=label_prefix,
                    grouped_dim_pos=grouped_dim_pos,
                    n_for_dimension=n_for_dimension))

                # highest and lowest gross margin averagers (current year)
                highlight_rows.extend(self._get_highest_and_lowest_gross_margin_averagers(
                    summary_view_df_without_total_row=summary_view_df_without_total_row,
                    label_prefix=label_prefix,
                    grouped_dim_pos=grouped_dim_pos,
                    n_for_dimension=n_for_dimension))

                # highest and lowest gross margin improvers
                highlight_rows.extend(self._get_highest_and_lowest_gross_margin_improvers(
                    summary_view_df_without_total_row=summary_view_df_without_total_row,
                    label_prefix=label_prefix,
                    grouped_dim_pos=grouped_dim_pos,
                    n_for_dimension=n_for_dimension))

        if highlight_rows:
            # combine total row with all highlight rows

            # create data frame from highlight rows, using series names as MultiIndex
            highlight_df: DataFrame = DataFrame(data=highlight_rows,
                                                columns=view_df.columns,
                                                dtype=None, copy=None)

            # set the index names properly
            highlight_df.index.names = [self._ROW_TYPE_INDEX_NAME] + total_row_index_names

            # combine total row with highlight rows (both now have same structure)
            result_df: DataFrame = concat(objs=[view_df.iloc[[0]],  # preserve RowType index
                                                highlight_df],
                                          axis='index',
                                          join='outer',
                                          ignore_index=False,
                                          keys=None,
                                          levels=None,
                                          names=None,  # let pandas preserve existing names
                                          verify_integrity=True,
                                          sort=False,
                                          copy=False)

        else:
            # if no highlight rows, just return the total row
            result_df: DataFrame = total_row_df

        DF_VIEWS_CACHE.record(result_df)

        return result_df

    def _get_highest_and_lowest_rev_contributors(
            self,
            summary_view_df_without_total_row: DataFrame,
            label_prefix: str,
            grouped_dim_pos: int,
            n_for_dimension: int = 3) -> list[Series]:
        """Get highest and lowest revenue contributors (current year)."""
        rev_contributors_df: DataFrame = (
            summary_view_df_without_total_row
            .sort_values(by=self.CURR_YR_REV_PCT_COL,
                         axis='index',
                         ascending=False,
                         inplace=False,
                         kind='quicksort',
                         na_position='last',
                         ignore_index=False,
                         key=None))

        highlight_rows: list[Series] = []

        for i, (idx, row) in enumerate(rev_contributors_df.head(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---highest-revenue---{i + 1}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        for i, (idx, row) in enumerate(rev_contributors_df.tail(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---lowest-revenue---{n_for_dimension - i}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        return highlight_rows

    def _get_highest_and_lowest_rev_growers(
            self,
            summary_view_df_without_total_row: DataFrame,
            label_prefix: str,
            grouped_dim_pos: int,
            n_for_dimension: int = 3) -> list[Series]:
        """Get highest and lowest revenue growers."""
        rev_growers_df: DataFrame = (
            summary_view_df_without_total_row
            .sort_values(by=self.YOY_PCT_CHG_REV_COL,
                         axis='index',
                         ascending=False,
                         inplace=False,
                         kind='quicksort',
                         na_position='last',
                         ignore_index=False,
                         key=None))

        highlight_rows: list[Series] = []

        for i, (idx, row) in enumerate(rev_growers_df.head(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---fastest-revenue-grower---{i + 1}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        for i, (idx, row) in enumerate(rev_growers_df.tail(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---slowest-revenue-grower---{n_for_dimension - i}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        return highlight_rows

    def _get_highest_and_lowest_gross_profit_contributors(
            self,
            summary_view_df_without_total_row: DataFrame,
            label_prefix: str,
            grouped_dim_pos: int,
            n_for_dimension: int = 3) -> list[Series]:
        """Get highest and lowest gross profit contributors."""
        gross_profit_contributors_df: DataFrame = (
            summary_view_df_without_total_row
            .sort_values(by=self.CURR_YR_GROSS_PROFIT_PCT_COL,
                         axis='index',
                         ascending=False,
                         inplace=False,
                         kind='quicksort',
                         na_position='last',
                         ignore_index=False,
                         key=None))

        highlight_rows: list[Series] = []

        for i, (idx, row) in enumerate(gross_profit_contributors_df.head(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---highest-gross-profit---{i + 1}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        for i, (idx, row) in enumerate(gross_profit_contributors_df.tail(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---lowest-gross-profit---{n_for_dimension - i}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        return highlight_rows

    def _get_highest_and_lowest_gross_margin_averagers(
            self,
            summary_view_df_without_total_row: DataFrame,
            label_prefix: str,
            grouped_dim_pos: int,
            n_for_dimension: int = 3) -> list[Series]:
        """Get highest and lowest gross margin averagers."""
        margin_averagers_df: DataFrame = (
            summary_view_df_without_total_row
            .sort_values(by=self.CURR_YR_GROSS_MARGIN_COL,
                         axis='index',
                         ascending=False,
                         inplace=False,
                         kind='quicksort',
                         na_position='last',
                         ignore_index=False,
                         key=None))

        highlight_rows: list[Series] = []

        for i, (idx, row) in enumerate(margin_averagers_df.head(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---best-gross-margin---{i + 1}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        for i, (idx, row) in enumerate(margin_averagers_df.tail(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---worst-gross-margin---{n_for_dimension - i}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        return highlight_rows

    def _get_highest_and_lowest_gross_margin_improvers(
            self,
            summary_view_df_without_total_row: DataFrame,
            label_prefix: str,
            grouped_dim_pos: int,
            n_for_dimension: int = 3) -> list[Series]:
        """Get highest and lowest gross margin improvers."""
        margin_improvers_df: DataFrame = (
            summary_view_df_without_total_row
            .sort_values(by=self.YOY_PCTPT_CHG_GROSS_MARGIN_COL,
                         axis='index',
                         ascending=False,
                         inplace=False,
                         kind='quicksort',
                         na_position='last',
                         ignore_index=False,
                         key=None))

        highlight_rows: list[Series] = []

        for i, (idx, row) in enumerate(margin_improvers_df.head(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---most-gross-margin-improver---{i + 1}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        for i, (idx, row) in enumerate(margin_improvers_df.tail(n_for_dimension).iterrows()):
            grouped_dim_value = idx[grouped_dim_pos]
            highlight_rows.append(
                Series(data=row.values,
                       index=row.index,
                       dtype=None,
                       name=(f'{label_prefix}---least-gross-margin-improver---{n_for_dimension - i}---is---"{grouped_dim_value}"',) + idx,
                       copy=None))

        return highlight_rows
