from __future__ import unicode_literals
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponseRedirect, HttpResponse
from django.conf import settings
import requests
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import ChartMeta, DashboardWidgetSummaryLog
from django.db.models import Subquery
from django.http import JsonResponse
from django.db import connection
from django.utils.encoding import smart_str
from datetime import datetime
import csv
from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
import traceback
import sys
import logging

logger = logging.getLogger(__name__)


# #****************************************************************************
# # update stackabar chart data to replace dummy data with actual values
# #****************************************************************************


def set_column_stack_chart_data(sql, headers):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        newdata = []
        newdata.append(headers)
        for row in rows:
            row_data = list(row)
            newdata.append(row_data)
            new_row_data = []
    finally:
        if cursor:
            cursor.close()
    return newdata


# #****************************************************************************
# # update column chart data  and labels to replace dummy data with actual values
# # labels only for dynamic bars - last 6 months kind of charts
# #****************************************************************************


def old_set_column_chart_data(sql, labels):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        descr = cursor.description
        counter = 0
        data = []

        data = [dict(zip([column for column in labels], row))for row in rows]

        # all queries always return one row - even when no data exists
        row = rows[0]
    finally:
        if cursor:
            cursor.close()
    return data[0].items()

def set_column_chart_data(sql, labels): #, bar_colors):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        counter = 0
        data = []
        header_row = labels
        #header_row.append({ 'role': 'annotation' })
        data.append(header_row)
        #all queries always return one row - even when no data exists
        for row in list(rows):
            row_data = []
            for item in row:
                row_data.append(item)
            #row_data.append(str(row_data[-1]))
            data.append(row_data)
    finally:
        if cursor:
            cursor.close()
    return data


def set_bar_chart_dynamic_lable(sql):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        descr = cursor.description
        data = []
        for i in rows:
            i = list(i)
            i[1] = int(i[1])
            data.append(i)
    finally:
        if cursor:
            cursor.close()
    return data

# #****************************************************************************
# # update table chart data to replace dummy data with actual values
# #****************************************************************************
def set_table_chart_data(sql, headers):
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    newdata = []
    newdata.append(headers)
    for row in rows:
        newdata.append(list(row))
    return newdata


# #****************************************************************************
# # Dashboard
# #****************************************************************************


@login_required(login_url='/login/')
def dashboard(request):
    heading = "Dashboard"
    district_id = request.session.get('user_district')
    block_id = request.session.get('user_block')

    try:
        slug = 'dashboard1'
        cht = ChartMeta.objects.filter(page_slug = slug,
            status=1).order_by('display_order')
        chart_list = []
        # states = filter_location_state(request)
        # selected_items = [request.POST.get('state', 0), request.POST.get(
        #     'district', 0), request.POST.get('shelter', 0)]
        # districts, shelterhome = None, None
        # if request.POST.get('state'):
        #     districts = filter_location_district(
        #         request, request.POST.get('state'))
        # elif states.count() == 1:
        #     districts = filter_location_district(
        #         request, states[0].id)
        # if request.POST.get('district'):
        #     shelterhome = filter_location_shelterhome(
        #         request, request.POST.get('district'),True)
        # elif districts and districts.count() == 1:
        #     shelterhome = filter_location_shelterhome(
        #         request, districts[0].id,True)
        # print(districts)
        mat_view_last_updated = '' #DashboardWidgetSummaryLog.objects.get(status=2, log_key='mat_child_dashboard_view').last_successful_update
        logger.error("cht-len:"+ str(len(cht)))
        table_chart_addln_headers = {}
        for i in cht:
            if i.chart_type == 1: #column Chart
                cht_info = {}
                filtered_query = apply_filter(request, i.chart_query.get('sql_query'),i.filter_info)
                labels = i.chart_query.get('labels')
                #update query here to replace the filter values
                chart_data = list(set_column_chart_data(filtered_query, labels))
                cht_info = {"chart_type": "COLUMNCHART"}
                cht_info["chart_title"] = i.chart_title
                cht_info["datas"] = chart_data
                cht_info["chart_slug"] = i.chart_slug
                cht_info.update({"options": i.chart_options})
                cht_info.update({"tooltip": i.chart_tooltip})
                cht_info.update({"chart_note": i.chart_note})
                cht_info.update({"chart_name": i.chart_slug})
                cht_info["chart_height"] = i.chart_height
                cht_info["addln_header"] = ""
                cht_info.update({"div": i.div_class})
                chart_list.append(cht_info)
            elif i.chart_type == 3: #Table Chart
                cht_info = {"chart_type": "TABLECHART"}
                headers = i.chart_query.get('col_headers')
                filtered_query = apply_filter(request, i.chart_query.get('sql_query'), i.filter_info)
                chart_data = set_table_chart_data(filtered_query, headers)
                cht_info["chart_slug"] = i.chart_slug
                cht_info["chart_title"] = i.chart_title
                cht_info["options"] = i.chart_options
                cht_info["datas"] = chart_data
                cht_info["tooltip"] = i.chart_tooltip
                cht_info["chart_height"] = i.chart_height
                cht_info["chart_name"] = i.chart_slug
                cht_info.update({"chart_note": i.chart_note})
                cht_info["div"] = i.div_class
                cht_info["addln_header"] = i.chart_query.get('addln_header','').strip()
                chart_list.append(cht_info)
            elif i.chart_type == 4 or i.chart_type == 6: # Bar chart
                cht_info = {}
                filtered_query = apply_filter(request, i.chart_query.get('sql_query'),i.filter_info)
                if i.chart_type == 4:
                    chart_data = list(set_column_chart_data(filtered_query, i.chart_query.get('labels')))
                else:
                    chart_data = list(set_bar_chart_dynamic_lable(filtered_query))
                cht_info = {"chart_type": "BARCHART"}
                cht_info["chart_slug"] = i.chart_slug
                cht_info["chart_title"] = i.chart_title
                chart_data.insert(0, ('', ''))
                cht_info["datas"] = chart_data
                cht_info.update({"tooltip": i.chart_tooltip})
                cht_info.update({"options": i.chart_options})
                cht_info.update({"chart_note": i.chart_note})
                cht_info.update({"chart_name": i.chart_slug})
                cht_info["chart_height"] = i.chart_height
                cht_info["addln_header"] = ''
                cht_info.update({"div": i.div_class})
                chart_list.append(cht_info)

            elif i.chart_type == 5:
                cht_info = {"chart_type": "COLUMNSTACK"}
                filtered_query = apply_filter(request, i.chart_query.get('sql_query'), i.filter_info)
                chart_data = set_column_stack_chart_data(filtered_query, i.chart_query.get('col_headers'))
                cht_info["chart_slug"] = i.chart_slug
                cht_info["chart_title"] = i.chart_title
                cht_info["datas"] = chart_data
                cht_info["options"] = i.chart_options
                # chart_type values: 1=Column Chart, 2=Pie Chart, 3=Table Chart , 4- Column Stack
                cht_info["chart_height"] = i.chart_height
                cht_info["addln_header"] = ''
                cht_info["chart_name"] = i.chart_slug
                cht_info["div"] = i.div_class
                cht_info.update({"tooltip": i.chart_tooltip})
                cht_info.update({"chart_note": i.chart_note})
                cht_info.update({"chart_name": i.chart_title})
                chart_list.append(cht_info)
            if i.chart_query.get('addln_header','').strip() != '':
                func_info = [i.chart_slug.replace('-','_'),i.chart_query.get('addln_header').strip()]
                table_chart_addln_headers.update({i.chart_slug:func_info})

        logger.error("chart_list-len:"+ str(len(chart_list)))
        data = {"chart": chart_list}

        context = {'data': json.dumps(data), 'data_html': data, 'district_id': district_id, 'block_id': block_id, 'heading': heading,
                'mat_view_last_updated': mat_view_last_updated, 'table_chart_addln_headers':table_chart_addln_headers}
        return render(request, 'dashboard/dashboard.html', context)
    except KeyError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(
        exc_type, exc_value, exc_traceback))
        logger.error(error_stack)
        return redirect('/login/')

def apply_filter(request, sql_query, filter_info):
    user_site = request.session['site_id'] if 'site_id' in request.session else None  
    logger.error("User Site not added in sesssion")
    filter_values = {"user_site":str(user_site)}
    filter_cond = filter_info['filter_cond']
    for key in filter_cond.keys():
        filter_value = filter_values.get(key)   
        updated_cond = filter_cond[key].replace('@@filter_value', filter_value)
        sql_query = sql_query.replace('@@'+key+'_filter', updated_cond)
    return sql_query

def get_block(request, district_id):
    if request.method == 'GET' and request.is_ajax():
        result_set = []
        blocks = Block.objects.filter(status=1, district__id=district_id)
        for block in blocks:
            result_set.append(
                {'id': block.id, 'name': block.name,})
        return HttpResponse(json.dumps(result_set))