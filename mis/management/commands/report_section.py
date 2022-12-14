import datetime
from datetime import date
import sys
import traceback
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from django.utils import timezone
from mis.models import *
from django.db.models import Q

def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - datetime.timedelta(days=next_month.day)

# def last_day_of_month(date):
#     return date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)

# Report Section 1 Done
def get_report_section1(sd, ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj  in  Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)
                
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                session_objs = FossilAHSession.objects.filter(status=1)
                for task in task_obj_list:
                    awc_list = []
                    for i in task_obj_list:
                        awc_list.append(i.awc)
                    awc_lists = []
                    for item in awc_list:
                            awc_lists.extend(item)

                    for awc in AWC.objects.filter(id__in = awc_lists):
                        for session_obj in session_objs:
                            ahsession_objs = AHSession.objects.filter(status=1, fossil_ah_session = session_obj, adolescent_name__awc = awc, task__id__in = task_ids)
                            adolescent_ids = ahsession_objs.values_list('adolescent_name__id', flat=True)
                            adolescent_obj = Adolescent.objects.filter(id__in = adolescent_ids)
                                
                            for ahsession_obj in ahsession_objs: 
                                # for i in task_obj_list:
                                obj, created = ReportSection1.objects.get_or_create(task = ahsession_obj.task, site = site_obj.site, name_of_awc_code = awc.name, unique_id = ahsession_obj.id)
                                obj.name_of_cc = ahsession_obj.task.user.groups.all()[0].name
                                obj.name_of_block = awc.village.grama_panchayat.block.name
                                obj.name_of_panchayat = awc.village.grama_panchayat.name
                                obj.name_of_village = awc.village.name
                                obj.session_name = ahsession_obj.fossil_ah_session.session_name
                                obj.girls_10_14_year = adolescent_obj.filter(gender = 2, age_in_completed_years__range=[10, 14]).count()
                                obj.girls_15_19_year = adolescent_obj.filter(gender = 2, age_in_completed_years__range=[15, 19]).count()
                                obj.boys_10_14_year = adolescent_obj.filter(gender = 1, age_in_completed_years__range=[10, 14], ).count()
                                obj.boys_15_19_year = adolescent_obj.filter(gender = 1, age_in_completed_years__range=[15, 19]).count()
                                obj.save()

    print('report_section 1')
    return "Report Section 1"

# Report Section 2 Done
def get_report_section2(sd, ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)         
                            
                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                session_objs = FossilDLSessionConfig.objects.filter(status=1)
                
                for task in task_obj_list:
                    awc_list = []
                    for i in task_obj_list:
                        awc_list.append(i.awc)
                    awc_lists = []
                    for item in awc_list:
                            awc_lists.extend(item)

                    for awc in AWC.objects.filter(id__in = awc_lists):
                        for session_obj in session_objs:
                            dlsession_objs = DLSession.objects.filter(status=1, fossil_dl_session_config = session_obj, adolescent_name__awc = awc, task__id__in = task_ids)
                            adolescent_ids = dlsession_objs.values_list('adolescent_name__id', flat=True)
                            adolescent_obj = Adolescent.objects.filter(id__in = adolescent_ids)
                                
                            for dlsession_obj in dlsession_objs: 
                                # for i in task_obj_list:
                                obj, created = ReportSection2.objects.get_or_create(task = dlsession_obj.task, site = site_obj.site, name_of_awc_code = awc.name, unique_id = dlsession_obj.id)
                                obj.name_of_cc = task.user.groups.all()[0].name
                                obj.name_of_block = awc.village.grama_panchayat.block.name
                                obj.name_of_panchayat = awc.village.grama_panchayat.name
                                obj.name_of_village = awc.village.name
                                obj.session_name = dlsession_obj.fossil_dl_session_config.session_category.session_category
                                obj.girls_10_14_year = adolescent_obj.filter(gender = 2, age_in_completed_years__range=[10, 14]).count()
                                obj.girls_15_19_year = adolescent_obj.filter(gender = 2, age_in_completed_years__range=[15, 19]).count()
                                obj.save()

    print('report_section 2')
    return "Report Section 2"


def get_report_section3(sd, ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(status=1, user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                
                task_ids = task_obj_list.values_list('id', flat=True)

                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)
                for awc_obj in AWC.objects.filter(id__in = awc_lists): 
                    avtraining_obj = AdolescentVocationalTraining.objects.filter(status=1, task__id__in = task_ids, adolescent_name__awc = awc_obj)
                    adolescent_ids = avtraining_obj.values_list('adolescent_name__id', flat=True)
                    adolescent_obj = Adolescent.objects.filter(id__in = adolescent_ids)
                    if avtraining_obj:
                        for vocational in avtraining_obj:
                            obj, created = ReportSection3.objects.get_or_create(task = vocational.task, site = site_obj.site, unique_id = awc_obj.id)
                            obj.name_of_block = awc_obj.village.grama_panchayat.block.name
                            obj.name_of_panchayat = awc_obj.village.grama_panchayat.name
                            obj.name_of_village = awc_obj.village.name
                            obj.name_of_awc_code = awc_obj.name
                            obj.number_adolescent_girls_linked = adolescent_obj.filter(gender = 2).count()
                            obj.number_girls_completed_training = avtraining_obj.filter(training_complated = 1).count()
                            obj.number_girls_accepted_placement = avtraining_obj.filter(placement_accepted = 2).count()
                            obj.number_of_girls_offered_placement = avtraining_obj.filter(placement_offered = 1).count()
                            obj.save()

    print('Report Section 3')
    return 'Report Section3'

# Report Section 4a
def get_report_section4a(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                
                task_ids = task_obj_list.values_list('id', flat=True)
                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)

                for school in School.objects.filter(status=1):
                    for awc in AWC.objects.filter(id__in = awc_lists):
                        girlsahwd_objs = GirlsAHWD.objects.filter(Q(place_of_ahwd=1, object_id = awc.id) | Q(place_of_ahwd=2, object_id = school.id) | Q(place_of_ahwd=3), status=1, task__id__in = task_ids, )
                    
                        for girlsahwd_obj in girlsahwd_objs:
                            # for i in task_obj_list:
                            obj, created = ReportSection4a.objects.get_or_create(task = girlsahwd_obj.task, site = site_obj.site, unique_id = girlsahwd_obj.id)
                            if girlsahwd_obj.place_of_ahwd == 2:
                                obj.name_of_awc_code = school.name
                                obj.name_of_block = school.village.grama_panchayat.block.name
                                obj.name_of_panchayat = school.village.grama_panchayat.name
                                obj.name_of_village = school.village.name
                            elif girlsahwd_obj.place_of_ahwd == 1:
                                obj.name_of_awc_code = awc.name
                                obj.name_of_block = awc.village.grama_panchayat.block.name
                                obj.name_of_panchayat = awc.village.grama_panchayat.name
                                obj.name_of_village = awc.village.name
                            else:
                                obj.name_of_awc_code = girlsahwd_obj.hwc_name
                            obj.participated_10_14_years = girlsahwd_obj.participated_10_14_years
                            obj.participated_15_19_years = girlsahwd_obj.participated_15_19_years
                            obj.bmi_10_14_year = girlsahwd_obj.bmi_10_14_years
                            obj.bmi_15_19_year = girlsahwd_obj.bmi_15_19_years
                            obj.hb_test_10_14_year = girlsahwd_obj.hb_10_14_years
                            obj.hb_test_15_19_year = girlsahwd_obj.hb_15_19_years
                            obj.tt_shot_10_14_year = girlsahwd_obj.tt_10_14_years
                            obj.tt_shot_15_19_year = girlsahwd_obj.tt_15_19_years
                            obj.counselling_10_14_year = girlsahwd_obj.counselling_10_14_years
                            obj.counselling_15_19_year = girlsahwd_obj.counselling_15_19_years
                            obj.referral_10_14_year = girlsahwd_obj.referral_10_14_years
                            obj.referral_15_19_year = girlsahwd_obj.referral_15_19_years
                            obj.save() 

    print('report_section 4a')                               
    return 'Report Section4a'

# Report Section 4b
def get_report_section4b(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)
                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)
                for school in School.objects.filter(status=1):     
                    for awc in AWC.objects.filter(id__in = awc_lists):
                        boysahwd_objs = BoysAHWD.objects.filter(Q(place_of_ahwd=1, object_id = awc.id) | Q(place_of_ahwd=2, object_id = school.id) | Q(place_of_ahwd=3), status=1, task__id__in = task_ids)
                        for boysahwd_obj in boysahwd_objs:
                            obj, created = ReportSection4b.objects.get_or_create(task = boysahwd_obj.task, site = site_obj.site, unique_id = boysahwd_obj.id)
                            if boysahwd_obj.place_of_ahwd == 2:
                                obj.name_of_awc_code = school.name
                                obj.name_of_block = school.village.grama_panchayat.block.name
                                obj.name_of_panchayat = school.village.grama_panchayat.name
                                obj.name_of_village = school.village.name
                            elif boysahwd_obj.place_of_ahwd == 1:
                                obj.name_of_awc_code = awc.name
                                obj.name_of_block = awc.village.grama_panchayat.block.name
                                obj.name_of_panchayat = awc.village.grama_panchayat.name
                                obj.name_of_village = awc.village.name
                            else:
                                obj.name_of_awc_code = boysahwd_obj.hwc_name
                            obj.participated_10_14_years = boysahwd_obj.participated_10_14_years
                            obj.participated_15_19_years = boysahwd_obj.participated_15_19_years
                            obj.bmi_10_14_year = boysahwd_obj.bmi_10_14_years
                            obj.bmi_15_19_year = boysahwd_obj.bmi_15_19_years
                            obj.hb_test_10_14_year = boysahwd_obj.hb_10_14_years
                            obj.hb_test_15_19_year = boysahwd_obj.hb_15_19_years
                            obj.counselling_10_14_year =  boysahwd_obj.counselling_10_14_years
                            obj.counselling_15_19_year = boysahwd_obj.counselling_15_19_years
                            obj.referral_10_14_year = boysahwd_obj.referral_10_14_years
                            obj.referral_15_19_year = boysahwd_obj.referral_15_19_years
                            obj.save()

    print('report_section 4b')
    return 'report_section 4b'

# Report Section 5 Done
def get_report_section5(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)
                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)
                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)
                
                for awc in AWC.objects.filter(id__in = awc_lists):
                    for boysahwd_obj in AdolescentsReferred.objects.filter(status=1, task__id__in = task_ids, awc_name = awc):
                        # for i in task_obj_list:
                        obj, created = ReportSection5.objects.get_or_create(task = boysahwd_obj.task, site = site_obj.site, unique_id = boysahwd_obj.id)
                        obj.name_of_block = awc.village.grama_panchayat.block.name
                        obj.name_of_panchayat = awc.village.grama_panchayat.name
                        obj.name_of_village = awc.village.name
                        obj.name_of_awc_code = awc.name

                        obj.girls_referred_10_14_year = boysahwd_obj.girls_referred_10_14_year
                        obj.girls_referred_15_19_year = boysahwd_obj.girls_referred_15_19_year
                        
                        obj.boys_referred_10_14_year = boysahwd_obj.boys_referred_10_14_year
                        obj.boys_referred_15_19_year = boysahwd_obj.boys_referred_15_19_year

                        obj.girls_hwc_referred = boysahwd_obj.girls_hwc_referred
                        obj.girls_hwc_visited = boysahwd_obj.girls_hwc_visited
                        
                        obj.girls_afhc_referred = boysahwd_obj.girls_afhc_referred
                        obj.girls_afhc_visited = boysahwd_obj.girls_afhc_visited

                        obj.girls_dh_referred = boysahwd_obj.girls_dh_referred
                        obj.girls_dh_visited = boysahwd_obj.girls_dh_visited

                        obj.boys_hwc_referred =  boysahwd_obj.boys_hwc_referred
                        obj.boys_hwc_visited =  boysahwd_obj.boys_hwc_visited

                        obj.boys_afhc_referred = boysahwd_obj.boys_afhc_referred
                        obj.boys_afhc_visited = boysahwd_obj.boys_afhc_visited

                        obj.boys_dh_referred = boysahwd_obj.boys_dh_referred
                        obj.boys_dh_visited = boysahwd_obj.boys_dh_visited
                        obj.save()

    print('Report Section 5')
    return 'report_section5'

# Report Section 6 Done
def get_report_section6(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1)) 
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)
                
                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                for gramapanchayat_obj in GramaPanchayat.objects.filter(status=1):
                    
                    for afc_obj in AdolescentFriendlyClub.objects.filter(status=1, task__id__in = task_ids, panchayat_name = gramapanchayat_obj):              
                        # for i in task_obj_list:
                        obj, created = ReportSection6.objects.get_or_create(task = afc_obj.task, site = site_obj.site, unique_id = afc_obj.id)
                        obj.name_of_panchayat = gramapanchayat_obj.name
                        obj.name_of_block = gramapanchayat_obj.block.name
                        obj.name_of_hsc = afc_obj.hsc_name
                        obj.name_of_sahiya_participated = afc_obj.no_of_sahiya
                        obj.no_of_aww =  afc_obj.no_of_aww
                        obj.girls_10_14_year = afc_obj.pe_girls_10_14_year
                        obj.girls_15_19_year = afc_obj.pe_girls_15_19_year
                        obj.boys_10_14_year = afc_obj.pe_boys_10_14_year
                        obj.boys_15_19_year = afc_obj.pe_boys_15_19_year
                        obj.save()   

    print('Report Section 6')
    return 'report_section6'

# Report Section 7 Done
def get_report_section7(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)
                
                # for report_person in report_person_cc:
                task_obj_list =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                for school_obj in School.objects.filter(status=1):
                    for balsansadmeeting_obj in BalSansadMeeting.objects.filter(status=1, task__id__in = task_ids, school_name = school_obj):
                        # for i in task_obj_list:
                        obj, created = ReportSection7.objects.get_or_create(task = balsansadmeeting_obj.task, site = site_obj.site, school_id = balsansadmeeting_obj.id)
                        obj.school_name = school_obj.name
                        obj.name_of_block = school_obj.village.grama_panchayat.block.name
                        obj.name_of_panchayat = school_obj.village.grama_panchayat.name
                        obj.no_of_participants = balsansadmeeting_obj.no_of_participants
                        obj.number_issues_discussed = balsansadmeeting_obj.issues_discussion.name if balsansadmeeting_obj.issues_discussion else ''
                        obj.number_decision_taken = balsansadmeeting_obj.decision_taken
                        obj.save()

    print('Report Section 7')                    
    return 'report_section7'

# Report Section 8 Done
def get_report_section8(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))  
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator', 'Senior Program Officer']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)
                
                for village_obj in Village.objects.filter(status=1):

                    for cea_obj in CommunityEngagementActivities.objects.filter(status=1, task__id__in = task_ids, village_name = village_obj):
                        # for i in task_obj_list:
                        obj, created = ReportSection8.objects.get_or_create(task = cea_obj.task, site = site_obj.site, village_id = cea_obj.id)
                        obj.name_of_block = village_obj.grama_panchayat.block.name
                        obj.name_of_panchayat = village_obj.grama_panchayat.name
                        obj.name_of_village = village_obj.name 
                        obj.event_name = cea_obj.event_name.name if cea_obj.event_name else ''
                        obj.activity_name = cea_obj.activity_name.name if cea_obj.activity_name else ''
                        obj.organized_by = cea_obj.get_organized_by_display()
                        obj.girls_10_14_year = cea_obj.girls_10_14_year
                        obj.girls_15_19_year = cea_obj.girls_15_19_year
                        obj.boys_10_14_year = cea_obj.boys_10_14_year
                        obj.boys_15_19_year = cea_obj.boys_15_19_year
                        obj.champions_15_19_year = cea_obj.champions_15_19_year
                        obj.adult_male = cea_obj.adult_male
                        obj.adult_female = cea_obj.adult_female
                        obj.teachers = cea_obj.teachers
                        obj.pri_members = cea_obj.pri_members
                        obj.services_providers = cea_obj.services_providers
                        obj.sms_members = cea_obj.sms_members
                        obj.other = cea_obj.other
                        obj.save()

    print('Report Section 8')
    return 'Report Section 8'

# Report Section 9 Done
def get_report_section9(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj in Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                # for report_person in report_person_cc:
                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)
                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)
                        
                for awc_obj in AWC.objects.filter(status=1, id__in = awc_lists):
                    champion_objs = Champions.objects.filter(status=1, task__id__in = task_ids, awc_name = awc_obj)

                    for champion_obj in champion_objs:
                        # for i in task_obj_list:
                        obj, created = ReportSection9.objects.get_or_create(task = champion_obj.task, site = site_obj.site, unique_id = champion_obj.id )
                        obj.name_of_block = awc_obj.village.grama_panchayat.block.name
                        obj.name_of_panchayat = awc_obj.village.grama_panchayat.name
                        obj.name_of_village = awc_obj.village.name
                        obj.name_of_awc_code = awc_obj.name
                        obj.girls_10_14_year = champion_obj.girls_10_14_year
                        obj.girls_15_19_year = champion_obj.girls_15_19_year
                        obj.boys_10_14_year = champion_obj.boys_10_14_year
                        obj.boys_15_19_year = champion_obj.boys_15_19_year
                        obj.first_inst_visited = champion_obj.get_first_inst_visited_display()
                        obj.second_inst_visited = champion_obj.get_second_inst_visited_display()
                        obj.third_inst_visited = champion_obj.get_third_inst_visited_display()
                        obj.fourth_inst_visited = champion_obj.get_fourth_inst_visited_display()
                        obj.save()
   
    print('Report Section 9')
    return 'Report Section 9'

# Report Section 10 Done
def get_report_section10(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj  in  Task.objects.filter(start_date = sd, user__groups__name__in = ['Program Officer', 'Trainging Coordinator']):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)

                for adolescent_obj in Adolescent.objects.filter(awc__id__in = awc_lists):
                    adolre_objs = AdolescentRe_enrolled.objects.filter(status=1, task__id__in = task_ids, adolescent_name = adolescent_obj)

                    for adolre_obj in adolre_objs:
                        obj, created = ReportSection10.objects.get_or_create(task = adolre_obj.task, site = site_obj.site, unique_id = adolre_obj.id)
                        obj.name_of_block = adolescent_obj.awc.village.grama_panchayat.block.name
                        obj.name_of_panchayat = adolescent_obj.awc.village.grama_panchayat.name
                        obj.name_of_village = adolescent_obj.awc.village.name
                        obj.name_of_awc_code = adolescent_obj.awc.name
                        obj.name_of_adolescent = adolre_obj.adolescent_name.name
                        obj.gender = adolre_obj.get_gender_display()
                        obj.age = adolre_obj.age
                        obj.parent_guardian_name = adolre_obj.parent_guardian_name
                        obj.name_of_school = adolre_obj.school_name
                        obj.class_enrolled = adolre_obj.get_which_class_enrolled_display()
                        obj.save()
    
    print('Report Section 10')
    return 'Report Section 10'

# Untrust VLCPCMetting
def get_report_untrust_vlcpcmetting(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj  in  Task.objects.filter(start_date = sd, user__groups__name = 'Program Officer'):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)

                for awc_obj in AWC.objects.filter(status=1, id__in = awc_lists):
                    vlcp_metting_objs = VLCPCMetting.objects.filter(status=1, task__id__in = task_ids, awc_name = awc_obj)
                    for vlcp_metting_obj in vlcp_metting_objs:
                        obj, created = UntrustVLCPCMetting.objects.get_or_create(task = vlcp_metting_obj.task, site = site_obj.site, unique_id = vlcp_metting_obj.id)
                        obj.name_of_block = awc_obj.village.grama_panchayat.block.name
                        obj.name_of_panchayat = awc_obj.village.grama_panchayat.name
                        obj.name_of_village = awc_obj.village.name
                        obj.name_of_awc_code = awc_obj.name
                        obj.date_of_meeting = vlcp_metting_obj.date_of_meeting
                        obj.no_of_participants_planned = vlcp_metting_obj.no_of_participants_planned
                        obj.no_of_participants_attended = vlcp_metting_obj.no_of_participants_attended
                        obj.save()
                
    print('Untrust VLCPCMetting')
    return 'Untrust VLCPCMetting'

# Untrust DCPU_BCPU
def get_report_untrust_dcpu_bcpu(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj  in  Task.objects.filter(start_date = sd, user__groups__name = 'Program Officer'):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                for block_obj in Block.objects.filter(status=1):
                    dcpu_objs = DCPU_BCPU.objects.filter(status=1, task__id__in = task_ids, block_name = block_obj)

                    for dcpu_obj in dcpu_objs:
                        obj, created = UntrustDCPU_BCPU.objects.get_or_create(task = dcpu_obj.task, site = site_obj.site, unique_id = dcpu_obj.id)
                        obj.name_of_block = block_obj.name
                        obj.name_of_institution = dcpu_obj.name_of_institution
                        obj.date_of_visit1 = dcpu_obj.date_of_visit
                        obj.name_of_lead = dcpu_obj.name_of_lead
                        obj.designation = dcpu_obj.designation
                        obj.issues_discussed = dcpu_obj.issues_discussed
                        obj.girls_10_14_year = dcpu_obj.girls_10_14_year
                        obj.girls_15_19_year = dcpu_obj.girls_15_19_year
                        obj.boys_10_14_year = dcpu_obj.boys_10_14_year
                        obj.boys_15_19_year = dcpu_obj.boys_15_19_year
                        obj.champions_15_19_year = dcpu_obj.champions_15_19_year
                        obj.adult_male = dcpu_obj.adult_male
                        obj.adult_female = dcpu_obj.adult_female
                        obj.teachers = dcpu_obj.teachers
                        obj.pri_members = dcpu_obj.pri_members
                        obj.services_providers = dcpu_obj.services_providers
                        obj.sms_members = dcpu_obj.sms_members
                        obj.other = dcpu_obj.other
                        obj.save()
    
    print('Untrust DCPU_BCPU')
    return 'Untrust DCPU_BCPU'

# Untrust EducatinalEnrichmentSupportProvided
def get_report_untrust_education_enrichment(sd,ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj  in  Task.objects.filter(start_date = sd, user__groups__name = 'Program Officer'):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                task_ids = task_obj_list.values_list('id', flat=True)

                awc_list = []
                for i in task_obj_list:
                    awc_list.append(i.awc)
                awc_lists = []
                for item in awc_list:
                        awc_lists.extend(item)

                for adolescent_obj in Adolescent.objects.filter(awc__id__in = awc_lists):
                    edu_objs = EducatinalEnrichmentSupportProvided.objects.filter(status=1, task__id__in = task_ids, adolescent_name = adolescent_obj)

                    for edu_obj in edu_objs:
                        obj, created = UntrustEducatinalEnrichmentSupportProvided.objects.get_or_create(task = edu_obj.task, site = site_obj.site, unique_id = edu_obj.id)
                        obj.name_of_block = adolescent_obj.awc.village.grama_panchayat.block.name
                        obj.name_of_panchayat = adolescent_obj.awc.village.grama_panchayat.name
                        obj.name_of_village = adolescent_obj.awc.village.name
                        obj.name_of_awc_code = adolescent_obj.awc.name
                        obj.name_of_adolescent = adolescent_obj.name
                        obj.parent_guardian_name = edu_obj.parent_guardian_name
                        obj.enrolment_date = edu_obj.enrolment_date
                        obj.standard = edu_obj.get_standard_display()
                        obj.duration_of_coaching_support = edu_obj.duration_of_coaching_support
                        obj.save()

    print('Untrust EducatinalEnrichmentSupportProvided')
    return 'Untrust EducatinalEnrichmentSupportProvided'


# Untrust Parent Vocational Training
def get_untrust_parent_vocational_training(sd, ed):
    if (sd == None and ed == None):
        start_date = datetime.date.today().replace(day=1)
        current_year = start_date.year
        less_than_one_year = current_year - 1
        years={current_year: 1, less_than_one_year: 2}
    for year in years:
        for months in range(1, 13):
            sd = datetime.date(year, months, (start_date.day))
            month = sd.strftime("%B")            
            ed = last_day_of_month(datetime.date(year, months, 1))
            for task_obj  in  Task.objects.filter(start_date = sd, user__groups__name = 'Program Officer'):
                try:
                    site_obj = UserSiteMapping.objects.get(user=task_obj.user)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=e)
                report_person_cc = MisReport.objects.filter(status=1, report_to = task_obj.user)
                if report_person_cc:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                else:
                    report_person_cc_list = report_person_cc.values_list('report_person__id', flat=True)
                    error_message = 'Mis reports matching query does not exist.'
                    obj, created = Logged.objects.get_or_create(user=task_obj.user, month=month, error_message=error_message)

                for report_person in report_person_cc:
                    task_obj_list  =  Task.objects.filter(user__id__in = report_person_cc_list, start_date = sd, end_date = ed)
                    task_ids = task_obj_list.values_list('id', flat=True)
                    awc_list = []
                    for i in task_obj_list:
                        awc_list.append(i.awc)
                    awc_lists = []
                    for item in awc_list:
                            awc_lists.extend(item)
                    for awc_obj in AWC.objects.filter(id__in = awc_lists): 
                        avtraining_obj = ParentVocationalTraining.objects.filter(status=1, task__id__in = task_ids, adolescent_name__awc = awc_obj)
                        adolescent_ids = avtraining_obj.values_list('adolescent_name__id', flat=True)
                        adolescent_obj = Adolescent.objects.filter(id__in = adolescent_ids)
                        if avtraining_obj:
                            for vocational in avtraining_obj:
                                obj, created = UntrustParentVocationalTraining.objects.get_or_create(task = vocational.task, site = site_obj.site, unique_id = awc_obj.id)
                                obj.name_of_block = awc_obj.village.grama_panchayat.block.name
                                obj.name_of_panchayat = awc_obj.village.grama_panchayat.name
                                obj.name_of_village = awc_obj.village.name
                                obj.name_of_awc_code = awc_obj.name
                                obj.parent_name = avtraining_obj.filter(parent_name__isnull = False).count()
                                obj.training_complated = avtraining_obj.filter(training_complated = 1).count()
                                obj.placement_offered = avtraining_obj.filter(placement_offered = 2).count()
                                obj.placement_accepted =  avtraining_obj.filter(placement_accepted = 1).count()
                                obj.save()

    print('Untrust Parent Vocational Training')
    return 'Untrust Parent Vocational Training'


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        history_record = HistoryRecord()
        first_time = timezone.now()
        history_record.start_date_time = first_time  
        sd = None
        ed = None   
        get_report_section1(sd, ed)
        get_report_section2(sd, ed)
        get_report_section3(sd, ed) 
        get_report_section4a(sd, ed)
        get_report_section4b(sd, ed)
        get_report_section5(sd, ed)
        get_report_section6(sd, ed)
        get_report_section7(sd, ed)
        get_report_section8(sd, ed)
        get_report_section9(sd, ed)
        get_report_section10(sd, ed)
        get_report_untrust_vlcpcmetting(sd, ed)
        get_report_untrust_dcpu_bcpu(sd, ed)
        get_untrust_parent_vocational_training(sd, ed)
        get_report_untrust_education_enrichment(sd, ed)
        second_time = timezone.now()
        history_record.end_date_time = second_time
        history_record.execution_time = str(second_time - first_time)
        history_record.save()
