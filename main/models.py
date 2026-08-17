from django.db import models
from django.core.cache import cache
from django.utils import timezone
import statistics
import pandas as pd
from django.db import connections



class Home(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    img = models.ImageField(upload_to='media')

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        verbose_name_plural = 'Home'


# ==============================================================================
# LAYER 1 — LOCAL CONFIGURATION MODELS (stored in local SQLite, editable via Admin)
# ==============================================================================

class CalculationParameter(models.Model):
    """
    Admin-editable numeric/string parameters used by the calculation engine.
    Instead of hardcoding thresholds, multipliers, or rates in Python,
    store them here and pull them at runtime.

    Example rows:
        key='profit_margin_target'  value='0.25'  param_type='float'
        key='vat_rate'              value='0.20'  param_type='float'
        key='currency_symbol'       value='$'     param_type='string'
        key='low_stock_threshold'   value='50'    param_type='integer'
    """
    PARAM_TYPES = [
        ('float', 'Float (decimal number)'),
        ('integer', 'Integer (whole number)'),
        ('string', 'String (text)'),
        ('boolean', 'Boolean (true/false)'),
        ('json', 'JSON (structured data)'),
    ]

    key = models.CharField(max_length=100, unique=True,
                           help_text="Python-safe identifier used in code, e.g. 'vat_rate'")
    value = models.TextField(help_text="The parameter value as text")
    param_type = models.CharField(max_length=20, choices=PARAM_TYPES, default='float')
    description = models.TextField(blank=True, help_text="What this parameter controls")
    category = models.CharField(max_length=50, blank=True,
                                help_text="Group related params, e.g. 'Financial', 'Inventory'")
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'key']
        verbose_name = "Calculation Parameter"
        verbose_name_plural = "Calculation Parameters"

    def __str__(self):
        return f"{self.key} = {self.value} ({self.param_type})"

    def typed_value(self):
        """Return value cast to its declared Python type."""
        import json
        converters = {
            'float': float,
            'integer': int,
            'string': str,
            'boolean': lambda v: v.strip().lower() in ('true', '1', 'yes'),
            'json': json.loads,
        }
        try:
            return converters[self.param_type](self.value)
        except (ValueError, TypeError, KeyError):
            return self.value


class DataSourceConfig(models.Model):
    """
    Admin-configurable SQL queries / table names for the external DB.
    Lets admins adjust which data gets pulled without touching Python code.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    sql_query = models.TextField(
        help_text="Raw SQL query executed against the external SQL Server database. "
                  "Use %(param)s style placeholders for safe parameterization."
    )
    is_active = models.BooleanField(default=True)
    cache_timeout_seconds = models.PositiveIntegerField(
        default=300,
        help_text="Seconds to cache query results (0 = no cache)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Data Source Query"
        verbose_name_plural = "Data Source Queries"

    def __str__(self):
        return self.name


class Report(models.Model):
    """
    Admin-configurable report definitions.
    Links a data source query to a calculation and a template.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Used in the URL: /reports/<slug>/")
    data_source = models.ForeignKey(DataSourceConfig, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    calculation_type = models.CharField(
        max_length=50,
        choices=[
            ('sales_summary', 'Sales Summary'),
            ('inventory_analysis', 'Inventory Analysis'),
            ('profit_margin', 'Profit Margin Report'),
            ('trend_analysis', 'Trend Analysis'),
            ('custom', 'Custom (uses slug to find calculator)'),
        ],
        default='sales_summary'
    )
    is_active = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    def __str__(self):
        return self.name


# ==============================================================================
# LAYER 2 — EXTERNAL DB PROXY MODELS (read-only, map to SQL Server tables)
# Set managed=False so Django never tries to CREATE/ALTER these tables.
# ==============================================================================

class SalesRecord(models.Model):
    """
    Maps to an existing table in your external SQL Server.
    Change field names / table name to match your actual schema.
    """

    # id = models.IntegerField()
    Branch = models.SmallIntegerField()
    ClientID = models.IntegerField(primary_key=True)
    Name = models.CharField(max_length=500)
    Address = models.CharField(max_length=500)
    Phones = models.CharField(max_length=200)
    AgreementNumber = models.CharField(max_length=150)
    Currency = models.CharField(max_length=3)
    SubDoc = models.SmallIntegerField()
    Balance = models.DecimalField()
    PastPercent0 = models.DecimalField()
    PastPercent90 = models.DecimalField()
    PastAmount = models.DecimalField()
    PastDays = models.SmallIntegerField()
    MaturityDay = models.SmallIntegerField()
    IndBranch = models.CharField(max_length=200)
    IndBranchGroup = models.CharField(max_length=200)
    AgreementPercent = models.DecimalField()
    Deposits = models.CharField()
    FutureIncomeAmount = models.DecimalField()
    PassiveAmount = models.DecimalField()
    Ledger = models.CharField(max_length=10)
    NewLedger = models.CharField(max_length=10)
    BalanceEQ = models.DecimalField()
    PastPercent0_EQ = models.DecimalField()
    PastPercent90_EQ = models.DecimalField()
    PastAmountEQ = models.DecimalField()
    CommissionAmountToPay = models.DecimalField()
    ComPastDays = models.IntegerField()
    LastPercent = models.DecimalField()
    PercentAmountToPay = models.DecimalField()
    ReservePercent = models.DecimalField()
    DocID = models.IntegerField()

    class Meta:
        managed = False          # ← Django won't touch this table in migrations
        db_table = 'PastDueLoanRazm'   # ← exact SQL Server table name
        app_label = 'external_source'     # ← router sends queries to external_db

    def __str__(self):
        return f"Sale #{self.ClientID} — {self.Name}"

    # Calculated properties on individual rows:
    # @property
    # def revenue(self):
    #     return self.quantity * self.unit_price

    # @property
    # def gross_profit(self):
    #     return self.quantity * (self.unit_price - self.cost_price)

    # @property
    # def margin_pct(self):
    #     if self.unit_price == 0:
    #         return 0
    #     return ((self.unit_price - self.cost_price) / self.unit_price) * 100


# ==============================================================================
# LAYER 3 — CALCULATION CLASSES
#
# These are plain Python classes living in models.py.
# They have NO database table — Django is fine with that.
# They receive data (from ORM queries, raw SQL, or other services),
# perform calculations, and return structured result dictionaries.
#
# WHY in models.py?
#   • Keeps data + logic in one layer
#   • Views stay thin (just call calculator, pass result to template)
#   • Easy to unit-test in isolation
#   • Can import and reuse across multiple views
# ==============================================================================

class DataToPandasDataset:

    def __init__(self):
        self.dt

    # Fetches data from external database and stores to pandas dataframe
    def load_loans_dataframe(self, query: str="",  table: str="", params=None,) -> pd.DataFrame:
        if query is "":
            query = f"SELECT * FROM {table}"
        
        with connections['external_db'].cursor() as cursor:
            cursor.execute(query, params or [])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        
        return pd.DataFrame.from_records(rows, columns=columns)

    def dt(self):
        dt = self.load_loans_dataframe("","","PastDueLoanRazm")
    


class ParameterStore:
    """
    Lightweight helper that loads CalculationParameter rows from local DB
    and exposes them as typed Python values.
    Cached so the DB isn't hit on every request.
    """
    _cache_key = 'param_store_all'

    @classmethod
    def get(cls, key: str, default=None):
        """Get a single parameter by key, typed."""
        params = cls._load_all()
        return params.get(key, default)

    @classmethod
    def _load_all(cls) -> dict:
        cached = cache.get(cls._cache_key)
        if cached:
            return cached
        params = {p.key: p.typed_value() for p in CalculationParameter.objects.all()}
        cache.set(cls._cache_key, params, timeout=120)
        return params

    @classmethod
    def invalidate(cls):
        cache.delete(cls._cache_key)


class CalculationEngine:
    """
    Performs calculations on a SINGLE queryset / dataset.

    Instantiate with a queryset or list of model instances,
    call whichever calculation methods you need, then read the results dict.

    Example usage in a view:
        records = SalesRecord.objects.using('external_db').filter(sale_date__year=2024)
        engine = CalculationEngine(records)
        results = engine.sales_summary()
    """

    def __init__(self, queryset_or_list):
        # Materialise once so we don't hit the DB multiple times
        self.data = list(queryset_or_list)
        self.params = ParameterStore  # access calculation params from admin

    # ------------------------------------------------------------------
    def sales_summary(self) -> dict:
        """Aggregate revenue, profit, margins across a sales queryset."""
        # if not self.data:
        #     return self._empty_sales_summary()

        total_BalanceEQ = sum(r.BalanceEQ for r in self.data)
        # total_revenue = sum(r.revenue for r in self.data)
        # total_cost = sum(r.quantity * r.cost_price for r in self.data)
        # total_profit = total_revenue - total_cost
        total_units = sum(r.quantity for r in self.data)

        # margin_target = self.params.get('profit_margin_target', 0.20)
        # vat_rate = self.params.get('vat_rate', 0.20)

        # margins = [r.margin_pct for r in self.data if r.unit_price > 0]
        # avg_margin = statistics.mean(margins) if margins else 0

        # Group revenue by category
        # by_category = {}
        # for r in self.data:
        #     by_category.setdefault(r.category, 0)
        #     by_category[r.category] += float(r.revenue)

        # Group revenue by region
        # by_region = {}
        # for r in self.data:
        #     by_region.setdefault(r.region, 0)
        #     by_region[r.region] += float(r.revenue)

        return {
            'total_BalanceEQ': round(float(total_BalanceEQ), 2),
            # 'total_cost': round(float(total_cost), 2),
            # 'total_profit': round(float(total_profit), 2),
            'total_units': round(float(total_units), 2),
            # 'avg_margin_pct': round(avg_margin, 2),
            # 'revenue_ex_vat': round(float(total_revenue) / (1 + vat_rate), 2),
            # 'vat_amount': round(float(total_revenue) - float(total_revenue) / (1 + vat_rate), 2),
            # 'margin_vs_target': round(avg_margin / 100 - margin_target, 4),
            # 'target_achieved': (avg_margin / 100) >= margin_target,
            # 'transaction_count': len(self.data),
            # 'by_category': dict(sorted(by_category.items(), key=lambda x: -x[1])),
            # 'by_region': dict(sorted(by_region.items(), key=lambda x: -x[1])),
            # 'top_products': self._top_products(n=10),
        }

    # def _top_products(self, n=10) -> list:
    #     by_product = {}
    #     for r in self.data:
    #         key = r.product_code
    #         if key not in by_product:
    #             by_product[key] = {'name': r.product_name, 'revenue': 0, 'units': 0}
    #         by_product[key]['revenue'] += float(r.revenue)
    #         by_product[key]['units'] += float(r.quantity)
    #     ranked = sorted(by_product.values(), key=lambda x: -x['revenue'])
    #     return ranked[:n]

    # def inventory_analysis(self) -> dict:
    #     """Analyse stock levels (pass InventoryItem queryset)."""
    #     if not self.data:
    #         return {}

    #     low_stock_threshold = self.params.get('low_stock_threshold', 50)
    #     total_value = sum(item.stock_value for item in self.data)
    #     low_stock_items = [i for i in self.data if float(i.current_stock) <= low_stock_threshold]
    #     out_of_stock = [i for i in self.data if float(i.current_stock) == 0]

    #     by_category = {}
    #     for item in self.data:
    #         by_category.setdefault(item.category, {'count': 0, 'value': 0})
    #         by_category[item.category]['count'] += 1
    #         by_category[item.category]['value'] += float(item.stock_value)

    #     return {
    #         'total_items': len(self.data),
    #         'total_stock_value': round(float(total_value), 2),
    #         'low_stock_count': len(low_stock_items),
    #         'out_of_stock_count': len(out_of_stock),
    #         'low_stock_items': low_stock_items[:20],
    #         'by_category': by_category,
    #         'avg_stock_value_per_item': round(float(total_value) / len(self.data), 2),
    #     }

    # @staticmethod
    # def _empty_sales_summary() -> dict:
    #     return {k: 0 for k in [
    #         'total_revenue', 'total_cost', 'total_profit', 'total_units',
    #         'avg_margin_pct', 'revenue_ex_vat', 'vat_amount', 'margin_vs_target',
    #         'transaction_count',
    #     ]} | {'target_achieved': False, 'by_category': {}, 'by_region': {}, 'top_products': []}


# class AggregateCalculator:
#     """
#     Multi-source calculations that JOIN or combine data from MULTIPLE
#     querysets / sources. No single DB row owns these results.

#     This class answers questions like:
#       - "Which products have high sales but low stock (risk of stockout)?"
#       - "What is our overall business health score?"
#       - "How does actual margin compare to configured targets across regions?"

#     Example usage in a view:
#         sales_qs = SalesRecord.objects.using('external_db').filter(sale_date__year=2024)
#         inv_qs   = InventoryItem.objects.using('external_db').all()
#         agg = AggregateCalculator(sales_qs, inv_qs)
#         dashboard = agg.dashboard_kpis()
#     """

#     def __init__(self, sales_queryset=None, inventory_queryset=None, extra_data: dict = None):
#         self.sales = list(sales_queryset) if sales_queryset is not None else []
#         self.inventory = list(inventory_queryset) if inventory_queryset is not None else []
#         self.extra = extra_data or {}
#         self.params = ParameterStore

#     # ------------------------------------------------------------------
#     def dashboard_kpis(self) -> dict:
#         """
#         Top-level KPIs that combine sales + inventory into a single dashboard dict.
#         This is a multi-source aggregate — no single table holds all this data.
#         """
#         sales_engine = CalculationEngine(self.sales)
#         sales_data = sales_engine.sales_summary()

#         inv_engine = CalculationEngine(self.inventory)
#         inv_data = inv_engine.inventory_analysis()

#         # Cross-source: products selling fast but running low on stock
#         stockout_risks = self._stockout_risk_products()

#         # Overall business health score (0–100) from multiple signals
#         health_score = self._health_score(sales_data, inv_data)

#         return {
#             'sales': sales_data,
#             'inventory': inv_data,
#             'stockout_risks': stockout_risks,
#             'health_score': health_score,
#             'health_label': self._health_label(health_score),
#             'generated_at': timezone.now().isoformat(),
#         }

#     def _stockout_risk_products(self) -> list:
#         """
#         Products with above-average sales velocity AND below reorder level.
#         Requires both sales and inventory data — cannot come from one table.
#         """
#         if not self.sales or not self.inventory:
#             return []

#         # Build sales velocity map: product_code → total units sold
#         velocity = {}
#         for r in self.sales:
#             velocity[r.product_code] = velocity.get(r.product_code, 0) + float(r.quantity)

#         avg_velocity = statistics.mean(velocity.values()) if velocity else 0

#         risks = []
#         for item in self.inventory:
#             v = velocity.get(item.product_code, 0)
#             if v > avg_velocity and float(item.current_stock) <= float(item.reorder_level):
#                 risks.append({
#                     'product_code': item.product_code,
#                     'product_name': item.product_name,
#                     'current_stock': float(item.current_stock),
#                     'reorder_level': float(item.reorder_level),
#                     'sales_velocity': round(v, 2),
#                     'risk_level': 'HIGH' if float(item.current_stock) == 0 else 'MEDIUM',
#                 })

#         return sorted(risks, key=lambda x: -x['sales_velocity'])

#     def _health_score(self, sales_data: dict, inv_data: dict) -> int:
#         """
#         Composite score 0–100 from four signals:
#           25 pts — margin target hit
#           25 pts — low stock % acceptable
#           25 pts — revenue is positive
#           25 pts — no out-of-stock items
#         """
#         score = 0
#         if sales_data.get('target_achieved'):
#             score += 25
#         if inv_data.get('total_items', 0) > 0:
#             low_pct = inv_data.get('low_stock_count', 0) / inv_data['total_items']
#             score += max(0, 25 - int(low_pct * 100))
#         if sales_data.get('total_revenue', 0) > 0:
#             score += 25
#         if inv_data.get('out_of_stock_count', 0) == 0:
#             score += 25
#         return score

#     @staticmethod
#     def _health_label(score: int) -> str:
#         if score >= 80:
#             return 'Excellent'
#         if score >= 60:
#             return 'Good'
#         if score >= 40:
#             return 'Fair'
#         return 'Needs Attention'

#     def trend_analysis(self, period: str = 'monthly') -> dict:
#         """
#         Group sales by time period and compute trend metrics.
#         Returns data ready to feed into a Chart.js line/bar chart.
#         """
#         if not self.sales:
#             return {'labels': [], 'revenue': [], 'profit': []}

#         groups: dict = {}
#         for r in self.sales:
#             if period == 'monthly':
#                 key = r.sale_date.strftime('%Y-%m')
#             elif period == 'weekly':
#                 key = f"{r.sale_date.isocalendar()[0]}-W{r.sale_date.isocalendar()[1]:02d}"
#             else:
#                 key = str(r.sale_date.year)

#             if key not in groups:
#                 groups[key] = {'revenue': 0, 'profit': 0, 'units': 0}
#             groups[key]['revenue'] += float(r.revenue)
#             groups[key]['profit'] += float(r.gross_profit)
#             groups[key]['units'] += float(r.quantity)

#         sorted_keys = sorted(groups.keys())
#         revenues = [groups[k]['revenue'] for k in sorted_keys]

#         # Simple linear trend: positive slope = growing
#         trend = 'stable'
#         if len(revenues) >= 2:
#             slope = revenues[-1] - revenues[0]
#             trend = 'growing' if slope > 0 else 'declining' if slope < 0 else 'stable'

#         return {
#             'labels': sorted_keys,
#             'revenue': [round(groups[k]['revenue'], 2) for k in sorted_keys],
#             'profit': [round(groups[k]['profit'], 2) for k in sorted_keys],
#             'units': [round(groups[k]['units'], 2) for k in sorted_keys],
#             'trend': trend,
#         }


class ReportBuilder:
    """
    Orchestrates the full pipeline for a named Report:
      1. Load report config from DB
      2. Pull data from external DB (using configured query or ORM)
      3. Run the appropriate calculator
      4. Return a context dict ready for the template
    """

    def build(self, report_slug: str, filters: dict = None) -> dict:
        try:
            report = Report.objects.get(slug=report_slug, is_active=True)
        except Report.DoesNotExist:
            return {'error': f"Report '{report_slug}' not found or inactive."}

        filters = filters or {}

        # Dispatch to the right calculation method
        dispatch = {
            'sales_summary': self._build_sales_summary,
            # 'inventory_analysis': self._build_inventory,
            # 'profit_margin': self._build_profit_margin,
            # 'trend_analysis': self._build_trend,
        }

        builder_fn = dispatch.get(report.calculation_type, self._build_custom)
        result = builder_fn(report, filters)
        result['report'] = report
        return result

    def _build_sales_summary(self, report, filters) -> dict:
        qs = SalesRecord.objects.using('external_db').all()
        if filters.get('year'):
            qs = qs.filter(sale_date__year=filters['year'])
        if filters.get('region'):
            qs = qs.filter(region=filters['region'])
        engine = CalculationEngine(qs)
        return {'data': engine.sales_summary()}

    # def _build_inventory(self, report, filters) -> dict:
    #     qs = InventoryItem.objects.using('external_db').all()
    #     engine = CalculationEngine(qs)
    #     return {'data': engine.inventory_analysis()}

    # def _build_profit_margin(self, report, filters) -> dict:
    #     sales_qs = SalesRecord.objects.using('external_db').all()
    #     inv_qs = InventoryItem.objects.using('external_db').all()
    #     agg = AggregateCalculator(sales_qs, inv_qs)
    #     return {'data': agg.dashboard_kpis()}

    # def _build_trend(self, report, filters) -> dict:
    #     sales_qs = SalesRecord.objects.using('external_db').all()
    #     agg = AggregateCalculator(sales_queryset=sales_qs)
    #     period = filters.get('period', 'monthly')
    #     return {'data': agg.trend_analysis(period=period)}

    def _build_custom(self, report, filters) -> dict:
        return {'data': {}, 'message': f"Custom report: {report.name}"}


