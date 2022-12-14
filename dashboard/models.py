from django.db import models
from application_masters.models import BaseContent

# Create your models here.


class ChartMeta(BaseContent):
    chart_type = models.IntegerField(choices=((1, 'Column Chart'), (2, 'Pie Chart'), (
        3, 'Table Chart'), (4, 'Bar Chart'), (5, 'Column Stack'), (6, 'Bar Stack')), blank=True, null=True, help_text="1=Column Chart, 2=Pie Chart, 3=Table Chart, 4=Bar Chart, 5=Column Stack, 6=Bar Stack")
    chart_slug = models.CharField(
        max_length=500, blank=True, null=True, unique=True)
    page_slug = models.CharField(max_length=500, blank=True, null=True)
    chart_title = models.CharField(max_length=500, blank=True, null=True)
    vertical_axis_title = models.CharField(
        max_length=200, blank=True, null=True)
    horizontal_axis_title = models.CharField(
        max_length=200, blank=True, null=True)
    chart_note = models.TextField(blank=True, null=True)
    chart_tooltip = models.TextField(blank=True, null=True)
    chart_height = models.TextField(
        blank=True, null=True, help_text="Chart height in pixel or %")
    click_handler = models.JSONField(
        blank=True, null=True, help_text="json text to set the handler options: {on_click_handler:function-name, url_template:url with placeholders for chart element(bar/column) key value")
    chart_options = models.JSONField(
        blank=True, null=True, help_text="json text to set the chart options")
    div_class = models.TextField(
        blank=True, null=True, help_text="div class name to be used for the chart container - ex:col-md-6, col-md-12 etc")
    chart_query = models.JSONField(
        blank=True, null=True, help_text="sql query and related filter details as json - with keys sqlquery, filters and etc")
    display_order = models.IntegerField(
        blank=True, null=True, help_text="order in which the charts have to be displayed")
    filter_info = models.JSONField(
        blank=True, null=True, help_text="report filters meta data in json format")

    class Meta:
        verbose_name_plural = "Chart Meta"

    def __str__(self):
        return self.chart_title


class DashboardWidgetSummaryLog(BaseContent):
    log_key = models.CharField(max_length=500, unique=True)
    last_successful_update = models.DateTimeField(blank=True, null=True)
    most_recent_update = models.DateTimeField(blank=True, null=True)
    most_recent_update_status = models.CharField(
        max_length=2500, blank=True, null=True)
    most_recent_update_time_taken_millis = models.IntegerField(default=0)

    def __str__(self):
        return self.log_key

