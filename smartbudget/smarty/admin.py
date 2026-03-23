from django.contrib import admin

from .model import DailyTransactionSummary, Raw_Transaction, UPI_Category_Mapping

admin.site.register(Raw_Transaction)
admin.site.register(DailyTransactionSummary)
admin.site.register(UPI_Category_Mapping)
