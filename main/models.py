from django.db import models
from django.core.cache import cache
from django.utils import timezone
import statistics
import pandas as pd
import math
from django.db import connections



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



class DataToPandasDataset:

    def __init__(self, table: str = "PastDueLoanRazm", query: str | None = None, params: list | None = None):
        self.table = table
        self.query = query or f"SELECT * FROM {self.table}"
        self.params = params or []

    # Fetches data from external database and stores to pandas dataframe
    def load_loans_dataframe(self) -> pd.DataFrame:
        with connections['external_db'].cursor() as cursor:
            # cursor.execute("SELECT * FROM PastDueLoanRazm", self.params or [])
            cursor.execute(self.query, self.params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            # rows = cursor.fetchmany(1000)


        return pd.DataFrame.from_records(rows, columns=columns)

    
class Calculation:
    def __init__(self, table: str = "PastDueLoanRazm"):
        self.table = table


    def WeightedAverageRate(self):
        ds = DataToPandasDataset(table="PastDueLoanRazm")
        df = ds.load_loans_dataframe()

        df['Balance'] = df['Balance'].replace('NULL', 0.1)
        df['AgreementPercent'] = df['AgreementPercent'].replace('Null',0.1)

        result = math.sumprod(df['AgreementPercent'],df['Balance'])/sum(df['Balance'])
        return result
        


