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


class DFViewsCache(dict):
    """Data frame views cache."""

    def record(self, view_df: DataFrame):
        """Record the view data frame in the cache."""
        self[id(view_df)] = view_df

DF_VIEWS_CACHE = DFViewsCache()


@dataclass(init=True, repr=True, eq=True, order=False,
           unsafe_hash=False, frozen=False,
           match_args=True, kw_only=True,
           slots=False, weakref_slot=False)
class SalesVolCostPriceDF:
    """Sales Volume, Cost and Price Data Frame."""

    df: DataFrame

    biz_hierarchy_indexes: tuple[str]
    geo_hierarchy_indexes: tuple[str]

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

        # Initialize relationship dictionaries dynamically
        self._biz_relationship_dicts: list[dict[str, str]] = [{} for _ in range(len(self.biz_hierarchy_indexes) - 1)]
        self._geo_relationship_dicts: list[dict[str, str]] = [{} for _ in range(len(self.geo_hierarchy_indexes) - 1)]

        self.biz_hierarchy  # call once to cache
        self.geo_hierarchy  # call once to cache

    def __hash__(self) -> int:
        return hash((self.biz_hierarchy_indexes,
                     self.geo_hierarchy_indexes,

                     self.prev_yr_sales_vol_col,
                     self.prev_yr_avg_cost_col,
                     self.prev_yr_avg_price_col,

                     self.curr_yr_sales_vol_col,
                     self.curr_yr_avg_cost_col,
                     self.curr_yr_avg_price_col))

    def _build_hierarchy(self, hierarchy_indexes: tuple[str, ...], relationship_dicts: list[dict[str, str]]) -> dict:
        """Build nested dictionary for any hierarchy dynamically."""
        hierarchy: dict = {}

        for idx in self.df.index:
            # Get the relevant levels for this hierarchy
            if hierarchy_indexes == self.biz_hierarchy_indexes:
                levels = idx[:len(hierarchy_indexes)]
            else:  # geo hierarchy
                geo_start = len(self.biz_hierarchy_indexes)
                geo_end = geo_start + len(hierarchy_indexes)
                levels = idx[geo_start:geo_end]

            # Build nested structure dynamically
            current_level = hierarchy
            for i, level_value in enumerate(levels):
                if level_value not in current_level:
                    if i == len(levels) - 1:  # Last level - store as list
                        current_level[level_value] = []
                    else:  # Intermediate level - store as dict
                        current_level[level_value] = {}
                        # Store parent-child relationship
                        if i < len(relationship_dicts):
                            parent_value = levels[i - 1] if i > 0 else None
                            relationship_dicts[i][level_value] = parent_value

                current_level = current_level[level_value]

        # Sort the leaf lists
        self._sort_hierarchy_leaves(hierarchy)

        return hierarchy

    def _sort_hierarchy_leaves(self, hierarchy: dict) -> None:
        """Recursively sort leaf lists in hierarchy."""
        for value in hierarchy.values():
            if isinstance(value, list):
                value.sort()
            elif isinstance(value, dict):
                self._sort_hierarchy_leaves(value)

    def _build_hierarchy_tuple(self, hierarchy_indexes: tuple[str, ...], relationship_dicts: list[dict[str, str]], filters: dict[str, str | None]) -> tuple[str, ...]:
        """Build tuple for any hierarchy dynamically."""
        result = []

        # Process from most specific to least specific level
        for i in range(len(hierarchy_indexes) - 1, -1, -1):
            level_name = hierarchy_indexes[i]
            value = filters.get(level_name)

            if value and value != self._ALL_FILTER_VALUE:
                result.insert(0, value)
            else:
                result.insert(0, self._ALL_FILTER_VALUE)

        return tuple(result)

    @cached_property
    def biz_hierarchy(self) -> dict:
        """Build nested dictionary for business hierarchy dynamically."""
        return self._build_hierarchy(self.biz_hierarchy_indexes, self._biz_relationship_dicts)

    @cache
    def business_hierarchy_tuple(self, **filters: str | None) -> tuple[str, ...]:
        """Build tuple for business hierarchy dynamically based on biz_hierarchy_indexes."""
        return self._build_hierarchy_tuple(self.biz_hierarchy_indexes, self._biz_relationship_dicts, filters)

    def get_biz_level_names(self, level_index: int) -> set[str]:
        """Get unique names for a specific business hierarchy level."""
        if 0 <= level_index < len(self.biz_hierarchy_indexes):
            return set(self.df.index.get_level_values(self.biz_hierarchy_indexes[level_index]))
        raise IndexError(f"Business level index {level_index} out of range [0, {len(self.biz_hierarchy_indexes)})")

    def get_biz_level_names_by_name(self, level_name: str) -> set[str]:
        """Get unique names for a business hierarchy level by its name."""
        if level_name in self.biz_hierarchy_indexes:
            return set(self.df.index.get_level_values(level_name))
        raise ValueError(f"Business level name '{level_name}' not found in {self.biz_hierarchy_indexes}")

    @cached_property
    def geo_hierarchy(self) -> dict:
        """Build nested dictionary for geographical hierarchy dynamically."""
        return self._build_hierarchy(self.geo_hierarchy_indexes, self._geo_relationship_dicts)

    @cache
    def geographical_hierarchy_tuple(self, **filters: str | None) -> tuple[str, ...]:
        """Build tuple for geographical hierarchy dynamically based on geo_hierarchy_indexes."""
        return self._build_hierarchy_tuple(self.geo_hierarchy_indexes, self._geo_relationship_dicts, filters)

    def get_geo_level_names(self, level_index: int) -> set[str]:
        """Get unique names for a specific geographical hierarchy level."""
        if 0 <= level_index < len(self.geo_hierarchy_indexes):
            return set(self.df.index.get_level_values(self.geo_hierarchy_indexes[level_index]))
        raise IndexError(f"Geographical level index {level_index} out of range [0, {len(self.geo_hierarchy_indexes)})")

    def get_geo_level_names_by_name(self, level_name: str) -> set[str]:
        """Get unique names for a geographical hierarchy level by its name."""
        if level_name in self.geo_hierarchy_indexes:
            return set(self.df.index.get_level_values(level_name))
        raise ValueError(f"Geographical level name '{level_name}' not found in {self.geo_hierarchy_indexes}")

    def get_level_names(self, level_name: str) -> set[str]:
        """Get unique names for any hierarchy level by its name."""
        all_level_names = list(self.biz_hierarchy_indexes) + list(self.geo_hierarchy_indexes)
        if level_name in all_level_names:
            return set(self.df.index.get_level_values(level_name))
        raise ValueError(f"Level name '{level_name}' not found in hierarchy levels: {all_level_names}")

    @cache
    def view(self, biz_and_geo_filters: tuple[tuple[str, str], ...] | None = None, **other_biz_and_geo_filters: str) -> DataFrame:
        """View data with optional business & geographical filters."""
        # filter data
        indexes: list[str] = list(self.biz_hierarchy_indexes) + list(self.geo_hierarchy_indexes)

        # Merge filters from both sources
        all_biz_and_geo_filters = {}
        if biz_and_geo_filters:
            all_biz_and_geo_filters.update(dict(biz_and_geo_filters))
        all_biz_and_geo_filters.update(other_biz_and_geo_filters)

        filters: dict[str, str | None] = {}
        for name in self.biz_hierarchy_indexes:
            filters[name] = all_biz_and_geo_filters.get(name)
        for name in self.geo_hierarchy_indexes:
            filters[name] = all_biz_and_geo_filters.get(name)

        indexer = self.df.index
        mask = None
        for lvl_name in indexes:
            value = filters[lvl_name]
            if value is not None and value != self._ALL_FILTER_VALUE:
                cond = (indexer.get_level_values(lvl_name) == value)
                mask = cond if mask is None else (mask & cond)
        if mask is None:
            view_df: DataFrame = self.df
        else:
            view_df: DataFrame = self.df[mask]

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
                tuples=[self.business_hierarchy_tuple(**{name: all_biz_and_geo_filters.get(name) for name in self.biz_hierarchy_indexes}) +
                        self.geographical_hierarchy_tuple(**{name: all_biz_and_geo_filters.get(name) for name in self.geo_hierarchy_indexes})],
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
        """Query a single financial data point."""
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
        total_row_indexes: list[str] = total_row_df.index.names
        total_row_index_values: tuple[str, str, str, str, str, str, str, str] = total_row_df.index[0]

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
                                  in zip(total_row_indexes, total_row_index_values, strict=True))
                            for grouped_df_index_value in grouped_df.index],
                    sortorder=None,
                    names=total_row_df.index.names)

                # add total row to the grouped data frame
                summary_by_dimension_row_type: str = f'by-{dimension}'

                summary_view_df: DataFrame = concat(objs=[total_row_df[grouped_df.columns], grouped_df],
                                                    axis='index',
                                                    join='outer',
                                                    ignore_index=False,
                                                    keys=[self._TOTAL_ROW_TYPE,
                                                          summary_by_dimension_row_type],
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
                indexes_for_dim: list[str] = list(summary_view_df_without_total_row.index.names)
                grouped_dim_pos: int = indexes_for_dim.index(grouped_df_index_name)

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
            highlight_df.index.names = [self._ROW_TYPE_INDEX_NAME] + total_row_indexes

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
