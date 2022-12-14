from django.core.management.base import BaseCommand
from dateutil.relativedelta import relativedelta
from application_masters.models import *
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from mis.models import *
import datetime 

def end_date_of_a_month(date):
    start_date_of_this_month = date.replace(day=1)

    month = start_date_of_this_month.month
    year = start_date_of_this_month.year
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    next_month_start_date = start_date_of_this_month.replace(month=month, year=year)

    this_month_end_date = next_month_start_date - datetime.timedelta(days=1)
    return this_month_end_date

def get_create_task():
    first_day_of_the_month = datetime.date.today().replace(day=1)
    # first_day_of_the_month = '2022-09-01'
    last_day_of_the_month = end_date_of_a_month(datetime.datetime.now().date())
    # last_day_of_the_month = '2022-09-30'
    month = first_day_of_the_month.strftime('%B')
    # month = 'september'
    year = str(first_day_of_the_month.year)
    # year = '2022'
    for user_obj in User.objects.filter():
        user_name=user_obj.groups.all()
        if user_name:
            task_name = f'{user_obj.username} {month} {year}' 
            awc_ah_id = CC_AWC_AH.objects.filter(status=1, user=user_obj).values_list('awc__id', flat=True)
            awc_dl_id = CC_AWC_DL.objects.filter(status=1, user=user_obj).values_list('awc__id', flat=True)
            awc_id = list(awc_ah_id) + list(awc_dl_id)
            if awc_id:
                awc_ids = list(awc_id)
            else:
                awc_ids = list(awc_id)
                if user_name.filter(name='Cluster Coordinator'):
                    if user_obj.username == 'admin':
                        it_not_neccessary = 'It is okay'
                    else:
                        error_message = "AWC IDs at CC AWC AH and CC AWC DL matching query does not exist."
                        obj, created = Logged.objects.get_or_create(user=user_obj, month=month, error_message=error_message)
            obj, created = Task.objects.get_or_create(name=task_name, user=user_obj, start_date=first_day_of_the_month, end_date=last_day_of_the_month, 
            task_status=1, awc=awc_ids, extension_date=last_day_of_the_month)
            obj.name = task_name
            obj.user = user_obj
            obj.start_date = first_day_of_the_month
            obj.end_date = last_day_of_the_month
            obj.task_status = 1
            obj.awc = awc_ids
            obj.extension_date = last_day_of_the_month
            obj.save()
        else:
            if user_obj.username == 'admin':
                it_not_neccessary = 'It is okay'
            else:
                error = "User group matching query does not exist."  
                obj, created = Logged.objects.get_or_create(user=user_obj, month=month, error_message=error)
    print('Task')
    return 'Task'

    
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        get_create_task()