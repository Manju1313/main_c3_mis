import json
from datetime import date
from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, get_user, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.defaultfilters import slugify

from mis.models import *

# content_type__model=("awc", "school"), object_id=request.user.id
# Create your views here.

def getData(request):
    """ Get Data of subdomain """
    subDomain = request.META['HTTP_HOST'].lower().split('.')
    i = 0
    if subDomain[0] == 'www':
        i = (i + 1)
    codeobj = slugify(subDomain[i])

    try:
        site_obj = Site.objects.get(name = codeobj).domain
    except:
        site_obj = None

    return site_obj

def pagination_function(request, data):
    records_per_page = 10
    paginator = Paginator(data, records_per_page)
    page = request.GET.get('page', 1)
    try:
        pagination = paginator.page(page)
    except PageNotAnInteger:
        pagination = paginator.page(1)
    except EmptyPage:
        pagination = paginator.page(paginator.num_pages)
    return pagination

def login_view(request):
    heading = "Login"
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        data = getData(request)
        if UserSiteMapping.objects.filter(user__username = username, site__domain = data).exists():

            try:
                findUser = User._default_manager.get(username__iexact=username)
            except User.DoesNotExist:
                findUser = None
            if findUser is not None:
                username = findUser.get_username()
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['site_id'] = Site.objects.get(domain=request.META['HTTP_HOST']).id
                user_role = str(get_user(request).groups.last())
                if (user_role == 'Senior Lead'):
                    user_report_spo_to_sl = MisReport.objects.filter(report_to = user).values_list('report_person__id', flat=True)
                    user_report_po_to_spo = MisReport.objects.filter(report_to__id__in = user_report_spo_to_sl).values_list('report_person__id', flat=True)
                    user_report_cc_to_po = MisReport.objects.filter(report_to__id__in = user_report_po_to_spo).values_list('report_person__id', flat=True)
                    awc_id = CC_AWC_AH.objects.filter(user__id__in=user_report_cc_to_po).values_list('awc_id', flat=True)
                elif (user_role == 'Senior Program Officer'):
                    user_report_po_to_spo = MisReport.objects.filter(report_to = user).values_list('report_person__id', flat=True)
                    user_report_cc_to_po = MisReport.objects.filter(report_to__id__in = user_report_po_to_spo).values_list('report_person__id', flat=True)
                    awc_id = CC_AWC_AH.objects.filter(user__id__in=user_report_cc_to_po).values_list('awc_id', flat=True)
                elif (user_role == 'Program Officer' or user_role == 'Trainging Coordinator'):
                    user_report_cc_to_po = MisReport.objects.filter(report_to = user).values_list('report_person__id', flat=True)
                    awc_id = CC_AWC_AH.objects.filter(user__id__in=user_report_cc_to_po).values_list('awc_id', flat=True)
                elif (user_role == 'Cluster Coordinator'):
                    awc_id = CC_AWC_AH.objects.filter(user=user).values_list('awc_id', flat=True)
                block_id = AWC.objects.filter(id__in=awc_id).values_list('village__grama_panchayat__block__id', flat=True).distinct()
                district_id = AWC.objects.filter(id__in=awc_id).values_list('village__grama_panchayat__block__district__id', flat=True).distinct()
                districts = [{i.id: i.name} for i in District.objects.filter(id__in=district_id)]
                blocks = [{i.id: i.name} for i in Block.objects.filter(id__in=block_id)]
                request.session['user_district'] = districts
                request.session['user_block'] = blocks
                if (user_role == 'Senior Lead'):
                    return HttpResponseRedirect('/spo/monthly/report/')
                else:
                    return HttpResponseRedirect('/monthly/report/')
            else:
                logout(request)
                error_message = "Invalid Username and Password"

        else:
            logout(request)
            error_message = "Do not have access"
    return render(request, 'dashboard/login.html', locals())

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt 
def task_status_changes(request, task_id):
    if request.method == "POST":
        status_val = request.POST.get('status_val')
        remark = request.POST.get('remark')
        task_obj = Task.objects.get(id = task_id)
        task_obj.task_status = status_val
        task_obj.save()
        if remark:
            DataEntryRemark.objects.create(task = task_obj, remark = remark, user_name = request.user)
        return HttpResponse({"message":'true'} , content_type="application/json")
    return HttpResponse({"message":'false'}, content_type="application/json")  

# @ login_required(login_url='/login/')
def fossil_cc_monthly_report(request, task_id):
    
    current_site = request.session.get('site_id')
    task_obj = Task.objects.get(status=1, id=task_id)
    
    user = get_user(request)
    user_role = str(user.groups.last())
    awc_objs = AWC.objects.filter(id__in = task_obj.awc)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    health_sessions = AHSession.objects.filter(status=1, task__id = task_id)
    digital_literacy = DLSession.objects.filter(status=1, task__id = task_id)
    vocation =  AdolescentVocationalTraining.objects.filter(status=1,task__id = task_id)
    friendly_club = AdolescentFriendlyClub.objects.filter(status=1, task__id = task_id)
    balsansad_meeting = BalSansadMeeting.objects.filter(status=1, task__id = task_id)
    activities = CommunityEngagementActivities.objects.filter(status=1, task__id = task_id)
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, task__id = task_id)
    champions =  Champions.objects.filter(status=1, task__id = task_id)
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, task__id = task_id)
    cc_notes =  CCReportNotes.objects.filter()
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        successes = data.get('successes')
        challenges_faced = data.get('challenges_faced')
        feasible_solution_to_scale_up = data.get('feasible_solution_to_scale_up')
        task = Task.objects.get(id=task_id)
        if CCReportNotes.objects.filter(Q(successes__isnull=successes) & Q(challenges_faced__isnull=challenges_faced) & Q(feasible_solution_to_scale_up__isnull=feasible_solution_to_scale_up)).exists():
            return redirect('/fossil/cc/monthly/report/'+str(task_id) + '#fcc-report-notes')
        else:
            cc_notes =  CCReportNotes.objects.create(successes=successes, challenges_faced=challenges_faced, 
            feasible_solution_to_scale_up=feasible_solution_to_scale_up, task=task, site_id = current_site)
            cc_notes.save()

        return redirect('/fossil/cc/monthly/report/'+str(task_id) + '#fcc-report-notes')
        # return redirect('/admin/mis/ccreportnotes/')

    return render(request, 'cc_report/final_fossil.html', locals())

@ login_required(login_url='/login/')
def rnp_cc_monthly_report(request, task_id):
    current_site = request.session.get('site_id')
    task_obj = Task.objects.get(status=1, id=task_id)
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=task_obj.user).values_list('awc__village__grama_panchayat__id')
    # village_id = CC_AWC_AH.objects.filter(status=1, user=task_obj.user).values_list('awc__village__id')
    # school_id = CC_School.objects.filter(status=1, user=task_obj.user).values_list('school__id')
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=task_obj.user).values_list('awc__id')
    user = get_user(request)
    user_role = str(user.groups.last())
    awc_objs = AWC.objects.filter(id__in = task_obj.awc)
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True)))
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    vocation =  AdolescentVocationalTraining.objects.filter(status=1, task__id = task_id)
    friendly_club = AdolescentFriendlyClub.objects.filter(status=1, task__id = task_id)
    balsansad_meeting = BalSansadMeeting.objects.filter(status=1, task__id = task_id)
    activities = CommunityEngagementActivities.objects.filter(status=1, task__id = task_id)
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, task__id = task_id)
    champions =  Champions.objects.filter(status=1, task__id = task_id)
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    health_sessions = AHSession.objects.filter(status=1, task__id = task_id)
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, task__id = task_id)
    cc_notes =  CCReportNotes.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        successes = data.get('successes')
        challenges_faced = data.get('challenges_faced')
        feasible_solution_to_scale_up = data.get('feasible_solution_to_scale_up')
        task = Task.objects.get(id=task_id)
        if CCReportNotes.objects.filter(Q(successes__isnull=successes) & Q(challenges_faced__isnull=challenges_faced) & Q(feasible_solution_to_scale_up__isnull=feasible_solution_to_scale_up)).exists():
            return redirect('/rnp/cc/monthly/report/'+str(task_id) + '#rcc-report-notes')
        else:
            cc_notes =  CCReportNotes.objects.create(successes=successes, challenges_faced=challenges_faced, 
            feasible_solution_to_scale_up=feasible_solution_to_scale_up, task=task, site_id = current_site)
            cc_notes.save()

        return redirect('/rnp/cc/monthly/report/'+str(task_id) + '#rcc-report-notes')
        # return redirect('/admin/mis/ccreportnotes/')
    return render(request, 'cc_report/final_rnp.html', locals())

@ login_required(login_url='/login/')
def untrust_cc_monthly_report(request, task_id):
    current_site = request.session.get('site_id')
    task_obj = Task.objects.get(status=1, id=task_id)
    # block_id = CC_AWC_AH.objects.filter(status=1, user=task_obj.user).values_list('awc__village__grama_panchayat__block__id')
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=task_obj.user).values_list('awc__village__grama_panchayat__id')
    # village_id = CC_AWC_AH.objects.filter(status=1, user=task_obj.user).values_list('awc__village__id')
    # school_id = CC_School.objects.filter(status=1, user=task_obj.user).values_list('school__id')
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=task_obj.user).values_list('awc__id')
    user = get_user(request)
    user_role = str(user.groups.last())
    awc_objs = AWC.objects.filter(id__in = task_obj.awc)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    dcpu_bcpu = DCPU_BCPU.objects.filter(status=1, task__id = task_id)
    vlcpc_metting = VLCPCMetting.objects.filter(status=1, task__id = task_id)
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    health_sessions = AHSession.objects.filter(status=1, task__id = task_id)
    vocation =  AdolescentVocationalTraining.objects.filter(status=1, task__id = task_id)
    friendly_club = AdolescentFriendlyClub.objects.filter(status=1, task__id = task_id)
    balsansad_meeting = BalSansadMeeting.objects.filter(status=1, task__id = task_id)
    activities = CommunityEngagementActivities.objects.filter(status=1, task__id = task_id)
    education_enrichment = EducatinalEnrichmentSupportProvided.objects.filter(status=1, task__id = task_id)
    parent_vacation =  ParentVocationalTraining.objects.filter(status=1, task__id = task_id)
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, task__id = task_id)
    champions =  Champions.objects.filter(status=1, task__id = task_id)
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, task__id = task_id)
    cc_notes =  CCReportNotes.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')

    if request.method == 'POST':
        data = request.POST
        successes = data.get('successes')
        challenges_faced = data.get('challenges_faced')
        feasible_solution_to_scale_up = data.get('feasible_solution_to_scale_up')
        task = Task.objects.get(id=task_id)
        if CCReportNotes.objects.filter(Q(successes__isnull=successes) & Q(challenges_faced__isnull=challenges_faced) & Q(feasible_solution_to_scale_up__isnull=feasible_solution_to_scale_up)).exists():
            return redirect('/untrust/cc/monthly/report/'+str(task_id) + '#ucc-report-notes')
        else:
            cc_notes =  CCReportNotes.objects.create(successes=successes, challenges_faced=challenges_faced, 
            feasible_solution_to_scale_up=feasible_solution_to_scale_up, task=task, site_id = current_site)
            cc_notes.save()

        return redirect('/untrust/cc/monthly/report/'+str(task_id) + '#ucc-report-notes')
        # return redirect('/admin/mis/ccreportnotes/')
    return render(request, 'cc_report/final_un_trust.html', locals())

@ login_required(login_url='/login/')
def fossil_po_monthly_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(get_user(request).groups.last())
    current_site = request.session.get('site_id')
    if (user_role == 'Senior Program Officer'):
        user_report = MisReport.objects.filter(report_to = task_obj.user).values_list('report_person__id', flat=True)
        participating_meeting = ParticipatingMeeting.objects.filter(task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(task = task_obj)
        stakeholders_obj = Stakeholder.objects.filter(task = task_obj)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(task = task_obj)
    else:
        participating_meeting = ParticipatingMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(user_name=request.user.id, task = task_obj)
        stakeholders_obj = Stakeholder.objects.filter(user_name=request.user.id, task = task_obj)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(user_name=request.user.id, task = task_obj)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    
    task  =  Task.objects.filter(user__id__in = user_report, start_date=task_obj.start_date, end_date=task_obj.end_date).values_list('id', flat=True)
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    # village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # awc_dl_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')

    awc_id = CC_AWC_AH.objects.filter(status=1, user__id__in=user_report).values_list('awc__id', flat=True)
    awc_objs = AWC.objects.filter(id__in=awc_id)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()

    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    facility_visits = Events.objects.filter(status=1, task__id = task_id)

    health_sessions = ReportSection1.objects.filter(status=1, task__id__in = task)#1
    digital_literacy = ReportSection2.objects.filter(status=1, task__id__in = task)#2
    vocation =  ReportSection3.objects.filter(status=1, task__id__in = task)#3
    girls_ahwd = ReportSection4a.objects.filter(status=1, task__id__in = task)#4a
    boys_ahwd = ReportSection4b.objects.filter(status=1, task__id__in = task)#4b
    adolescents_referred =  ReportSection5.objects.filter(status=1, task__id__in = task)#5
    friendly_club = ReportSection6.objects.filter(status=1, task__id__in = task)#6
    balsansad_meeting = ReportSection7.objects.filter(status=1, task__id__in = task)#7
    activities = ReportSection8.objects.filter(status=1, task__id__in = task)#8
    champions =  ReportSection9.objects.filter(status=1, task__id__in = task)#9
    adolescent_reenrolled =  ReportSection10.objects.filter(status=1, task__id__in = task)#10
    po_notes =  POReportSection17.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')

    if request.method == 'POST':
        data = request.POST
        suggestions = data.get('suggestions')
        task = Task.objects.get(id=task_id)
        if POReportSection17.objects.filter(suggestions__isnull=suggestions).exists():
            return redirect('/fossil/po/monthly/report/'+str(task_id) + '#fpos-17')
        else:
            po_notes =  POReportSection17.objects.create(suggestions=suggestions, task=task, site_id = current_site)
            po_notes.save()
        return redirect('/fossil/po/monthly/report/'+str(task_id) + '#fpos-17')
    if Stakeholder.objects.filter(task=task_obj).exists():
        error="disabled"
    return render(request, 'po_report/fossil_mis_po.html', locals())


@ login_required(login_url='/login/')
def fossil_spo_monthly_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    
    user = get_user(request)
    current_site = request.session.get('site_id')
    user_role = str(get_user(request).groups.last())

    view_entry_flag = True
    if (user_role == 'Senior Program Officer'):
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
        sessions_monitoring = SessionMonitoring.objects.filter(status=1, task = task_obj)
        facility_visits = Events.objects.filter(status=1, task = task_obj)
        participating_meeting = ParticipatingMeeting.objects.filter(status=1, task = task_obj)
        faced_related = FacedRelatedOperation.objects.filter(status=1, task = task_obj)
        stakeholders_obj = Stakeholder.objects.filter(status=1, task = task_obj)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(status=1, task = task_obj)
    else:
        stakeholders_obj = Stakeholder.objects.filter(status=1,  task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(status=1,  task__id = task_id)
        participating_meeting = ParticipatingMeeting.objects.filter(status=1,  task__id = task_id)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(status=1,  task__id = task_id)
        sessions_monitoring = SessionMonitoring.objects.filter(status=1,  task__id = task_id)
        facility_visits = Events.objects.filter(status=1,  task__id = task_id)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)


    
    task  =  Task.objects.filter(user__id__in = user_report, start_date=task_obj.start_date, end_date=task_obj.end_date).values_list('id', flat=True)
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    # village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # awc_dl_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')

    awc_id = CC_AWC_AH.objects.filter(status=1, user__id__in=user_report).values_list('awc__id', flat=True)
    awc_objs = AWC.objects.filter(id__in=awc_id)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()

    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    facility_visits = Events.objects.filter(status=1, task__id = task_id)

    health_sessions = ReportSection1.objects.filter(status=1, task__id__in = task)#1
    digital_literacy = ReportSection2.objects.filter(status=1, task__id__in = task)#2
    vocation =  ReportSection3.objects.filter(status=1, task__id__in = task)#3
    girls_ahwd = ReportSection4a.objects.filter(status=1, task__id__in = task)#4a
    boys_ahwd = ReportSection4b.objects.filter(status=1, task__id__in = task)#4b
    adolescents_referred =  ReportSection5.objects.filter(status=1, task__id__in = task)#5
    friendly_club = ReportSection6.objects.filter(status=1, task__id__in = task)#6
    balsansad_meeting = ReportSection7.objects.filter(status=1, task__id__in = task)#7
    activities = ReportSection8.objects.filter(status=1, task__id__in = task)#8
    champions =  ReportSection9.objects.filter(status=1, task__id__in = task)#9
    adolescent_reenrolled =  ReportSection10.objects.filter(status=1, task__id__in = task)#10
    po_notes =  POReportSection17.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        suggestions = data.get('suggestions')
        task = Task.objects.get(id=task_id)
        if POReportSection17.objects.filter(suggestions__isnull=suggestions).exists():
            return redirect('/fossil/spo/monthly/report/'+str(task_id) + '#fpos-17')
        else:
            po_notes =  POReportSection17.objects.create(suggestions=suggestions, task=task, site_id = current_site)
            po_notes.save()

        return redirect('/fossil/spo/monthly/report/'+str(task_id) + '#fpos-17')
    if Stakeholder.objects.filter(task=task_obj).exists():
        error="disabled"
    return render(request, 'po_report/fossil_mis_po.html', locals())


@ login_required(login_url='/login/')
def rnp_po_monthly_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    
    current_site = request.session.get('site_id')
    user = get_user(request)
    user_role = str(user.groups.last())
    if (user_role == 'Senior Program Officer'):
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(task__id = task_id)
        participating_meeting = ParticipatingMeeting.objects.filter(task__id = task_id)
        stakeholders_obj = Stakeholder.objects.filter(task__id = task_id)
        user_report = MisReport.objects.filter(report_to = task_obj.user).values_list('report_person__id', flat=True)
        # user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
    else:
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(user_name=request.user.id, task__id = task_id)
        participating_meeting = ParticipatingMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
        stakeholders_obj = Stakeholder.objects.filter(user_name=request.user.id, task__id = task_id)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
      
    task  =  Task.objects.filter(user__id__in = user_report, start_date=task_obj.start_date, end_date=task_obj.end_date).values_list('id', flat=True)
    awc_id = CC_AWC_AH.objects.filter(status=1, user__id__in=user_report).values_list('awc__id', flat=True)
    awc_objs = AWC.objects.filter(id__in=awc_id)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    
    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    facility_visits = Events.objects.filter(status=1, task__id = task_id)

    health_sessions = ReportSection1.objects.filter(status=1, task__id__in = task)#1
    # digital_literacy = ReportSection2.objects.filter(status=1, task__id__in = task)#2
    vocation =  ReportSection3.objects.filter(status=1, task__id__in = task)#3
    girls_ahwd = ReportSection4a.objects.filter(status=1, task__id__in = task)#4a
    boys_ahwd = ReportSection4b.objects.filter(status=1, task__id__in = task)#4b
    adolescents_referred =  ReportSection5.objects.filter(status=1, task__id__in = task)#5
    friendly_club = ReportSection6.objects.filter(status=1, task__id__in = task)#6
    balsansad_meeting = ReportSection7.objects.filter(status=1, task__id__in = task)#7
    activities = ReportSection8.objects.filter(status=1, task__id__in = task)#8
    champions =  ReportSection9.objects.filter(status=1, task__id__in = task)#9
    adolescent_reenrolled =  ReportSection10.objects.filter(status=1, task__id__in = task)#10

    # girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id) #4
    # boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id) #5
    # health_sessions = AHSession.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id) #1
    # vocation =  AdolescentVocationalTraining.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)#3
    # friendly_club = AdolescentFriendlyClub.objects.filter(status=1, panchayat_name__id__in=panchayat_id, task__id = task_id) #7
    # balsansad_meeting = BalSansadMeeting.objects.filter(status=1, school_name__id__in=school_id, task__id = task_id)#8
    # activities =  CommunityEngagementActivities.objects.filter(status=1, village_name__id__in=village_id, task__id = task_id) #6
    # adolescents_referred =  AdolescentsReferred.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)#9
    # champions =  Champions.objects.filter(status=1, awc_name__id__in=awc_id)#10
    # adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id) #11
    
    po_notes =  POReportSection17.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        suggestions = data.get('suggestions')
        task = Task.objects.get(id=task_id)
        if POReportSection17.objects.filter(suggestions__isnull=suggestions).exists():
            return redirect('/rnp/po/monthly/report/'+str(task_id) + '#rpos-16')
        else:
            po_notes =  POReportSection17.objects.create(suggestions=suggestions, task=task, site_id = current_site)
            po_notes.save()

        return redirect('/rnp/po/monthly/report/'+str(task_id) + '#rpos-16')
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    return render(request, 'po_report/rnp_mis_po.html', locals())

@ login_required(login_url='/login/')
def rnp_tco_monthly_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    
    current_site = request.session.get('site_id')
    user = get_user(request)
    user_role = str(user.groups.last())
    if (user_role == 'Traing Coordinator'):
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(task__id = task_id)
        participating_meeting = ParticipatingMeeting.objects.filter(task__id = task_id)
        stakeholders_obj = Stakeholder.objects.filter(task__id = task_id)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
    else:
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(user_name=request.user.id, task__id = task_id)
        participating_meeting = ParticipatingMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
        stakeholders_obj = Stakeholder.objects.filter(user_name=request.user.id, task__id = task_id)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
   
    # user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    task  =  Task.objects.filter(user__id__in = user_report, start_date=task_obj.start_date, end_date=task_obj.end_date).values_list('id', flat=True)
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    # village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user__id__in=user_report).values_list('awc__id', flat=True)
    awc_objs = AWC.objects.filter(id__in=awc_id)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    
    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    facility_visits = Events.objects.filter(status=1, task__id = task_id)

    health_sessions = ReportSection1.objects.filter(status=1, task__id__in = task)#1
    # digital_literacy = ReportSection2.objects.filter(status=1, task__id__in = task)#2
    vocation =  ReportSection3.objects.filter(status=1, task__id__in = task)#3
    girls_ahwd = ReportSection4a.objects.filter(status=1, task__id__in = task)#4a
    boys_ahwd = ReportSection4b.objects.filter(status=1, task__id__in = task)#4b
    adolescents_referred =  ReportSection5.objects.filter(status=1, task__id__in = task)#5
    friendly_club = ReportSection6.objects.filter(status=1, task__id__in = task)#6
    balsansad_meeting = ReportSection7.objects.filter(status=1, task__id__in = task)#7
    activities = ReportSection8.objects.filter(status=1, task__id__in = task)#8
    champions =  ReportSection9.objects.filter(status=1, task__id__in = task)#9
    adolescent_reenrolled =  ReportSection10.objects.filter(status=1, task__id__in = task)#10
    po_notes =  POReportSection17.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        suggestions = data.get('suggestions')
        task = Task.objects.get(id=task_id)
        if POReportSection17.objects.filter(suggestions__isnull=suggestions).exists():
            return redirect('/rnp/tco/monthly/report/'+str(task_id) + '#rpos-16')
        else:
            po_notes =  POReportSection17.objects.create(suggestions=suggestions, task=task, site_id = current_site)
            po_notes.save()

        return redirect('/rnp/tco/monthly/report/'+str(task_id) + '#rpos-16')
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    return render(request, 'po_report/rnp_mis_po.html', locals())

@ login_required(login_url='/login/')
def rnp_spo_monthly_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)    
    user = get_user(request)
    user_role = str(get_user(request).groups.last())
    current_site = request.session.get('site_id')

    view_entry_flag = True
    if (user_role == 'Senior Program Officer'):
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
        
        sessions_monitoring = SessionMonitoring.objects.filter(status=1, task = task_obj)
        facility_visits = Events.objects.filter(status=1, task = task_obj)
        participating_meeting = ParticipatingMeeting.objects.filter(status=1, task = task_obj)
        faced_related = FacedRelatedOperation.objects.filter(status=1, task = task_obj)
        stakeholders_obj = Stakeholder.objects.filter(status=1, task = task_obj)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(status=1, task = task_obj)
    else:
        stakeholders_obj = Stakeholder.objects.filter(status=1, task = task_obj)
        faced_related = FacedRelatedOperation.objects.filter(status=1, task = task_obj)
        participating_meeting = ParticipatingMeeting.objects.filter(status=1, task = task_obj)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(status=1, task = task_obj)
        sessions_monitoring = SessionMonitoring.objects.filter(status=1, task = task_obj)
        facility_visits = Events.objects.filter(status=1, task = task_obj)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
   
    task  =  Task.objects.filter(user__id__in = user_report, start_date=task_obj.start_date, end_date=task_obj.end_date).values_list('id', flat=True)
    awc_id = CC_AWC_AH.objects.filter(status=1, user__id__in=user_report).values_list('awc__id', flat=True)
    awc_objs = AWC.objects.filter(id__in=awc_id)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    
    # sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    # facility_visits = Events.objects.filter(status=1, task__id = task_id)

    health_sessions = ReportSection1.objects.filter(status=1, task__id__in = task, )#1
    # digital_literacy = ReportSection2.objects.filter(status=1, task__id__in = task)#2
    vocation =  ReportSection3.objects.filter(status=1, task__id__in = task)#3
    girls_ahwd = ReportSection4a.objects.filter(status=1, task__id__in = task)#4a
    boys_ahwd = ReportSection4b.objects.filter(status=1, task__id__in = task)#4b
    adolescents_referred =  ReportSection5.objects.filter(status=1, task__id__in = task)#5
    friendly_club = ReportSection6.objects.filter(status=1, task__id__in = task)#6
    balsansad_meeting = ReportSection7.objects.filter(status=1, task__id__in = task)#7
    activities = ReportSection8.objects.filter(status=1, task__id__in = task)#8
    champions =  ReportSection9.objects.filter(status=1, task__id__in = task)#9
    adolescent_reenrolled =  ReportSection10.objects.filter(status=1, task__id__in = task)#10
    po_notes =  POReportSection17.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        suggestions = data.get('suggestions')
        task = Task.objects.get(id=task_id)
        if POReportSection17.objects.filter(suggestions__isnull=suggestions).exists():
            return redirect('/rnp/spo/monthly/report/'+str(task_id) + '#rpos-16')
        else:
            po_notes =  POReportSection17.objects.create(suggestions=suggestions, task=task, site_id = current_site)
            po_notes.save()

        return redirect('/rnp/spo/monthly/report/'+str(task_id) + '#rpos-16')
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    return render(request, 'po_report/rnp_mis_po.html', locals())

@ login_required(login_url='/login/')
def untrust_po_monthly_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    current_site = request.session.get('site_id')

    user_role = str(user.groups.last())
    if (user_role == 'Senior Program Officer'):
        stakeholders_obj = Stakeholder.objects.filter(task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(task__id = task_id)
        participating_meeting = ParticipatingMeeting.objects.filter(task__id = task_id)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(task__id = task_id)
        user_report = MisReport.objects.filter(report_to = task_obj.user).values_list('report_person__id', flat=True)
        # user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
    else:
        stakeholders_obj = Stakeholder.objects.filter(user_name=request.user.id, task__id = task_id)
        faced_related = FacedRelatedOperation.objects.filter(user_name=request.user.id, task__id = task_id)
        participating_meeting = ParticipatingMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    task  =  Task.objects.filter(user__id__in = user_report, start_date=task_obj.start_date, end_date=task_obj.end_date).values_list('id', flat=True)    
    awc_id = CC_AWC_AH.objects.filter(status=1, user__id__in=user_report).values_list('awc__id', flat=True)
    awc_objs = AWC.objects.filter(id__in=awc_id)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    
    facility_visits = Events.objects.filter(status=1, task__id = task_id)
    
    education_enrichment = UntrustEducatinalEnrichmentSupportProvided.objects.filter(status=1, task__id__in = task)
    dcpu_bcpu = UntrustDCPU_BCPU.objects.filter(status=1, task__id__in = task)
    vlcpc_metting = UntrustVLCPCMetting.objects.filter(status=1, task__id__in = task)
    health_sessions = ReportSection1.objects.filter(status=1, task__id__in = task)#1
    # digital_literacy = ReportSection2.objects.filter(status=1, task__id__in = task)#2
    vocation =  ReportSection3.objects.filter(status=1, task__id__in = task)#3
    girls_ahwd = ReportSection4a.objects.filter(status=1, task__id__in = task)#4a
    boys_ahwd = ReportSection4b.objects.filter(status=1, task__id__in = task)#4b
    adolescents_referred =  ReportSection5.objects.filter(status=1, task__id__in = task)#5
    friendly_club = ReportSection6.objects.filter(status=1, task__id__in = task)#6
    balsansad_meeting = ReportSection7.objects.filter(status=1, task__id__in = task)#7
    activities = ReportSection8.objects.filter(status=1, task__id__in = task)#8
    champions =  ReportSection9.objects.filter(status=1, task__id__in = task)#9
    adolescent_reenrolled =  ReportSection10.objects.filter(status=1, task__id__in = task)#10
    parent_vacation =  UntrustParentVocationalTraining.objects.filter(status=1, task__id__in = task)
    po_notes =  POReportSection17.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        suggestions = data.get('suggestions')
        task = Task.objects.get(id=task_id)
        if POReportSection17.objects.filter(suggestions__isnull=suggestions).exists():
            return redirect('/untrust/po/monthly/report/'+str(task_id) + '#upos-19')
        else:
            po_notes =  POReportSection17.objects.create(suggestions=suggestions, task=task, site_id = current_site)
            po_notes.save()

        return redirect('/untrust/po/monthly/report/'+str(task_id) + '#upos-19')
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    return render(request, 'po_report/un_trust_po.html', locals())

@ login_required(login_url='/login/')
def untrust_spo_monthly_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    current_site = request.session.get('site_id')
    user_role = str(get_user(request).groups.last())
    view_entry_flag = True
    if (user_role == 'Senior Program Officer'):
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
        sessions_monitoring = SessionMonitoring.objects.filter(status=1, task = task_obj)
        facility_visits = Events.objects.filter(status=1, task = task_obj)
        participating_meeting = ParticipatingMeeting.objects.filter(status=1, task = task_obj)
        faced_related = FacedRelatedOperation.objects.filter(status=1, task = task_obj)
        stakeholders_obj = Stakeholder.objects.filter(status=1, task = task_obj)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(status=1, task = task_obj)
    else:
        stakeholders_obj = Stakeholder.objects.filter(status=1,  task = task_obj)
        faced_related = FacedRelatedOperation.objects.filter(status=1,  task = task_obj)
        participating_meeting = ParticipatingMeeting.objects.filter(status=1,  task = task_obj)
        followup_liaision = FollowUP_LiaisionMeeting.objects.filter(status=1,  task = task_obj)
        sessions_monitoring = SessionMonitoring.objects.filter(status=1,  task = task_obj)
        facility_visits = Events.objects.filter(status=1,  task = task_obj)
        user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
        user_report = MisReport.objects.filter(report_to__id__in = user_report).values_list('report_person__id', flat=True)
    task  =  Task.objects.filter(user__id__in = user_report, start_date=task_obj.start_date, end_date=task_obj.end_date).values_list('id', flat=True)    
    awc_id = CC_AWC_AH.objects.filter(status=1, user__id__in=user_report).values_list('awc__id', flat=True)
    awc_objs = AWC.objects.filter(id__in=awc_id)
    village_id = awc_objs.values_list('village__id', flat=True )
    no_of_village = Village.objects.filter(id__in=village_id).count()
    block_name = list(set(awc_objs.values_list('village__grama_panchayat__block__name', flat=True )))
    district_name = list(set(awc_objs.values_list('village__grama_panchayat__block__district__name', flat=True)))
    cc_awc_ah = awc_objs.count()
    
    
    education_enrichment = UntrustEducatinalEnrichmentSupportProvided.objects.filter(status=1, task__id__in = task)
    dcpu_bcpu = UntrustDCPU_BCPU.objects.filter(status=1, task__id__in = task)
    vlcpc_metting = UntrustVLCPCMetting.objects.filter(status=1, task__id__in = task)
    health_sessions = ReportSection1.objects.filter(status=1, task__id__in = task)#1
    # digital_literacy = ReportSection2.objects.filter(status=1, task__id__in = task)#2
    vocation =  ReportSection3.objects.filter(status=1, task__id__in = task)#3
    girls_ahwd = ReportSection4a.objects.filter(status=1, task__id__in = task)#4a
    boys_ahwd = ReportSection4b.objects.filter(status=1, task__id__in = task)#4b
    adolescents_referred =  ReportSection5.objects.filter(status=1, task__id__in = task)#5
    friendly_club = ReportSection6.objects.filter(status=1, task__id__in = task)#6
    balsansad_meeting = ReportSection7.objects.filter(status=1, task__id__in = task)#7
    activities = ReportSection8.objects.filter(status=1, task__id__in = task)#8
    champions =  ReportSection9.objects.filter(status=1, task__id__in = task)#9
    adolescent_reenrolled =  ReportSection10.objects.filter(status=1, task__id__in = task)#10
    parent_vacation =  UntrustParentVocationalTraining.objects.filter(status=1, task__id__in = task)
    po_notes =  POReportSection17.objects.filter(task__id = task_id)
    need_revision =  DataEntryRemark.objects.filter(status=1, task__id = task_id).order_by('-server_created_on')
    
    if request.method == 'POST':
        data = request.POST
        suggestions = data.get('suggestions')
        task = Task.objects.get(id=task_id)
        if POReportSection17.objects.filter(suggestions__isnull=suggestions).exists():
            return redirect('/untrust/spo/monthly/report/'+str(task_id) + '#upos-19')
        else:
            po_notes =  POReportSection17.objects.create(suggestions=suggestions, task=task, site_id = current_site)
            po_notes.save()

        return redirect('/untrust/spo/monthly/report/'+str(task_id) + '#upos-19')
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    return render(request, 'po_report/un_trust_po.html', locals())


@ login_required(login_url='/login/')
def add_file(request):
    return render(request, 'dashboard/add_file.html', {})


@ login_required(login_url='/login/')
def monthly_report(request):
    heading = "Monthly Report"
    group = request.user.groups.all()
    # current_site = get_current_site(request)
    # current_site1 = getData(request)
    user_site_obj = UserSiteMapping.objects.get(status=1, user=request.user)
    # user_site_obj.site.objects.get_current()
    task  =  Task.objects.filter(status=1, user = user_site_obj.user,)
    
    user = get_user(request)
    if user.groups.filter(name = 'Program Officer').exists():
        if user_site_obj.site.name in ['fossil', 'c3neev']:
            report_site = '/fossil/po/monthly/report/'

        elif user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/po/monthly/report/'
            
        elif user_site_obj.site.name in ['untrust', 'c3manjari']:
            report_site = '/untrust/po/monthly/report/'

    elif (user.groups.filter(name = 'Cluster Coordinator').exists()):
        if user_site_obj.site.name in ['fossil', 'c3neev']:
            report_site = '/fossil/cc/monthly/report/'

        elif user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/cc/monthly/report/'
            
        elif user_site_obj.site.name in ['untrust', 'c3manjari']:
            report_site = '/untrust/cc/monthly/report/'
    
    elif (user.groups.filter(name = 'Trainging Coordinator').exists()):
        if user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/tco/monthly/report/'
            
    elif (user.groups.filter(name = 'Senior Program Officer').exists()):
        if user_site_obj.site.name in ['fossil', 'c3neev']:
            report_site = '/fossil/spo/monthly/report/'

        elif user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/spo/monthly/report/'
            
        elif user_site_obj.site.name in ['untrust', 'c3manjari']:
            report_site = '/untrust/spo/monthly/report/'
   
    return render(request, 'dashboard/task.html', locals())

@ login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')

#-----------cc-report  fossil---------------

@ login_required(login_url='/login/')
def cc_monthly_report(request):
    heading = "Monthly Report CC Monthly"
    group = request.user.groups.all()
    # current_site = get_current_site(request)
    # current_site1 = getData(request)
    user_site_obj = UserSiteMapping.objects.get(status=1, user=request.user)
    # user_site_obj.site.objects.get_current()
    # task  =  Task.objects.filter(status=1, user = user_site_obj.user,)

    report_person = MisReport.objects.filter(status=1, report_to = request.user).values_list('report_person__id', flat=True)

    task  =  Task.objects.filter(status=1, user__id__in = report_person)
    
    user = get_user(request)
    if user.groups.filter(name = 'Program Officer').exists():
        if user_site_obj.site.name in ['fossil', 'c3neev']:
            report_site = '/fossil/cc/monthly/report/'

        elif user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/cc/monthly/report/'
            
        elif user_site_obj.site.name in ['untrust', 'c3manjari']:
            report_site = '/untrust/cc/monthly/report/'
    
    else:
        if user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/cc/monthly/report/'
   
    return render(request, 'dashboard/task_list.html', locals())


@ login_required(login_url='/login/')
def po_monthly_report(request):
    heading = "Monthly Report PO Monthly"
    group = request.user.groups.all()
    user_site_obj = UserSiteMapping.objects.get(status=1, user=request.user)
    user_report = MisReport.objects.filter(status=1, report_to  = request.user).values_list('report_person__id', flat=True)
    task  =  Task.objects.filter(status=1, user__id__in = user_report)
    user = get_user(request)
   
    if (user.groups.filter(name = 'Senior Program Officer').exists()):
        if user_site_obj.site.name in ['fossil', 'c3neev']:
            report_site = '/fossil/po/monthly/report/'

        elif user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/po/monthly/report/'
            
        elif user_site_obj.site.name in ['untrust', 'c3manjari']:
            report_site = '/untrust/po/monthly/report/'
   
    return render(request, 'dashboard/task_list.html', locals())

@ login_required(login_url='/login/')
def spo_monthly_report(request):
    heading = "Monthly Report SPO Monthly"
    group = request.user.groups.all()
    user_site_obj = UserSiteMapping.objects.get(status=1, user=request.user)
    user_report = MisReport.objects.filter(status=1, report_to  = request.user).values_list('report_person__id', flat=True)
    task  =  Task.objects.filter(status=1, user__id__in = user_report)
    user = get_user(request)
   
    if (user.groups.filter(name = 'Senior Lead').exists()):
        if user_site_obj.site.name in ['fossil', 'c3neev']:
            report_site = '/fossil/spo/monthly/report/'

        elif user_site_obj.site.name in ['rnp', 'c3b4b']:
            report_site = '/rnp/spo/monthly/report/'
            
        elif user_site_obj.site.name in ['untrust', 'c3manjari']:
            report_site = '/untrust/spo/monthly/report/'
   
    return render(request, 'dashboard/task_list.html', locals())


def get_adolescent(request, awc_id):
    if request.method == 'GET' and request.is_ajax():
        result_set = []
        user_site_obj = UserSiteMapping.objects.get(status=1, user=request.user)
        # It is showing on rnp site at gender male data only.
        if user_site_obj.site.name in ['rnp', 'c3b4b']:
            adolescents = Adolescent.objects.filter(status=1, awc__id=awc_id, site=3).order_by('name')
        elif user_site_obj.site.name in ['untrust', 'c3manjari']:
            adolescents = Adolescent.objects.filter(status=1, awc__id=awc_id, site=4).order_by('name')
        else:
            adolescents = Adolescent.objects.filter(status=1, awc__id=awc_id).order_by('name')  
        for adolescent in adolescents:
            result_set.append(
                {'id': adolescent.id, 'name': f"{adolescent.name} - {adolescent.code}", })
        return HttpResponse(json.dumps(result_set))

def get_session_name(request, awc_id):
    if request.method == 'GET' and request.is_ajax():
        result_set = []
        fossilahsessions = FossilAHSession.objects.filter(status=1, fossil_ah_session_category__id=awc_id)
        for fossilahsession in fossilahsessions:
            result_set.append(
                {'id': fossilahsession.id, 'name': fossilahsession.session_name,})
        return HttpResponse(json.dumps(result_set))

@ login_required(login_url='/login/')
def health_sessions_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 1: Details of transaction of sessions on health & nutrition"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, health_sessions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/health_sessions/health_sessions_listing.html', locals())

@ login_required(login_url='/login/')
def add_health_sessions_fossil_cc_report(request, task_id):
    heading = "Section 1: Add of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')  
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(task__id = task_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1).exclude(session_category='Engaging Adolescents for Gender Equality Manual')
  
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id,)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session_selected_id = data.get('fossil_ah_session_category')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        fossil_ah_session_obj =  FossilAHSession.objects.filter(fossil_ah_session_category__id = fossil_ah_session_selected_id)
        session_day = data.get('session_day')
        
        age = data.get('age')
        gender = (data.get('gender'))
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'cc_report/fossil/health_sessions/add_health_sessions.html', locals())
        else:
            health_sessions = AHSession.objects.create(adolescent_name=adolescent_name, age=age or None, gender=gender or None, fossil_ah_session=fossil_ah_session,
            date_of_session=date_of_session, session_day=session_day, task=task, site_id = current_site, designation_data = designations, facilitator_name = facilitator_name)
            health_sessions.save()
        return redirect('/cc-report/fossil/health-sessions-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/health_sessions/add_health_sessions.html', locals())


@ login_required(login_url='/login/')
def edit_health_sessions_fossil_cc_report(request, ahsession_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 1: Edit of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.get(id=ahsession_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=health_sessions.adolescent_name.awc.id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    fossil_ah_session_obj =  FossilAHSession.objects.filter(status=1, fossil_ah_session_category__id=health_sessions.fossil_ah_session.fossil_ah_session_category.id)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1,).exclude(session_category='Engaging Adolescents for Gender Equality Manual')
    
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        age = data.get('age')
        gender_data = data.get('gender')
        gender = str(gender_data)
        fossil_ah_session_category = int(data.get('fossil_ah_session_category'))
        facilitator_name = data.get('facilitator_name')
        designations = str(data.get('designations'))
        date_of_session = data.get('date_of_session')
        session_day = data.get('session_day')
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exclude(id=ahsession_id).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'cc_report/fossil/health_sessions/edit_health_sessions.html', locals())
        else:
            health_sessions.adolescent_name_id = adolescent_name
            health_sessions.fossil_ah_session_id = fossil_ah_session
            health_sessions.date_of_session = date_of_session
            health_sessions.session_day = session_day
            health_sessions.gender = gender or None
            health_sessions.age = age or None
            health_sessions.designation_data = designations
            health_sessions.facilitator_name = facilitator_name
            health_sessions.site_id =  current_site
            health_sessions.save()
        return redirect('/cc-report/fossil/health-sessions-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/health_sessions/edit_health_sessions.html', locals())




@ login_required(login_url='/login/')
def digital_literacy_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2: Details of transaction of digital literacy sessions"
    # awc_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')
    digital_literacy = DLSession.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, digital_literacy)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/digital_literacy/digital_literacy_listing.html', locals())


@ login_required(login_url='/login/')
def add_digital_literacy_fossil_cc_report(request, task_id):
    heading = "Section 2: ADD of transaction of digital literacy sessions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')
    digital_literacy = DLSession.objects.filter(task__id = task_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    fossil_dl_session_category_obj =  FossilDLSessionConfig.objects.filter(status=1,)
    
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_dl_session_config_id = data.get('fossil_dl_session_config')
        fossil_dl_session_config = FossilDLSessionConfig.objects.get(id=fossil_dl_session_config_id)
        session_name = data.get('session_name')
        date_of_session = data.get('date_of_session')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        session_day = data.get('session_day')
        task = Task.objects.get(id=task_id)
        if DLSession.objects.filter(adolescent_name=adolescent_name, fossil_dl_session_config=fossil_dl_session_config,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "This data already exist!!!"
            return render(request, 'cc_report/fossil/digital_literacy/add_digital_literacy.html', locals())
        else:  
            digital_literacy = DLSession.objects.create(adolescent_name=adolescent_name, age=age or None, gender=gender or None,
            facilitator_name=facilitator_name, designation_data=designations, fossil_dl_session_config=fossil_dl_session_config,
            date_of_session=date_of_session, session_name=session_name, session_day=session_day, task=task, site_id = current_site)
            digital_literacy.save()
        return redirect('/cc-report/fossil/digital-literacy-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/digital_literacy/add_digital_literacy.html', locals())


@ login_required(login_url='/login/')
def edit_digital_literacy_fossil_cc_report(request, dlsession_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2: Edit of transaction of digital literacy sessions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')
    digital_literacy = DLSession.objects.get(id=dlsession_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=digital_literacy.adolescent_name.awc.id)
    fossil_dl_session_category_obj =  FossilDLSessionConfig.objects.filter(status=1,)

    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_dl_session_config_id = data.get('fossil_dl_session_config')
        fossil_dl_session_config = FossilDLSessionConfig.objects.get(id=fossil_dl_session_config_id)
        session_name = data.get('session_name')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        date_of_session = data.get('date_of_session')
        session_day = data.get('session_day')
        task = Task.objects.get(id=task_id)
        if DLSession.objects.filter(adolescent_name=adolescent_name, fossil_dl_session_config=fossil_dl_session_config,
                                    date_of_session=date_of_session,  status=1).exclude(id=dlsession_id).exists():
            exist_error = "This data already exist!!!"
            return render(request, 'cc_report/fossil/digital_literacy/edit_digital_literacy.html', locals())
        else:
            digital_literacy.adolescent_name_id = adolescent_name
            digital_literacy.fossil_dl_session_config_id = fossil_dl_session_config
            digital_literacy.date_of_session = date_of_session
            digital_literacy.session_name = session_name
            digital_literacy.age = age or None
            digital_literacy.gender = gender or None
            digital_literacy.facilitator_name = facilitator_name
            digital_literacy.designation_data = designations
            digital_literacy.session_day = session_day
            digital_literacy.task_id = task
            digital_literacy.site_id =  current_site
            digital_literacy.save()
        return redirect('/cc-report/fossil/digital-literacy-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/digital_literacy/edit_digital_literacy.html', locals())


@ login_required(login_url='/login/')
def girls_ahwd_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4(a): Details of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, girls_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/girls_ahwd/girls_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_girls_ahwd_fossil_cc_report(request, task_id):
    heading = "Section 4(a): Add of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter(task__id = task_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
  
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')

        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)
        

        girls_ahwd = GirlsAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        tt_10_14_years=tt_10_14_years, tt_15_19_years=tt_15_19_years, counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        girls_ahwd.save()
        return redirect('/cc-report/fossil/girls-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/girls_ahwd/add_girls_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_girls_ahwd_fossil_cc_report(request, girls_ahwd_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4(a): Edit of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.get(id=girls_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
  
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
            
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)
        

        girls_ahwd.place_of_ahwd = place_of_ahwd
        girls_ahwd.content_type = content_type
        girls_ahwd.object_id = selected_object_id
        girls_ahwd.hwc_name = hwc_name
        girls_ahwd.date_of_ahwd = date_of_ahwd
        girls_ahwd.participated_10_14_years = participated_10_14_years
        girls_ahwd.participated_15_19_years = participated_15_19_years
        girls_ahwd.bmi_10_14_years = bmi_10_14_years
        girls_ahwd.bmi_15_19_years = bmi_15_19_years
        girls_ahwd.hb_10_14_years = hb_10_14_years
        girls_ahwd.hb_15_19_years = hb_15_19_years
        girls_ahwd.tt_10_14_years = tt_10_14_years
        girls_ahwd.tt_15_19_years = tt_15_19_years
        girls_ahwd.counselling_10_14_years = counselling_10_14_years
        girls_ahwd.counselling_15_19_years = counselling_15_19_years
        girls_ahwd.referral_10_14_years = referral_10_14_years
        girls_ahwd.referral_15_19_years = referral_15_19_years
        girls_ahwd.task_id = task
        girls_ahwd.site_id =  current_site
        girls_ahwd.save()
        return redirect('/cc-report/fossil/girls-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/girls_ahwd/edit_girls_ahwd.html', locals())




@ login_required(login_url='/login/')
def boys_ahwd_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4(b): Details of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter( status=1, task__id = task_id)
    data = pagination_function(request, boys_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/boys_ahwd/boys_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_boys_ahwd_fossil_cc_report(request, task_id):
    heading = "Section 4(b): Add of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name') 
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)
       

        boys_ahwd = BoysAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd,  hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        boys_ahwd.save()
        return redirect('/cc-report/fossil/boys-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/boys_ahwd/add_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_boys_ahwd_fossil_cc_report(request, boys_ahwd_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4(b): Edit of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.get(id=boys_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd.place_of_ahwd = place_of_ahwd
        boys_ahwd.content_type = content_type
        boys_ahwd.object_id = selected_object_id
        boys_ahwd.hwc_name = hwc_name
        boys_ahwd.date_of_ahwd = date_of_ahwd
        boys_ahwd.participated_10_14_years = participated_10_14_years
        boys_ahwd.participated_15_19_years = participated_15_19_years
        boys_ahwd.bmi_10_14_years = bmi_10_14_years
        boys_ahwd.bmi_15_19_years = bmi_15_19_years
        boys_ahwd.hb_10_14_years = hb_10_14_years
        boys_ahwd.hb_15_19_years = hb_15_19_years
        boys_ahwd.counselling_10_14_years = counselling_10_14_years
        boys_ahwd.counselling_15_19_years = counselling_15_19_years
        boys_ahwd.referral_10_14_years = referral_10_14_years
        boys_ahwd.referral_15_19_years = referral_15_19_years
        boys_ahwd.task_id = task
        boys_ahwd.site_id =  current_site
        boys_ahwd.save()
        return redirect('/cc-report/fossil/boys-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/boys_ahwd/edit_boys_ahwd.html', locals())




@ login_required(login_url='/login/')
def vocation_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3: Details of adolescent linked with vocational training & placement"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # awc = AWC.objects.filter(status=1, id__in=awc_id)
    vocation_obj =  AdolescentVocationalTraining.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, vocation_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_vocation_fossil_cc_report(request, task_id):
    heading = "Section 3: Add of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter(status=1, task__id = task_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id=training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        
        vocation_obj = AdolescentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age or None, parent_guardian_name=parent_guardian_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered or None, placement_accepted=placement_accepted or None, type_of_employment=type_of_employment or None,
        task=task, site_id = current_site)
        vocation_obj.save()
        return redirect('/cc-report/fossil/vocation-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_vocation_fossil_cc_report(request, vocation_id,task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3: Edit of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.get(id=vocation_id)
    adolescent_obj =  Adolescent.objects.filter(awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered') 
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)

        vocation_obj.adolescent_name_id = adolescent_name
        vocation_obj.date_of_registration = date_of_registration
        vocation_obj.age = age or None
        vocation_obj.parent_guardian_name = parent_guardian_name
        vocation_obj.training_subject = training_subject
        vocation_obj.training_providing_by = training_providing_by
        vocation_obj.duration_days = duration_days
        vocation_obj.training_complated = training_complated
        vocation_obj.placement_offered = placement_offered or None
        vocation_obj.placement_accepted = placement_accepted or None
        vocation_obj.type_of_employment = type_of_employment or None
        vocation_obj.task_id = task
        vocation_obj.site_id =  current_site
        vocation_obj.save()
        return redirect('/cc-report/fossil/vocation-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/voctional_training/edit_vocation_training.html', locals())


@ login_required(login_url='/login/')
def adolescents_referred_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 5: Details of adolescents referred"
    current_site = request.session.get('site_id')
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, adolescents_referred)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/adolescent_referred/adolescent_referred_listing.html', locals())

@ login_required(login_url='/login/')
def add_adolescents_referred_fossil_cc_report(request, task_id):
    heading = "Section 5: Add of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')
        task = Task.objects.get(id=task_id)

        adolescents_referred = AdolescentsReferred.objects.create(awc_name=awc_name, girls_referred_10_14_year=girls_referred_10_14_year, 
        girls_referred_15_19_year=girls_referred_15_19_year, boys_referred_10_14_year=boys_referred_10_14_year, boys_referred_15_19_year=boys_referred_15_19_year,
        girls_hwc_referred=girls_hwc_referred, girls_hwc_visited=girls_hwc_visited, girls_afhc_referred=girls_afhc_referred, girls_afhc_visited=girls_afhc_visited,
        girls_dh_referred=girls_dh_referred, girls_dh_visited=girls_dh_visited, boys_hwc_referred=boys_hwc_referred, boys_hwc_visited=boys_hwc_visited,
        boys_afhc_referred=boys_afhc_referred, boys_afhc_visited=boys_afhc_visited, 
        boys_dh_referred=boys_dh_referred, boys_dh_visited=boys_dh_visited, task=task, site_id = current_site)
        adolescents_referred.save()
        return redirect('/cc-report/fossil/adolescent-referred-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/adolescent_referred/add_adolescen_referred.html', locals())


@ login_required(login_url='/login/')
def edit_adolescents_referred_fossil_cc_report(request, adolescents_referred_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 5: Edit of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.get(id=adolescents_referred_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')  
        task = Task.objects.get(id=task_id)

        adolescents_referred.awc_name_id = awc_name
        adolescents_referred.girls_referred_10_14_year = girls_referred_10_14_year
        adolescents_referred.girls_referred_15_19_year = girls_referred_15_19_year
        adolescents_referred.boys_referred_10_14_year = boys_referred_10_14_year
        adolescents_referred.boys_referred_15_19_year = boys_referred_15_19_year
        adolescents_referred.girls_hwc_referred = girls_hwc_referred
        adolescents_referred.girls_hwc_visited = girls_hwc_visited
        adolescents_referred.girls_afhc_referred = girls_afhc_referred
        adolescents_referred.girls_afhc_visited = girls_afhc_visited
        adolescents_referred.girls_dh_referred = girls_dh_referred
        adolescents_referred.girls_dh_visited = girls_dh_visited
        adolescents_referred.boys_hwc_referred = boys_hwc_referred
        adolescents_referred.boys_hwc_visited = boys_hwc_visited
        adolescents_referred.boys_afhc_referred = boys_afhc_referred
        adolescents_referred.boys_afhc_visited = boys_afhc_visited
        adolescents_referred.boys_dh_referred = boys_dh_referred
        adolescents_referred.boys_dh_visited = boys_dh_visited
        adolescents_referred.task_id = task
        adolescents_referred.site_id =  current_site
        adolescents_referred.save()
        return redirect('/cc-report/fossil/adolescent-referred-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/adolescent_referred/edit_adolescent_referred.html', locals())



@ login_required(login_url='/login/')
def friendly_club_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 6: Details of Adolescent Friendly Club (AFC)"
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, friendly_club)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/friendly_club/friendly_club_listing.html', locals())

@ login_required(login_url='/login/')
def add_friendly_club_fossil_cc_report(request, task_id):
    heading = "Section 6: Add of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        date_of_registration = data.get('date_of_registration')
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club = AdolescentFriendlyClub.objects.create(panchayat_name=panchayat_name,
        start_date = date_of_registration, hsc_name=hsc_name, subject=subject, facilitator=facilitator, designation=designation,
        no_of_sahiya=no_of_sahiya, no_of_aww=no_of_aww, pe_girls_10_14_year=pe_girls_10_14_year,
        pe_girls_15_19_year=pe_girls_15_19_year, pe_boys_10_14_year=pe_boys_10_14_year,
        pe_boys_15_19_year=pe_boys_15_19_year, task=task, site_id = current_site)
        friendly_club.save()
        return redirect('/cc-report/fossil/friendly-club-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/friendly_club/add_friendly_club.html', locals())



@ login_required(login_url='/login/')
def edit_friendly_club_fossil_cc_report(request, friendly_club_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 6: Edit of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.get(id=friendly_club_id)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        panchayat_name_id = data.get('panchayat_name')
        date_of_registration = data.get('date_of_registration')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)
       

        friendly_club.panchayat_name_id = panchayat_name
        friendly_club.start_date = date_of_registration
        friendly_club.hsc_name = hsc_name
        friendly_club.subject = subject
        friendly_club.facilitator = facilitator
        friendly_club.designation = designation
        friendly_club.no_of_sahiya = no_of_sahiya
        friendly_club.no_of_aww = no_of_aww
        friendly_club.pe_girls_10_14_year = pe_girls_10_14_year
        friendly_club.pe_girls_15_19_year = pe_girls_15_19_year
        friendly_club.pe_boys_10_14_year = pe_boys_10_14_year
        friendly_club.pe_boys_15_19_year = pe_boys_15_19_year
        friendly_club.task_id = task
        friendly_club.site_id =  current_site
        friendly_club.save()
        return redirect('/cc-report/fossil/friendly-club-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/friendly_club/edit_friendly_club.html', locals())


@ login_required(login_url='/login/')
def balsansad_meeting_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 7: Details of Bal Sansad meetings conducted"
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, balsansad_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/bal_sansad_metting/bal_sansad_listing.html', locals())

@ login_required(login_url='/login/')
def add_balsansad_meeting_fossil_cc_report(request, task_id):
    heading = "Section 7: Add of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter()
    school = School.objects.filter(status=1, id__in=school_id).order_by('name')
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        issues_discussion = data.get('issues_discussion')
        decision_taken = data.get('decision_taken')
        task = Task.objects.get(id=task_id)
        balsansad_meeting = BalSansadMeeting.objects.create(start_date = date_of_registration, school_name = school_name,
        no_of_participants=no_of_participants,   decision_taken=decision_taken,
        task=task, site_id =  current_site)

        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion

        balsansad_meeting.save()
        return redirect('/cc-report/fossil/balsansad-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/bal_sansad_metting/add_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def edit_balsansad_meeting_fossil_cc_report(request, balsansad_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 7: Edit of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.get(id=balsansad_id)
    school = School.objects.filter(status=1, id__in=school_id).order_by('name')
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        issues_discussion = data.get('issues_discussion')
        decision_taken = data.get('decision_taken')
        task = Task.objects.get(id=task_id)
        balsansad_meeting.start_date = date_of_registration
        balsansad_meeting.school_name_id = school_name
        balsansad_meeting.no_of_participants = no_of_participants
        balsansad_meeting.decision_taken = decision_taken
        balsansad_meeting.task_id = task
        balsansad_meeting.site_id =  current_site
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/cc-report/fossil/balsansad-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/bal_sansad_metting/edit_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def community_activities_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 8: Details of community engagement activities"
    # village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, activities)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/community_activities/community_activities_listing.html', locals())


@ login_required(login_url='/login/')
def add_community_activities_fossil_cc_report(request, task_id):
    heading = "Section 8: Add of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1,)
    village =  Village.objects.filter(status=1, id__in=village_id).order_by('name')
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity') 
        name_of_event_activity = data.get('name_of_event_activity')
        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities =  CommunityEngagementActivities.objects.create(village_name=village_name, start_date = date_of_registration,
        name_of_event_activity=name_of_event_activity, organized_by=organized_by,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year, adult_male=adult_male,
        adult_female=adult_female, teachers=teachers, pri_members=pri_members, services_providers=services_providers,
        sms_members=sms_members, other=other, task=task, site_id = current_site)
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id=name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id=name_of_activity_id)
            activities.activity_name = name_of_activity

        activities.save()
        return redirect('/cc-report/fossil/community-activities-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/community_activities/add_community_activities.html', locals())


@ login_required(login_url='/login/')
def edit_community_activities_fossil_cc_report(request, activities_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 8: Edit of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.get(id=activities_id)
    village =  Village.objects.filter(status=1, id__in=village_id).order_by('name')
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        # theme_topic = data.get('theme_topic')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')

        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities.start_date = date_of_registration
        activities.village_name_id = village_name
        activities.name_of_event_activity = name_of_event_activity
        # activities.theme_topic = theme_topic
        activities.organized_by = organized_by
        activities.boys_10_14_year = boys_10_14_year
        activities.boys_15_19_year = boys_15_19_year
        activities.girls_10_14_year = girls_10_14_year
        activities.girls_15_19_year = girls_15_19_year
        activities.champions_15_19_year = champions_15_19_year
        activities.adult_male = adult_male
        activities.adult_female = adult_female
        activities.teachers = teachers
        activities.pri_members = pri_members
        activities.services_providers = services_providers
        activities.sms_members = sms_members
        activities.other = other
        activities.task_id = task
        activities.site_id =  current_site
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/cc-report/fossil/community-activities-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/community_activities/edit_community_activities.html', locals())





@ login_required(login_url='/login/')
def champions_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 9: Details of exposure visits of adolescent champions"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, champions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/champions/champions_listing.html', locals())

@ login_required(login_url='/login/')
def add_champions_fossil_cc_report(request, task_id):
    heading = "Section 9: Add of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1,)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions =  Champions.objects.create(awc_name=awc_name, date_of_visit=date_of_visit, girls_10_14_year=girls_10_14_year,
        girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year, boys_15_19_year=boys_15_19_year,
        first_inst_visited=first_inst_visited,second_inst_visited=second_inst_visited or None,
        third_inst_visited=third_inst_visited or None, fourth_inst_visited=fourth_inst_visited or None, task=task, site_id = current_site)
        champions.save()
        return redirect('/cc-report/fossil/champions-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/champions/add_champions.html', locals())


@ login_required(login_url='/login/')
def edit_champions_fossil_cc_report(request, champions_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 9: Edit of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.get(id=champions_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions.awc_name_id = awc_name       
        champions.date_of_visit = date_of_visit       
        champions.girls_10_14_year = girls_10_14_year       
        champions.girls_15_19_year = girls_15_19_year     
        champions.boys_10_14_year = boys_10_14_year       
        champions.boys_15_19_year = boys_15_19_year       
        champions.first_inst_visited = first_inst_visited
        champions.second_inst_visited= second_inst_visited or None
        champions.third_inst_visited = third_inst_visited or None
        champions.fourth_inst_visited = fourth_inst_visited or None
        champions.task_id = task
        champions.site_id =  current_site       
        champions.save()
        return redirect('/cc-report/fossil/champions-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/champions/edit_champions.html', locals())

@ login_required(login_url='/login/')
def reenrolled_listing_fossil_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 10: Details of adolescent re-enrolled in schools"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, adolescent_reenrolled)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/fossil/re_enrolled/re_enrolled_listing.html', locals())

@ login_required(login_url='/login/')
def add_reenrolled_fossil_cc_report(request, task_id):
    heading = "Section 10: Add of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # school = School.objects.filter(status=1, id__in = school_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled =  AdolescentRe_enrolled.objects.create(adolescent_name=adolescent_name,
        gender=gender or None, age=age or None, parent_guardian_name=parent_guardian_name, school_name=school_name, which_class_enrolled=which_class_enrolled,
        task=task, site_id = current_site)
        adolescent_reenrolled.save()
        return redirect('/cc-report/fossil/reenrolled-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/re_enrolled/add_re_enrolled.html', locals())


@ login_required(login_url='/login/')
def edit_reenrolled_fossil_cc_report(request, reenrolled_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 10: Edit of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.get(id=reenrolled_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    # school = School.objects.filter()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled.adolescent_name_id = adolescent_name
        adolescent_reenrolled.gender = gender or None
        adolescent_reenrolled.age = age or None
        adolescent_reenrolled.parent_guardian_name = parent_guardian_name
        adolescent_reenrolled.school_name = school_name
        adolescent_reenrolled.which_class_enrolled = which_class_enrolled
        adolescent_reenrolled.task_id = task
        adolescent_reenrolled.site_id =  current_site
        adolescent_reenrolled.save()
        return redirect('/cc-report/fossil/reenrolled-listing/'+str(task_id))
    return render(request, 'cc_report/fossil/re_enrolled/edit_re_enrolled.html', locals())


#-----------cc-report  rnp---------------






@ login_required(login_url='/login/')
def health_sessions_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 1: Details of transaction of sessions on health & nutrition"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, health_sessions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/health_sessions/health_sessions_listing.html', locals())

@ login_required(login_url='/login/')
def add_health_sessions_rnp_cc_report(request, task_id):
    heading = "Section 1: Add of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(status=1)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1)
  
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id,)
        fossil_ah_session_id = data.get('fossil_ah_session')
        age = data.get('age')
        gender = data.get('gender')
        fossil_ah_session_selected_id = data.get('fossil_ah_session_category')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        fossil_ah_session_obj =  FossilAHSession.objects.filter(fossil_ah_session_category__id = fossil_ah_session_selected_id)
        session_day = data.get('session_day')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'cc_report/rnp/health_sessions/add_health_sessions.html', locals())
        else:
            health_sessions = AHSession.objects.create(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
            date_of_session=date_of_session, session_day=session_day, designation_data = designations,
            age = age or None, gender=gender or None, facilitator_name = facilitator_name, task=task, site_id = current_site)
            health_sessions.save()
        return redirect('/cc-report/rnp/health-sessions-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/health_sessions/add_health_sessions.html', locals())

@ login_required(login_url='/login/')
def edit_health_sessions_rnp_cc_report(request, ahsession_id, task_id):
    heading = "Section 1: Edit of transaction of sessions on health & nutrition"
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.get(id=ahsession_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=health_sessions.adolescent_name.awc.id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    fossil_ah_session_obj =  FossilAHSession.objects.filter(status=1, fossil_ah_session_category__id=health_sessions.fossil_ah_session.fossil_ah_session_category.id)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1,)
    
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        age = data.get('age')
        gender = data.get('gender')
        session_day = data.get('session_day')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exclude(id=ahsession_id).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'cc_report/rnp/health_sessions/edit_health_sessions.html', locals())
        else:
            health_sessions.adolescent_name_id = adolescent_name
            health_sessions.fossil_ah_session_id = fossil_ah_session
            health_sessions.date_of_session = date_of_session
            health_sessions.age = age or None
            health_sessions.gender = gender or None
            health_sessions.session_day = session_day
            health_sessions.designation_data = designations
            health_sessions.facilitator_name = facilitator_name
            health_sessions.task_id = task
            health_sessions.site_id =  current_site
            health_sessions.save()
        return redirect('/cc-report/rnp/health-sessions-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/health_sessions/edit_health_sessions.html', locals())


@ login_required(login_url='/login/')
def girls_ahwd_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(a): Details of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, girls_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/girls_ahwd/girls_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_girls_ahwd_rnp_cc_report(request, task_id):
    heading = "Section 3(a): Add of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model)  if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd = GirlsAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        tt_10_14_years=tt_10_14_years, tt_15_19_years=tt_15_19_years, counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        girls_ahwd.save()
        return redirect('/cc-report/rnp/girls-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/girls_ahwd/add_girls_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_girls_ahwd_rnp_cc_report(request, girls_ahwd_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(a): Edit of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.get(id=girls_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model)  if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd.place_of_ahwd = place_of_ahwd
        girls_ahwd.content_type = content_type
        girls_ahwd.object_id = selected_object_id
        girls_ahwd.hwc_name = hwc_name
        girls_ahwd.date_of_ahwd = date_of_ahwd
        girls_ahwd.participated_10_14_years = participated_10_14_years
        girls_ahwd.participated_15_19_years = participated_15_19_years
        girls_ahwd.bmi_10_14_years = bmi_10_14_years
        girls_ahwd.bmi_15_19_years = bmi_15_19_years
        girls_ahwd.hb_10_14_years = hb_10_14_years
        girls_ahwd.hb_15_19_years = hb_15_19_years
        girls_ahwd.tt_10_14_years = tt_10_14_years
        girls_ahwd.tt_15_19_years = tt_15_19_years
        girls_ahwd.counselling_10_14_years = counselling_10_14_years
        girls_ahwd.counselling_15_19_years = counselling_15_19_years
        girls_ahwd.referral_10_14_years = referral_10_14_years
        girls_ahwd.referral_15_19_years = referral_15_19_years
        girls_ahwd.task_id = task
        girls_ahwd.site_id =  current_site
        girls_ahwd.save()
        return redirect('/cc-report/rnp/girls-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/girls_ahwd/edit_girls_ahwd.html', locals())




@ login_required(login_url='/login/')
def boys_ahwd_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(b): Details of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, boys_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/boys_ahwd/boys_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_boys_ahwd_rnp_cc_report(request, task_id):
    heading = "Section 3(b): Add of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd = BoysAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        boys_ahwd.save()
        return redirect('/cc-report/rnp/boys-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/boys_ahwd/add_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_boys_ahwd_rnp_cc_report(request, boys_ahwd_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(b): Edit of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.get(id=boys_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model)  if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd.place_of_ahwd = place_of_ahwd
        boys_ahwd.content_type = content_type
        boys_ahwd.object_id = selected_object_id
        boys_ahwd.hwc_name = hwc_name
        boys_ahwd.date_of_ahwd = date_of_ahwd
        boys_ahwd.participated_10_14_years = participated_10_14_years
        boys_ahwd.participated_15_19_years = participated_15_19_years
        boys_ahwd.bmi_10_14_years = bmi_10_14_years
        boys_ahwd.bmi_15_19_years = bmi_15_19_years
        boys_ahwd.hb_10_14_years = hb_10_14_years
        boys_ahwd.hb_15_19_years = hb_15_19_years
        boys_ahwd.counselling_10_14_years = counselling_10_14_years
        boys_ahwd.counselling_15_19_years = counselling_15_19_years
        boys_ahwd.referral_10_14_years = referral_10_14_years
        boys_ahwd.referral_15_19_years = referral_15_19_years
        boys_ahwd.task_id = task
        boys_ahwd.site_id =  current_site
        boys_ahwd.save()
        return redirect('/cc-report/rnp/boys-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/boys_ahwd/edit_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def vocation_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2: Details of adolescent boys linked with vocational training & placement"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj = AdolescentVocationalTraining.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, vocation_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_vocation_rnp_cc_report(request, task_id):
    heading = "Section 2: Add of adolescent boys linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id=training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        vocation_obj = AdolescentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age or None, parent_guardian_name=parent_guardian_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered or None, placement_accepted=placement_accepted or None, type_of_employment=type_of_employment or None,
        task=task, site_id = current_site)
        vocation_obj.save()
        return redirect('/cc-report/rnp/vocation-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_vocation_rnp_cc_report(request, vocation_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2: Edit of adolescent boys linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.get(id=vocation_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)

        vocation_obj.adolescent_name_id = adolescent_name
        vocation_obj.date_of_registration = date_of_registration
        vocation_obj.age = age or None
        vocation_obj.parent_guardian_name = parent_guardian_name
        vocation_obj.training_subject = training_subject
        vocation_obj.training_providing_by = training_providing_by
        vocation_obj.duration_days = duration_days
        vocation_obj.training_complated = training_complated
        vocation_obj.placement_offered = placement_offered or None
        vocation_obj.placement_accepted = placement_accepted or None
        vocation_obj.type_of_employment = type_of_employment or None
        vocation_obj.task_id = task
        vocation_obj.site_id =  current_site
        vocation_obj.save()
        return redirect('/cc-report/rnp/vocation-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/voctional_training/edit_vocation_training.html', locals())


@ login_required(login_url='/login/')
def adolescents_referred_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4: Details of adolescents referred"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, adolescents_referred)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/adolescent_referred/adolescent_referred_listing.html', locals())

@ login_required(login_url='/login/')
def add_adolescents_referred_rnp_cc_report(request, task_id):
    heading = "Section 4: Add of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')
        task = Task.objects.get(id=task_id)
        adolescents_referred = AdolescentsReferred.objects.create(awc_name=awc_name, girls_referred_10_14_year=girls_referred_10_14_year, 
        girls_referred_15_19_year=girls_referred_15_19_year, boys_referred_10_14_year=boys_referred_10_14_year, boys_referred_15_19_year=boys_referred_15_19_year,
        girls_hwc_referred=girls_hwc_referred, girls_hwc_visited=girls_hwc_visited, girls_afhc_referred=girls_afhc_referred, girls_afhc_visited=girls_afhc_visited,
        girls_dh_referred=girls_dh_referred, girls_dh_visited=girls_dh_visited, boys_hwc_referred=boys_hwc_referred, boys_hwc_visited=boys_hwc_visited,
        boys_afhc_referred=boys_afhc_referred, boys_afhc_visited=boys_afhc_visited, 
        boys_dh_referred=boys_dh_referred, boys_dh_visited=boys_dh_visited, task=task, site_id = current_site)
        adolescents_referred.save()
        return redirect('/cc-report/rnp/adolescent-referred-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/adolescent_referred/add_adolescen_referred.html', locals())


@ login_required(login_url='/login/')
def edit_adolescents_referred_rnp_cc_report(request, adolescents_referred_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4: Edit of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.get(id=adolescents_referred_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')  
        task = Task.objects.get(id=task_id)

        adolescents_referred.awc_name_id = awc_name
        adolescents_referred.girls_referred_10_14_year = girls_referred_10_14_year
        adolescents_referred.girls_referred_15_19_year = girls_referred_15_19_year
        adolescents_referred.boys_referred_10_14_year = boys_referred_10_14_year
        adolescents_referred.boys_referred_15_19_year = boys_referred_15_19_year
        adolescents_referred.girls_hwc_referred = girls_hwc_referred
        adolescents_referred.girls_hwc_visited = girls_hwc_visited
        adolescents_referred.girls_afhc_referred = girls_afhc_referred
        adolescents_referred.girls_afhc_visited = girls_afhc_visited
        adolescents_referred.girls_dh_referred = girls_dh_referred
        adolescents_referred.girls_dh_visited = girls_dh_visited
        adolescents_referred.boys_hwc_referred = boys_hwc_referred
        adolescents_referred.boys_hwc_visited = boys_hwc_visited
        adolescents_referred.boys_afhc_referred = boys_afhc_referred
        adolescents_referred.boys_afhc_visited = boys_afhc_visited
        adolescents_referred.boys_dh_referred = boys_dh_referred
        adolescents_referred.boys_dh_visited = boys_dh_visited
        adolescents_referred.task_id = task
        adolescents_referred.site_id =  current_site
        adolescents_referred.save()
        return redirect('/cc-report/rnp/adolescent-referred-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/adolescent_referred/edit_adolescent_referred.html', locals())

@ login_required(login_url='/login/')
def friendly_club_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 5: Details of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, friendly_club)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/friendly_club/friendly_club_listing.html', locals())

@ login_required(login_url='/login/')
def add_friendly_club_rnp_cc_report(request, task_id):
    heading = "Section 5: Add of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club = AdolescentFriendlyClub.objects.create(panchayat_name=panchayat_name,
        hsc_name=hsc_name, subject=subject, start_date=date_of_registration, facilitator=facilitator, designation=designation,
        no_of_sahiya=no_of_sahiya, no_of_aww=no_of_aww, pe_girls_10_14_year=pe_girls_10_14_year,
        pe_girls_15_19_year=pe_girls_15_19_year, pe_boys_10_14_year=pe_boys_10_14_year,
        pe_boys_15_19_year=pe_boys_15_19_year, task=task, site_id = current_site)
        friendly_club.save()
        return redirect('/cc-report/rnp/friendly-club-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/friendly_club/add_friendly_club.html', locals())



@ login_required(login_url='/login/')
def edit_friendly_club_rnp_cc_report(request, friendly_club_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 5: Edit of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.get(id=friendly_club_id)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)
        friendly_club.start_date = date_of_registration

        friendly_club.panchayat_name_id = panchayat_name
        friendly_club.hsc_name = hsc_name
        friendly_club.subject = subject
        friendly_club.facilitator = facilitator
        friendly_club.designation = designation
        friendly_club.no_of_sahiya = no_of_sahiya
        friendly_club.no_of_aww = no_of_aww
        friendly_club.pe_girls_10_14_year = pe_girls_10_14_year
        friendly_club.pe_girls_15_19_year = pe_girls_15_19_year
        friendly_club.pe_boys_10_14_year = pe_boys_10_14_year
        friendly_club.pe_boys_15_19_year = pe_boys_15_19_year
        friendly_club.task_id = task
        friendly_club.site_id =  current_site
        friendly_club.save()
        return redirect('/cc-report/rnp/friendly-club-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/friendly_club/edit_friendly_club.html', locals())

@ login_required(login_url='/login/')
def balsansad_meeting_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 6: Details of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, balsansad_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/bal_sansad_metting/bal_sansad_listing.html', locals())

@ login_required(login_url='/login/')
def add_balsansad_meeting_rnp_cc_report(request, task_id):
    heading = "Section 6: Add of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter()
    school = School.objects.filter(status=1, id__in=school_id).order_by('name')
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        issues_discussion = data.get('issues_discussion')
        decision_taken = data.get('decision_taken')
        task = Task.objects.get(id=task_id)
        balsansad_meeting = BalSansadMeeting.objects.create(start_date = date_of_registration, school_name=school_name,
        no_of_participants=no_of_participants, decision_taken=decision_taken,
        task=task, site_id = current_site)
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/cc-report/rnp/balsansad-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/bal_sansad_metting/add_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def edit_balsansad_meeting_rnp_cc_report(request, balsansad_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 6: Edit of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.get(id=balsansad_id)
    school = School.objects.filter(status=1, id__in=school_id).order_by('name')
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        issues_discussion = data.get('issues_discussion')
        decision_taken = data.get('decision_taken')
        task = Task.objects.get(id=task_id)
        balsansad_meeting.start_date = date_of_registration
        balsansad_meeting.school_name_id = school_name
        balsansad_meeting.no_of_participants = no_of_participants
        balsansad_meeting.decision_taken = decision_taken
        balsansad_meeting.task_id = task
        balsansad_meeting.site_id =  current_site
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/cc-report/rnp/balsansad-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/bal_sansad_metting/edit_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def community_activities_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 7: Details of community engagement activities"
    # village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, activities)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/community_activities/community_activities_listing.html', locals())


@ login_required(login_url='/login/')
def add_community_activities_rnp_cc_report(request, task_id):
    heading = "Section 7: Add of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1,)
    village =  Village.objects.filter(status=1, id__in=village_id).order_by('name')
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')
        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities =  CommunityEngagementActivities.objects.create(village_name=village_name, start_date = date_of_registration,
        name_of_event_activity=name_of_event_activity, organized_by=organized_by,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year, adult_male=adult_male,
        adult_female=adult_female, teachers=teachers, pri_members=pri_members, services_providers=services_providers,
        sms_members=sms_members, other=other, task=task, site_id = current_site)
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id=name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id=name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/cc-report/rnp/community-activities-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/community_activities/add_community_activities.html', locals())


@ login_required(login_url='/login/')
def edit_community_activities_rnp_cc_report(request, activities_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 7: Edit of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.get(id=activities_id)
    village =  Village.objects.filter(status=1, id__in=village_id).order_by('name')
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        # theme_topic = data.get('theme_topic')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')

        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities.start_date = date_of_registration
        activities.village_name_id = village_name
        activities.name_of_event_activity = name_of_event_activity
        # activities.theme_topic = theme_topic
        activities.organized_by = organized_by
        activities.boys_10_14_year = boys_10_14_year
        activities.boys_15_19_year = boys_15_19_year
        activities.girls_10_14_year = girls_10_14_year
        activities.girls_15_19_year = girls_15_19_year
        activities.champions_15_19_year = champions_15_19_year
        activities.adult_male = adult_male
        activities.adult_female = adult_female
        activities.teachers = teachers
        activities.pri_members = pri_members
        activities.services_providers = services_providers
        activities.sms_members = sms_members
        activities.other = other
        activities.task_id = task
        activities.site_id =  current_site
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/cc-report/rnp/community-activities-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/community_activities/edit_community_activities.html', locals())


@ login_required(login_url='/login/')
def champions_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 8: Details of exposure visits of adolescent champions"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, champions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/champions/champions_listing.html', locals())

@ login_required(login_url='/login/')
def add_champions_rnp_cc_report(request, task_id):
    heading = "Section 8: Add of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions =  Champions.objects.create(awc_name=awc_name, date_of_visit=date_of_visit, girls_10_14_year=girls_10_14_year,
        girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year, boys_15_19_year=boys_15_19_year,
        first_inst_visited=first_inst_visited,second_inst_visited=second_inst_visited or None,
        third_inst_visited=third_inst_visited or None, fourth_inst_visited=fourth_inst_visited or None, task=task, site_id = current_site)
        champions.save()
        return redirect('/cc-report/rnp/champions-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/champions/add_champions.html', locals())


@ login_required(login_url='/login/')
def edit_champions_rnp_cc_report(request, champions_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 8: Edit of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.get(id=champions_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions.awc_name_id = awc_name       
        champions.date_of_visit = date_of_visit 
        champions.girls_10_14_year = girls_10_14_year       
        champions.girls_15_19_year = girls_15_19_year     
        champions.boys_10_14_year = boys_10_14_year       
        champions.boys_15_19_year = boys_15_19_year       
        champions.first_inst_visited = first_inst_visited
        champions.second_inst_visited= second_inst_visited or None
        champions.third_inst_visited = third_inst_visited or None
        champions.fourth_inst_visited = fourth_inst_visited or None
        champions.task_id = task
        champions.site_id =  current_site       
        champions.save()
        return redirect('/cc-report/rnp/champions-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/champions/edit_champions.html', locals())

@ login_required(login_url='/login/')
def reenrolled_listing_rnp_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 9: Details of adolescent re-enrolled in schools"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, adolescent_reenrolled)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/rnp/re_enrolled/re_enrolled_listing.html', locals())

@ login_required(login_url='/login/')
def add_reenrolled_rnp_cc_report(request, task_id):
    heading = "Section 9: Add of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # school = School.objects.filter(status=1, id__in = school_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)
       

        adolescent_reenrolled =  AdolescentRe_enrolled.objects.create(adolescent_name=adolescent_name,
        gender=gender or None, age=age or None, parent_guardian_name=parent_guardian_name, school_name=school_name, which_class_enrolled=which_class_enrolled,
        task=task, site_id = current_site)
        adolescent_reenrolled.save()
        return redirect('/cc-report/rnp/reenrolled-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/re_enrolled/add_re_enrolled.html', locals())


@ login_required(login_url='/login/')
def edit_reenrolled_rnp_cc_report(request, reenrolled_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 9: Edit of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.get(id=reenrolled_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    # school = School.objects.filter()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)
        

        adolescent_reenrolled.adolescent_name_id = adolescent_name
        adolescent_reenrolled.gender = gender or None
        adolescent_reenrolled.age = age or None
        adolescent_reenrolled.parent_guardian_name = parent_guardian_name
        adolescent_reenrolled.school_name = school_name
        adolescent_reenrolled.which_class_enrolled = which_class_enrolled
        adolescent_reenrolled.task_id = task
        adolescent_reenrolled.site_id =  current_site
        adolescent_reenrolled.save()
        return redirect('/cc-report/rnp/reenrolled-listing/'+str(task_id))
    return render(request, 'cc_report/rnp/re_enrolled/edit_re_enrolled.html', locals())


#------------cc-report untrust

@ login_required(login_url='/login/')
def health_sessions_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 1: Details of transaction of sessions on health & nutrition"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, health_sessions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/health_sessions/health_sessions_listing.html', locals())

@ login_required(login_url='/login/')
def add_health_sessions_untrust_cc_report(request, task_id):
    heading = "Section 1: Add of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1)
  
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id,)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session_selected_id = data.get('fossil_ah_session_category')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        age = data.get('age')
        gender = data.get('gender')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        fossil_ah_session_obj =  FossilAHSession.objects.filter(fossil_ah_session_category__id = fossil_ah_session_selected_id)
        session_day = data.get('session_day')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'cc_report/untrust/health_sessions/add_health_sessions.html', locals())
        else:
            health_sessions = AHSession.objects.create(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
            date_of_session=date_of_session, session_day=session_day,designation_data = designations,
            age=age or None, gender=gender or None, facilitator_name = facilitator_name, task=task, site_id = current_site)
            health_sessions.save()
        return redirect('/cc-report/untrust/health-sessions-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/health_sessions/add_health_sessions.html', locals())


@ login_required(login_url='/login/')
def edit_health_sessions_untrust_cc_report(request, ahsession_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 1: Edit of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.get(id=ahsession_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=health_sessions.adolescent_name.awc.id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    fossil_ah_session_obj =  FossilAHSession.objects.filter(status=1, fossil_ah_session_category__id=health_sessions.fossil_ah_session.fossil_ah_session_category.id)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1,)
    
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exclude(id=ahsession_id).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request, 'cc_report/untrust/health_sessions/edit_health_sessions.html', locals())
        else:
            health_sessions.adolescent_name_id = adolescent_name
            health_sessions.fossil_ah_session_id = fossil_ah_session
            health_sessions.age = age or None
            health_sessions.gender = gender or None
            health_sessions.date_of_session = date_of_session
            health_sessions.session_day = session_day
            health_sessions.designation_data = designations
            health_sessions.facilitator_name = facilitator_name
            health_sessions.task_id = task
            health_sessions.site_id =  current_site
            health_sessions.save()
        return redirect('/cc-report/untrust/health-sessions-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/health_sessions/edit_health_sessions.html', locals())


@ login_required(login_url='/login/')
def girls_ahwd_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(a): Details of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, girls_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/girls_ahwd/girls_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_girls_ahwd_untrust_cc_report(request, task_id):
    heading = "Section 3(a): Add of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd = GirlsAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        tt_10_14_years=tt_10_14_years, tt_15_19_years=tt_15_19_years, counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        girls_ahwd.save()
        return redirect('/cc-report/untrust/girls-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/girls_ahwd/add_girls_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_girls_ahwd_untrust_cc_report(request, girls_ahwd_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(a): Edit of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.get(id=girls_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd.place_of_ahwd = place_of_ahwd
        girls_ahwd.content_type = content_type
        girls_ahwd.object_id = selected_object_id
        girls_ahwd.hwc_name = hwc_name
        girls_ahwd.date_of_ahwd = date_of_ahwd
        girls_ahwd.participated_10_14_years = participated_10_14_years
        girls_ahwd.participated_15_19_years = participated_15_19_years
        girls_ahwd.bmi_10_14_years = bmi_10_14_years
        girls_ahwd.bmi_15_19_years = bmi_15_19_years
        girls_ahwd.hb_10_14_years = hb_10_14_years
        girls_ahwd.hb_15_19_years = hb_15_19_years
        girls_ahwd.tt_10_14_years = tt_10_14_years
        girls_ahwd.tt_15_19_years = tt_15_19_years
        girls_ahwd.counselling_10_14_years = counselling_10_14_years
        girls_ahwd.counselling_15_19_years = counselling_15_19_years
        girls_ahwd.referral_10_14_years = referral_10_14_years
        girls_ahwd.referral_15_19_years = referral_15_19_years
        girls_ahwd.task_id = task
        girls_ahwd.site_id =  current_site
        girls_ahwd.save()
        return redirect('/cc-report/untrust/girls-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/girls_ahwd/edit_girls_ahwd.html', locals())




@ login_required(login_url='/login/')
def boys_ahwd_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(b): Details of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, boys_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/boys_ahwd/boys_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_boys_ahwd_untrust_cc_report(request, task_id):
    heading = "Section 3(b): Add of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd = BoysAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        boys_ahwd.save()
        return redirect('/cc-report/untrust/boys-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/boys_ahwd/add_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_boys_ahwd_untrust_cc_report(request, boys_ahwd_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 3(b): Edit of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.get(id=boys_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd.place_of_ahwd = place_of_ahwd
        boys_ahwd.content_type = content_type
        boys_ahwd.object_id = selected_object_id
        boys_ahwd.hwc_name = hwc_name
        boys_ahwd.date_of_ahwd = date_of_ahwd
        boys_ahwd.participated_10_14_years = participated_10_14_years
        boys_ahwd.participated_15_19_years = participated_15_19_years
        boys_ahwd.bmi_10_14_years = bmi_10_14_years
        boys_ahwd.bmi_15_19_years = bmi_15_19_years
        boys_ahwd.hb_10_14_years = hb_10_14_years
        boys_ahwd.hb_15_19_years = hb_15_19_years
        boys_ahwd.counselling_10_14_years = counselling_10_14_years
        boys_ahwd.counselling_15_19_years = counselling_15_19_years
        boys_ahwd.referral_10_14_years = referral_10_14_years
        boys_ahwd.referral_15_19_years = referral_15_19_years
        boys_ahwd.task_id = task
        boys_ahwd.site_id =  current_site
        boys_ahwd.save()
        return redirect('/cc-report/untrust/boys-ahwd-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/boys_ahwd/edit_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def vocation_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2(a): Details of adolescent linked with vocational training & placement"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')

    vocation_obj =  AdolescentVocationalTraining.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, vocation_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_vocation_untrust_cc_report(request, task_id):
    heading = "Section 2(a): Add of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id=training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        vocation_obj = AdolescentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age or None, parent_guardian_name=parent_guardian_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered or None, placement_accepted=placement_accepted or None, type_of_employment=type_of_employment or None,
        task=task, site_id = current_site)
        vocation_obj.save()
        return redirect('/cc-report/untrust/vocation-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_vocation_untrust_cc_report(request, vocation_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2(a): Edit of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.get(id=vocation_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)

        vocation_obj.adolescent_name_id = adolescent_name
        vocation_obj.date_of_registration = date_of_registration
        vocation_obj.age = age or None
        vocation_obj.parent_guardian_name = parent_guardian_name
        vocation_obj.training_subject = training_subject
        vocation_obj.training_providing_by = training_providing_by
        vocation_obj.duration_days = duration_days
        vocation_obj.training_complated = training_complated
        vocation_obj.placement_offered = placement_offered or None
        vocation_obj.placement_accepted = placement_accepted or None
        vocation_obj.type_of_employment = type_of_employment or None
        vocation_obj.task_id = task
        vocation_obj.site_id =  current_site
        vocation_obj.save()
        return redirect('/cc-report/untrust/vocation-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/voctional_training/edit_vocation_training.html', locals())


@ login_required(login_url='/login/')
def parents_vocation_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2(b): Details of parents linked with vocational training & placement"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    parents_vocation =  ParentVocationalTraining.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, parents_vocation)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/parents_voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_parents_vocation_untrust_cc_report(request, task_id):
    heading = "Section 2(b): Add of parents linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    parents_vocation =  ParentVocationalTraining.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.filter(status=1,)

    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_name = data.get('parent_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        parents_vocation = ParentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age or None, parent_name=parent_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered or None, placement_accepted=placement_accepted or None, type_of_employment=type_of_employment or None,
        task=task, site_id = current_site)
        parents_vocation.save()
        return redirect('/cc-report/untrust/parents-vocation-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/parents_voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_parents_vocation_untrust_cc_report(request, parent_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 2(b): Edit of parents linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    parents_vocation =  ParentVocationalTraining.objects.get(id=parent_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    tranining_sub_obj = TrainingSubject.objects.filter(status=1,)

    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_name = data.get('parent_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)

        parents_vocation.adolescent_name_id = adolescent_name
        parents_vocation.date_of_registration = date_of_registration
        parents_vocation.age = age or None
        parents_vocation.parent_name = parent_name
        parents_vocation.training_subject = training_subject
        parents_vocation.training_providing_by = training_providing_by
        parents_vocation.duration_days = duration_days
        parents_vocation.training_complated = training_complated
        parents_vocation.placement_offered = placement_offered  or None
        parents_vocation.placement_accepted = placement_accepted  or None
        parents_vocation.type_of_employment = type_of_employment  or None
        parents_vocation.task_id = task
        parents_vocation.site_id =  current_site
        parents_vocation.save()
        return redirect('/cc-report/untrust/parents-vocation-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/parents_voctional_training/edit_vocation_training.html', locals())


@ login_required(login_url='/login/')
def adolescents_referred_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4: Details of adolescents referred"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, adolescents_referred)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/adolescent_referred/adolescent_referred_listing.html', locals())

@ login_required(login_url='/login/')
def add_adolescents_referred_untrust_cc_report(request, task_id):
    heading = "Section 4: Add of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')
        task = Task.objects.get(id=task_id)
        adolescents_referred = AdolescentsReferred.objects.create(awc_name=awc_name, girls_referred_10_14_year=girls_referred_10_14_year, 
        girls_referred_15_19_year=girls_referred_15_19_year, boys_referred_10_14_year=boys_referred_10_14_year, boys_referred_15_19_year=boys_referred_15_19_year,
        girls_hwc_referred=girls_hwc_referred, girls_hwc_visited=girls_hwc_visited, girls_afhc_referred=girls_afhc_referred, girls_afhc_visited=girls_afhc_visited,
        girls_dh_referred=girls_dh_referred, girls_dh_visited=girls_dh_visited, boys_hwc_referred=boys_hwc_referred, boys_hwc_visited=boys_hwc_visited,
        boys_afhc_referred=boys_afhc_referred, boys_afhc_visited=boys_afhc_visited, 
        boys_dh_referred=boys_dh_referred, boys_dh_visited=boys_dh_visited, task=task, site_id = current_site)
        adolescents_referred.save()
        return redirect('/cc-report/untrust/adolescent-referred-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/adolescent_referred/add_adolescen_referred.html', locals())


@ login_required(login_url='/login/')
def edit_adolescents_referred_untrust_cc_report(request, adolescents_referred_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 4: Edit of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.get(id=adolescents_referred_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')  
        task = Task.objects.get(id=task_id)

        adolescents_referred.awc_name_id = awc_name
        adolescents_referred.girls_referred_10_14_year = girls_referred_10_14_year
        adolescents_referred.girls_referred_15_19_year = girls_referred_15_19_year
        adolescents_referred.boys_referred_10_14_year = boys_referred_10_14_year
        adolescents_referred.boys_referred_15_19_year = boys_referred_15_19_year
        adolescents_referred.girls_hwc_referred = girls_hwc_referred
        adolescents_referred.girls_hwc_visited = girls_hwc_visited
        adolescents_referred.girls_afhc_referred = girls_afhc_referred
        adolescents_referred.girls_afhc_visited = girls_afhc_visited
        adolescents_referred.girls_dh_referred = girls_dh_referred
        adolescents_referred.girls_dh_visited = girls_dh_visited
        adolescents_referred.boys_hwc_referred = boys_hwc_referred
        adolescents_referred.boys_hwc_visited = boys_hwc_visited
        adolescents_referred.boys_afhc_referred = boys_afhc_referred
        adolescents_referred.boys_afhc_visited = boys_afhc_visited
        adolescents_referred.boys_dh_referred = boys_dh_referred
        adolescents_referred.boys_dh_visited = boys_dh_visited
        adolescents_referred.task_id = task
        adolescents_referred.site_id =  current_site
        adolescents_referred.save()
        return redirect('/cc-report/untrust/adolescent-referred-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/adolescent_referred/edit_adolescent_referred.html', locals())


@ login_required(login_url='/login/')
def friendly_club_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 5: Details of Adolescent Friendly Club (AFC)"
    # panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, friendly_club)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/friendly_club/friendly_club_listing.html', locals())

@ login_required(login_url='/login/')
def add_friendly_club_untrust_cc_report(request, task_id):
    heading = "Section 5: Add of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club = AdolescentFriendlyClub.objects.create(panchayat_name=panchayat_name,
        hsc_name=hsc_name, subject=subject, start_date=date_of_registration, facilitator=facilitator, designation=designation,
        no_of_sahiya=no_of_sahiya, no_of_aww=no_of_aww, pe_girls_10_14_year=pe_girls_10_14_year,
        pe_girls_15_19_year=pe_girls_15_19_year, pe_boys_10_14_year=pe_boys_10_14_year,
        pe_boys_15_19_year=pe_boys_15_19_year, task=task, site_id = current_site)
        friendly_club.save()
        return redirect('/cc-report/untrust/friendly-club-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/friendly_club/add_friendly_club.html', locals())



@ login_required(login_url='/login/')
def edit_friendly_club_untrust_cc_report(request, friendly_club_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 5: Edit of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.get(id=friendly_club_id)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club.start_date = date_of_registration
        friendly_club.panchayat_name_id = panchayat_name
        friendly_club.hsc_name = hsc_name
        friendly_club.subject = subject
        friendly_club.facilitator = facilitator
        friendly_club.designation = designation
        friendly_club.no_of_sahiya = no_of_sahiya
        friendly_club.no_of_aww = no_of_aww
        friendly_club.pe_girls_10_14_year = pe_girls_10_14_year
        friendly_club.pe_girls_15_19_year = pe_girls_15_19_year
        friendly_club.pe_boys_10_14_year = pe_boys_10_14_year
        friendly_club.pe_boys_15_19_year = pe_boys_15_19_year
        friendly_club.task_id = task
        friendly_club.site_id =  current_site
        friendly_club.save()
        return redirect('/cc-report/untrust/friendly-club-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/friendly_club/edit_friendly_club.html', locals())


@ login_required(login_url='/login/')
def balsansad_meeting_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 6: Details of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    # school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, balsansad_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/bal_sansad_metting/bal_sansad_listing.html', locals())

@ login_required(login_url='/login/')
def add_balsansad_meeting_untrust_cc_report(request, task_id):
    heading = "Section 6: Add of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter()
    school = School.objects.filter(status=1, id__in=school_id).order_by('name')
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        issues_discussion = data.get('issues_discussion')
        decision_taken = data.get('decision_taken')
        task = Task.objects.get(id=task_id)
        balsansad_meeting = BalSansadMeeting.objects.create(start_date = date_of_registration, school_name=school_name,
        no_of_participants=no_of_participants, decision_taken=decision_taken,
        task=task, site_id = current_site)
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/cc-report/untrust/balsansad-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/bal_sansad_metting/add_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def edit_balsansad_meeting_untrust_cc_report(request, balsansad_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 6: Edit of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.get(id=balsansad_id)
    school = School.objects.filter(status=1, id__in=school_id).order_by('name')
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        decision_taken = data.get('decision_taken')
        issues_discussion = data.get('issues_discussion')
        task = Task.objects.get(id=task_id)
        balsansad_meeting.start_date = date_of_registration
        balsansad_meeting.school_name_id = school_name
        balsansad_meeting.no_of_participants = no_of_participants
        balsansad_meeting.decision_taken = decision_taken
        balsansad_meeting.task_id = task
        balsansad_meeting.site_id =  current_site
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/cc-report/untrust/balsansad-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/bal_sansad_metting/edit_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def community_activities_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 7: Details of community engagement activities"
    # village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, activities)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/community_activities/community_activities_listing.html', locals())


@ login_required(login_url='/login/')
def add_community_activities_untrust_cc_report(request, task_id):
    heading = "Section 7: Add of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1, )
    village =  Village.objects.filter(status=1, id__in=village_id).order_by('name')
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')
        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities =  CommunityEngagementActivities.objects.create(village_name=village_name, start_date = date_of_registration,
        name_of_event_activity=name_of_event_activity, organized_by=organized_by,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year, adult_male=adult_male,
        adult_female=adult_female, teachers=teachers, pri_members=pri_members, services_providers=services_providers,
        sms_members=sms_members, other=other, task=task, site_id = current_site)
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id=name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id=name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/cc-report/untrust/community-activities-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/community_activities/add_community_activities.html', locals())


@ login_required(login_url='/login/')
def edit_community_activities_untrust_cc_report(request, activities_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 7: Edit of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.get(id=activities_id)
    village =  Village.objects.filter(status=1, id__in=village_id).order_by('name')
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        # theme_topic = data.get('theme_topic')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')

        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities.start_date = date_of_registration
        activities.village_name_id = village_name
        activities.name_of_event_activity = name_of_event_activity
        # activities.theme_topic = theme_topic
        activities.organized_by = organized_by
        activities.boys_10_14_year = boys_10_14_year
        activities.boys_15_19_year = boys_15_19_year
        activities.girls_10_14_year = girls_10_14_year
        activities.girls_15_19_year = girls_15_19_year
        activities.champions_15_19_year = champions_15_19_year
        activities.adult_male = adult_male
        activities.adult_female = adult_female
        activities.teachers = teachers
        activities.pri_members = pri_members
        activities.services_providers = services_providers
        activities.sms_members = sms_members
        activities.other = other
        activities.task_id = task
        activities.site_id =  current_site
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/cc-report/untrust/community-activities-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/community_activities/edit_community_activities.html', locals())


@ login_required(login_url='/login/')
def champions_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 8: Details of exposure visits of adolescent champions"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, champions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/champions/champions_listing.html', locals())

@ login_required(login_url='/login/')
def add_champions_untrust_cc_report(request, task_id):
    heading = "Section 8: Add of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions =  Champions.objects.create(awc_name=awc_name, date_of_visit=date_of_visit, girls_10_14_year=girls_10_14_year,
        girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year, boys_15_19_year=boys_15_19_year,
        first_inst_visited=first_inst_visited,second_inst_visited=second_inst_visited or None,
        third_inst_visited=third_inst_visited or None, fourth_inst_visited=fourth_inst_visited or None,  task=task, site_id = current_site)
        champions.save()
        return redirect('/cc-report/untrust/champions-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/champions/add_champions.html', locals())


@ login_required(login_url='/login/')
def edit_champions_untrust_cc_report(request, champions_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 8: Edit of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.get(id=champions_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions.awc_name_id = awc_name       
        champions.date_of_visit = date_of_visit 
        champions.girls_10_14_year = girls_10_14_year       
        champions.girls_15_19_year = girls_15_19_year     
        champions.boys_10_14_year = boys_10_14_year       
        champions.boys_15_19_year = boys_15_19_year       
        champions.first_inst_visited = first_inst_visited
        champions.second_inst_visited= second_inst_visited or None
        champions.third_inst_visited = third_inst_visited or None
        champions.fourth_inst_visited = fourth_inst_visited or None
        champions.task_id = task
        champions.site_id =  current_site       
        champions.save()
        return redirect('/cc-report/untrust/champions-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/champions/edit_champions.html', locals())

@ login_required(login_url='/login/')
def reenrolled_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 9: Details of adolescent re-enrolled in schools"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, adolescent_reenrolled)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/re_enrolled/re_enrolled_listing.html', locals())

@ login_required(login_url='/login/')
def add_reenrolled_untrust_cc_report(request, task_id):
    heading = "Section 9: Add of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # school = School.objects.filter(status=1, id__in = school_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled =  AdolescentRe_enrolled.objects.create(adolescent_name=adolescent_name,
        gender=gender or None, age=age or None, parent_guardian_name=parent_guardian_name, school_name=school_name, which_class_enrolled=which_class_enrolled,
        task=task, site_id = current_site)
        adolescent_reenrolled.save()
        return redirect('/cc-report/untrust/reenrolled-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/re_enrolled/add_re_enrolled.html', locals())


@ login_required(login_url='/login/')
def edit_reenrolled_untrust_cc_report(request, reenrolled_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 9: Edit of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.get(id=reenrolled_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    # school = School.objects.filter()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled.adolescent_name_id = adolescent_name
        adolescent_reenrolled.gender = gender or None
        adolescent_reenrolled.age = age or None
        adolescent_reenrolled.parent_guardian_name = parent_guardian_name
        adolescent_reenrolled.school_name = school_name
        adolescent_reenrolled.which_class_enrolled = which_class_enrolled
        adolescent_reenrolled.task_id = task
        adolescent_reenrolled.site_id =  current_site
        adolescent_reenrolled.save()
        return redirect('/cc-report/untrust/reenrolled-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/re_enrolled/edit_re_enrolled.html', locals())

@ login_required(login_url='/login/')
def vlcpc_meeting_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 10: Details of VLCPC meetings"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vlcpc_metting =  VLCPCMetting.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, vlcpc_metting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/vlcpc_meetings/vlcpc_meeting_listing.html', locals())

@ login_required(login_url='/login/')
def add_vlcpc_meeting_untrust_cc_report(request, task_id):
    heading = "Section 10: Add of VLCPC meetings"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vlcpc_metting =  VLCPCMetting.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        date_of_meeting = data.get('date_of_meeting')
        issues_discussed = data.get('issues_discussed')
        decision_taken = data.get('decision_taken')
        no_of_participants_planned = data.get('no_of_participants_planned')
        no_of_participants_attended = data.get('no_of_participants_attended')
        task = Task.objects.get(id=task_id)

        vlcpc_metting = VLCPCMetting.objects.create(awc_name=awc_name, date_of_meeting=date_of_meeting,
        issues_discussed=issues_discussed, decision_taken=decision_taken, no_of_participants_planned=no_of_participants_planned,
        no_of_participants_attended=no_of_participants_attended, task=task, site_id = current_site)
        vlcpc_metting.save()
        return redirect('/cc-report/untrust/vlcpc-meeting-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/vlcpc_meetings/add_vlcpc_meeting.html', locals())


@ login_required(login_url='/login/')
def edit_vlcpc_meeting_untrust_cc_report(request, vlcpc_metting, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 10: Edit of VLCPC meetings"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vlcpc_metting =  VLCPCMetting.objects.get(id=vlcpc_metting)
    awc =  AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        date_of_meeting = data.get('date_of_meeting')
        issues_discussed = data.get('issues_discussed')
        decision_taken = data.get('decision_taken')
        no_of_participants_planned = data.get('no_of_participants_planned')
        no_of_participants_attended = data.get('no_of_participants_attended')
        task = Task.objects.get(id=task_id)

        vlcpc_metting.awc_name_id = awc_name
        vlcpc_metting.date_of_meeting = date_of_meeting
        vlcpc_metting.issues_discussed = issues_discussed
        vlcpc_metting.decision_taken = decision_taken
        vlcpc_metting.no_of_participants_planned = no_of_participants_planned
        vlcpc_metting.no_of_participants_attended = no_of_participants_attended
        vlcpc_metting.task_id = task
        vlcpc_metting.site_id =  current_site
        vlcpc_metting.save()
        return redirect('/cc-report/untrust/vlcpc-meeting-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/vlcpc_meetings/edit_vlcpc_meeting.html', locals())

@ login_required(login_url='/login/')
def dcpu_bcpu_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 11: Details of DCPU/BCPU engagement at community and institutional level"
    # block_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__block__id')
    dcpu_bcpu = DCPU_BCPU.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, dcpu_bcpu)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/dcpu_bcpu/dcpu_bcpu_listing.html', locals())

@ login_required(login_url='/login/')
def add_dcpu_bcpu_untrust_cc_report(request, task_id):
    heading = "Section 11: Add of DCPU/BCPU engagement at community and institutional level"
    current_site = request.session.get('site_id')
    block_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__block__id')
    dcpu_bcpu = DCPU_BCPU.objects.filter(status=1)
    block_obj = Block.objects.filter(status=1, id__in=block_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        block_name_id = data.get('block_name')
        block_name = Block.objects.get(id=block_name_id)
        name_of_institution = data.get('name_of_institution')
        date_of_visit = data.get('date_of_visit')
        name_of_lead = data.get('name_of_lead')
        designation = data.get('designation')
        issues_discussed = data.get('issues_discussed')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)
        
        dcpu_bcpu = DCPU_BCPU.objects.create(block_name=block_name, name_of_institution=name_of_institution,
        date_of_visit=date_of_visit, name_of_lead=name_of_lead, designation=designation, issues_discussed=issues_discussed,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year,
        adult_male=adult_male, adult_female=adult_female, teachers=teachers, pri_members=pri_members, 
        services_providers=services_providers, sms_members=sms_members, other=other,
        task=task, site_id = current_site )
        dcpu_bcpu.save()
        return redirect('/cc-report/untrust/dcpu-bcpu-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/dcpu_bcpu/add_dcpu_bcpu.html', locals())



@ login_required(login_url='/login/')
def edit_dcpu_bcpu_untrust_cc_report(request, dcpu_bcpu_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 11: Edit of DCPU/BCPU engagement at community and institutional level"
    current_site = request.session.get('site_id')
    block_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__block__id')
    dcpu_bcpu = DCPU_BCPU.objects.get(id=dcpu_bcpu_id)
    block_obj = Block.objects.filter(status=1, id__in=block_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        block_name_id = data.get('block_name')
        block_name = Block.objects.get(id=block_name_id)
        name_of_institution = data.get('name_of_institution')
        date_of_visit = data.get('date_of_visit')
        name_of_lead = data.get('name_of_lead')
        designation = data.get('designation')
        issues_discussed = data.get('issues_discussed')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)


        dcpu_bcpu.block_name_id = block_name
        dcpu_bcpu.name_of_institution = name_of_institution 
        dcpu_bcpu.date_of_visit = date_of_visit 
        dcpu_bcpu.name_of_lead = name_of_lead 
        dcpu_bcpu.designation = designation 
        dcpu_bcpu.issues_discussed = issues_discussed 
        dcpu_bcpu.girls_10_14_year = girls_10_14_year 
        dcpu_bcpu.girls_15_19_year = girls_15_19_year 
        dcpu_bcpu.boys_10_14_year = boys_10_14_year 
        dcpu_bcpu.boys_15_19_year = boys_15_19_year 
        dcpu_bcpu.champions_15_19_year = champions_15_19_year 
        dcpu_bcpu.adult_male = adult_male 
        dcpu_bcpu.adult_female = adult_female 
        dcpu_bcpu.teachers = teachers 
        dcpu_bcpu.pri_members = pri_members 
        dcpu_bcpu.services_providers = services_providers 
        dcpu_bcpu.sms_members = sms_members 
        dcpu_bcpu.other = other 
        dcpu_bcpu.task_id = task 
        dcpu_bcpu.site_id =  current_site 
        dcpu_bcpu.save()
        return redirect('/cc-report/untrust/dcpu-bcpu-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/dcpu_bcpu/edit_dcpu_bcpu.html', locals())



@ login_required(login_url='/login/')
def educational_enrichment_listing_untrust_cc_report(request, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 12: Details of educational enrichment support provided"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    education_enrichment =  EducatinalEnrichmentSupportProvided.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, education_enrichment)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'cc_report/untrust/educational_enrichment/educational_enrichment_listing.html', locals())



@ login_required(login_url='/login/')
def add_educational_enrichment_untrust_cc_report(request, task_id):
    heading = "Section 12: Add of educational enrichment support provided"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    education_enrichment =  EducatinalEnrichmentSupportProvided.objects.filter(status=1, )
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        parent_guardian_name = data.get('parent_guardian_name')
        enrolment_date = data.get('enrolment_date')
        standard = data.get('standard')
        duration_of_coaching_support = data.get('duration_of_coaching_support')
        task = Task.objects.get(id=task_id)
        education_enrichment =  EducatinalEnrichmentSupportProvided.objects.create(adolescent_name=adolescent_name,
        parent_guardian_name=parent_guardian_name, standard=standard, enrolment_date=enrolment_date,
        duration_of_coaching_support=duration_of_coaching_support, task=task, site_id = current_site)
        education_enrichment.save()
        return redirect('/cc-report/untrust/educational-enrichment-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/educational_enrichment/add_educational_enrichment.html', locals())


@ login_required(login_url='/login/')
def edit_educational_enrichment_untrust_cc_report(request, educational_id, task_id):
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(status=1, id=task_id)
    heading = "Section 12: edit of educational enrichment support provided"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    education_enrichment =  EducatinalEnrichmentSupportProvided.objects.get(id=educational_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        parent_guardian_name = data.get('parent_guardian_name')
        enrolment_date = data.get('enrolment_date')
        standard = data.get('standard')
        duration_of_coaching_support = data.get('duration_of_coaching_support')
        task = Task.objects.get(id=task_id)

        education_enrichment.adolescent_name_id = adolescent_name
        education_enrichment.parent_guardian_name = parent_guardian_name
        education_enrichment.enrolment_date = enrolment_date
        education_enrichment.standard = standard
        education_enrichment.duration_of_coaching_support = duration_of_coaching_support
        education_enrichment.task_id = task
        education_enrichment.site_id =  current_site
        education_enrichment.save()
        return redirect('/cc-report/untrust/educational-enrichment-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/educational_enrichment/edit_educational_enrichment.html', locals())


#--- ---------po-report-fossil--------------


@ login_required(login_url='/login/')
def health_sessions_listing_fossil_po_report(request, task_id):
    heading = "Section 1: Details of transaction of sessions on health & nutrition"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, health_sessions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/health_sessions/health_sessions_listing.html', locals())

@ login_required(login_url='/login/')
def add_health_sessions_fossil_po_report(request, task_id):
    heading = "Section 1: Add of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    adolescent_obj =  Adolescent.objects.filter(status=1)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1).exclude(session_category='Engaging Adolescents for Gender Equality Manual')
  
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id,)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session_selected_id = data.get('fossil_ah_session_category')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        fossil_ah_session_obj =  FossilAHSession.objects.filter(fossil_ah_session_category__id = fossil_ah_session_selected_id)
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'po_report/fossil/health_sessions/add_health_sessions.html', locals())
        else:
            health_sessions = AHSession.objects.create(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
            date_of_session=date_of_session, session_day=session_day,designation_data = designations,
            age=age or None, gender=gender or None, facilitator_name = facilitator_name, task=task, site_id = current_site)
            health_sessions.save()
        return redirect('/po-report/fossil/health-sessions-listing/'+str(task_id))
    return render(request, 'po_report/fossil/health_sessions/add_health_sessions.html', locals())


@ login_required(login_url='/login/')
def edit_health_sessions_fossil_po_report(request, ahsession_id, task_id):
    heading = "Section 1: Edit of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.get(id=ahsession_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=health_sessions.adolescent_name.awc.id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    fossil_ah_session_obj =  FossilAHSession.objects.filter(status=1, fossil_ah_session_category__id=health_sessions.fossil_ah_session.fossil_ah_session_category.id)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1,).exclude(session_category='Engaging Adolescents for Gender Equality Manual')
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exclude(id=ahsession_id).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request, 'po_report/fossil/health_sessions/edit_health_sessions.html', locals())
        else:
            health_sessions.adolescent_name_id = adolescent_name
            health_sessions.fossil_ah_session_id = fossil_ah_session
            health_sessions.date_of_session = date_of_session
            health_sessions.age = age or None
            health_sessions.gender = gender or None
            health_sessions.session_day = session_day
            health_sessions.designation_data = designations
            health_sessions.facilitator_name = facilitator_name
            health_sessions.task_id = task
            health_sessions.site_id =  current_site
            health_sessions.save()
        return redirect('/po-report/fossil/health-sessions-listing/'+str(task_id))
    return render(request, 'po_report/fossil/health_sessions/edit_health_sessions.html', locals())




@ login_required(login_url='/login/')
def digital_literacy_listing_fossil_po_report(request, task_id):
    heading = "Section 2: Details of transaction of digital literacy sessions"
    awc_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')
    digital_literacy = DLSession.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, digital_literacy)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/digital_literacy/digital_literacy_listing.html', locals())


@ login_required(login_url='/login/')
def add_digital_literacy_fossil_po_report(request, task_id):
    heading = "Section 2: Add of transaction of digital literacy sessions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')
    digital_literacy = DLSession.objects.filter(status=1)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    fossil_dl_session_category_obj =  FossilDLSessionConfig.objects.filter(status=1,)
    
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_dl_session_config_id = data.get('fossil_dl_session_config')
        fossil_dl_session_config = FossilDLSessionConfig.objects.get(id=fossil_dl_session_config_id)
        session_name = data.get('session_name')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        date_of_session = data.get('date_of_session')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        session_day = data.get('session_day')
        task = Task.objects.get(id=task_id)
        if DLSession.objects.filter(adolescent_name=adolescent_name, fossil_dl_session_config=fossil_dl_session_config,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "This data already exist!!!"
            return render(request, 'po_report/fossil/digital_literacy/add_digital_literacy.html', locals())
        else:
            digital_literacy = DLSession.objects.create(adolescent_name=adolescent_name, fossil_dl_session_config=fossil_dl_session_config,
            date_of_session=date_of_session, session_name=session_name, age=age or None, gender=gender or None, facilitator_name=facilitator_name, 
            session_day=session_day, task=task, site_id = current_site)
            digital_literacy.save()
        return redirect('/po-report/fossil/digital-literacy-listing/'+str(task_id))
    return render(request, 'po_report/fossil/digital_literacy/add_digital_literacy.html', locals())



@ login_required(login_url='/login/')
def edit_digital_literacy_fossil_po_report(request, dlsession_id, task_id):
    heading = "Section 2: Edit of transaction of digital literacy sessions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_DL.objects.filter(status=1, user=request.user).values_list('awc__id')
    digital_literacy = DLSession.objects.get(id=dlsession_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=digital_literacy.adolescent_name.awc.id)
    fossil_dl_session_category_obj =  FossilDLSessionConfig.objects.filter(status=1,)

    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_dl_session_config_id = data.get('fossil_dl_session_config')
        fossil_dl_session_config = FossilDLSessionConfig.objects.get(id=fossil_dl_session_config_id)
        session_name = data.get('session_name')
        date_of_session = data.get('date_of_session')
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        task = Task.objects.get(id=task_id)
        if DLSession.objects.filter(adolescent_name=adolescent_name, fossil_dl_session_config=fossil_dl_session_config,
                                    date_of_session=date_of_session,  status=1).exclude(id=dlsession_id).exists():
            exist_error = "This data already exist!!!"
            return render(request, 'po_report/fossil/digital_literacy/edit_digital_literacy.html', locals())
        else:
            digital_literacy.adolescent_name_id = adolescent_name
            digital_literacy.fossil_dl_session_config_id = fossil_dl_session_config
            digital_literacy.date_of_session = date_of_session
            digital_literacy.age = age
            digital_literacy.gender = gender
            digital_literacy.facilitator_name = facilitator_name
            digital_literacy.session_day = session_day
            digital_literacy.session_name = session_name
            digital_literacy.task_id = task
            digital_literacy.site_id =  current_site
            digital_literacy.save()
        return redirect('/po-report/fossil/digital-literacy-listing/'+str(task_id))
    return render(request, 'po_report/fossil/digital_literacy/edit_digital_literacy.html', locals())


@ login_required(login_url='/login/')
def girls_ahwd_listing_fossil_po_report(request, task_id):
    heading = "Section 4(a): Details of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, girls_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/girls_ahwd/girls_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_girls_ahwd_fossil_po_report(request, task_id):
    heading = "Section 4(a): Add of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd = GirlsAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        tt_10_14_years=tt_10_14_years, tt_15_19_years=tt_15_19_years, counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        girls_ahwd.save()
        return redirect('/po-report/fossil/girls-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/fossil/girls_ahwd/add_girls_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_girls_ahwd_fossil_po_report(request, girls_ahwd_id, task_id):
    heading = "Section 4(a): Edit of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.get(id=girls_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd.place_of_ahwd = place_of_ahwd
        girls_ahwd.content_type = content_type
        girls_ahwd.object_id = selected_object_id
        girls_ahwd.hwc_name = hwc_name
        girls_ahwd.date_of_ahwd = date_of_ahwd
        girls_ahwd.participated_10_14_years = participated_10_14_years
        girls_ahwd.participated_15_19_years = participated_15_19_years
        girls_ahwd.bmi_10_14_years = bmi_10_14_years
        girls_ahwd.bmi_15_19_years = bmi_15_19_years
        girls_ahwd.hb_10_14_years = hb_10_14_years
        girls_ahwd.hb_15_19_years = hb_15_19_years
        girls_ahwd.tt_10_14_years = tt_10_14_years
        girls_ahwd.tt_15_19_years = tt_15_19_years
        girls_ahwd.counselling_10_14_years = counselling_10_14_years
        girls_ahwd.counselling_15_19_years = counselling_15_19_years
        girls_ahwd.referral_10_14_years = referral_10_14_years
        girls_ahwd.referral_15_19_years = referral_15_19_years
        girls_ahwd.task_id = task
        girls_ahwd.site_id =  current_site
        girls_ahwd.save()
        return redirect('/po-report/fossil/girls-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/fossil/girls_ahwd/edit_girls_ahwd.html', locals())




@ login_required(login_url='/login/')
def boys_ahwd_listing_fossil_po_report(request, task_id):
    heading = "Section 4(b): Details of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, boys_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/boys_ahwd/boys_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_boys_ahwd_fossil_po_report(request, task_id):
    heading = "Section 4(b): Add of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd = BoysAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        boys_ahwd.save()
        return redirect('/po-report/fossil/boys-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/fossil/boys_ahwd/add_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_boys_ahwd_fossil_po_report(request, boys_ahwd_id, task_id):
    heading = "Section 4(b): Edit of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.get(id=boys_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd.place_of_ahwd = place_of_ahwd
        boys_ahwd.content_type = content_type
        boys_ahwd.object_id = selected_object_id
        boys_ahwd.hwc_name = hwc_name
        boys_ahwd.date_of_ahwd = date_of_ahwd
        boys_ahwd.participated_10_14_years = participated_10_14_years
        boys_ahwd.participated_15_19_years = participated_15_19_years
        boys_ahwd.bmi_10_14_years = bmi_10_14_years
        boys_ahwd.bmi_15_19_years = bmi_15_19_years
        boys_ahwd.hb_10_14_years = hb_10_14_years
        boys_ahwd.hb_15_19_years = hb_15_19_years
        boys_ahwd.counselling_10_14_years = counselling_10_14_years
        boys_ahwd.counselling_15_19_years = counselling_15_19_years
        boys_ahwd.referral_10_14_years = referral_10_14_years
        boys_ahwd.referral_15_19_years = referral_15_19_years
        boys_ahwd.task_id = task
        boys_ahwd.site_id =  current_site
        boys_ahwd.save()
        return redirect('/po-report/fossil/boys-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/fossil/boys_ahwd/edit_boys_ahwd.html', locals())



@ login_required(login_url='/login/')
def vocation_listing_fossil_po_report(request, task_id):
    heading = "Section 3: Details of adolescent linked with vocational training & placement"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, vocation_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_vocation_fossil_po_report(request, task_id):
    heading = "Section 3: Add of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id=training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        vocation_obj = AdolescentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age or None, parent_guardian_name=parent_guardian_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered or None, placement_accepted=placement_accepted or None, type_of_employment=type_of_employment or None,
        task=task, site_id = current_site)
        vocation_obj.save()
        return redirect('/po-report/fossil/vocation-listing/'+str(task_id))
    return render(request, 'po_report/fossil/voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_vocation_fossil_po_report(request, vocation_id, task_id):
    heading = "Section 3: Edit of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.get(id=vocation_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)

        vocation_obj.adolescent_name_id = adolescent_name
        vocation_obj.date_of_registration = date_of_registration
        vocation_obj.age = age or None
        vocation_obj.parent_guardian_name = parent_guardian_name
        vocation_obj.training_subject = training_subject
        vocation_obj.training_providing_by = training_providing_by
        vocation_obj.duration_days = duration_days
        vocation_obj.training_complated = training_complated
        vocation_obj.placement_offered = placement_offered or None
        vocation_obj.placement_accepted = placement_accepted or None
        vocation_obj.type_of_employment = type_of_employment or None
        vocation_obj.task_id = task
        vocation_obj.site_id =  current_site
        vocation_obj.save()
        return redirect('/po-report/fossil/vocation-listing/'+str(task_id))
    return render(request, 'po_report/fossil/voctional_training/edit_vocation_training.html', locals())



@ login_required(login_url='/login/')
def adolescents_referred_listing_fossil_po_report(request, task_id):
    heading = "Section 5: Details of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, adolescents_referred)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/adolescent_referred/adolescent_referred_listing.html', locals())

@ login_required(login_url='/login/')
def add_adolescents_referred_fossil_po_report(request, task_id):
    heading = "Section 5: Add of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')
        
        task = Task.objects.get(id=task_id)
        adolescents_referred = AdolescentsReferred.objects.create(awc_name=awc_name, girls_referred_10_14_year=girls_referred_10_14_year, 
        girls_referred_15_19_year=girls_referred_15_19_year, boys_referred_10_14_year=boys_referred_10_14_year, boys_referred_15_19_year=boys_referred_15_19_year,
        girls_hwc_referred=girls_hwc_referred, girls_hwc_visited=girls_hwc_visited, girls_afhc_referred=girls_afhc_referred, girls_afhc_visited=girls_afhc_visited,
        girls_dh_referred=girls_dh_referred, girls_dh_visited=girls_dh_visited, boys_hwc_referred=boys_hwc_referred, boys_hwc_visited=boys_hwc_visited,
        boys_afhc_referred=boys_afhc_referred, boys_afhc_visited=boys_afhc_visited, 
        boys_dh_referred=boys_dh_referred, boys_dh_visited=boys_dh_visited, task=task, site_id = current_site)
        adolescents_referred.save()
        return redirect('/po-report/fossil/adolescent-referred-listing/'+str(task_id))
    return render(request, 'po_report/fossil/adolescent_referred/add_adolescen_referred.html', locals())


@ login_required(login_url='/login/')
def edit_adolescents_referred_fossil_po_report(request, adolescents_referred_id, task_id):
    heading = "Section 5: Edit of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.get(id=adolescents_referred_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')  
        task = Task.objects.get(id=task_id)

        adolescents_referred.awc_name_id = awc_name
        adolescents_referred.girls_referred_10_14_year = girls_referred_10_14_year
        adolescents_referred.girls_referred_15_19_year = girls_referred_15_19_year
        adolescents_referred.boys_referred_10_14_year = boys_referred_10_14_year
        adolescents_referred.boys_referred_15_19_year = boys_referred_15_19_year
        adolescents_referred.girls_hwc_referred = girls_hwc_referred
        adolescents_referred.girls_hwc_visited = girls_hwc_visited
        adolescents_referred.girls_afhc_referred = girls_afhc_referred
        adolescents_referred.girls_afhc_visited = girls_afhc_visited
        adolescents_referred.girls_dh_referred = girls_dh_referred
        adolescents_referred.girls_dh_visited = girls_dh_visited
        adolescents_referred.boys_hwc_referred = boys_hwc_referred
        adolescents_referred.boys_hwc_visited = boys_hwc_visited
        adolescents_referred.boys_afhc_referred = boys_afhc_referred
        adolescents_referred.boys_afhc_visited = boys_afhc_visited
        adolescents_referred.boys_dh_referred = boys_dh_referred
        adolescents_referred.boys_dh_visited = boys_dh_visited
        adolescents_referred.task_id = task
        adolescents_referred.site_id =  current_site
        adolescents_referred.save()
        return redirect('/po-report/fossil/adolescent-referred-listing/'+str(task_id))
    return render(request, 'po_report/fossil/adolescent_referred/edit_adolescent_referred.html', locals())


@ login_required(login_url='/login/')
def friendly_club_listing_fossil_po_report(request, task_id):
    heading = "Section 6: Details of Adolescent Friendly Club (AFC)"
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1, panchayat_name__id__in=panchayat_id, task__id = task_id)
    data = pagination_function(request, friendly_club)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/friendly_club/friendly_club_listing.html', locals())

@ login_required(login_url='/login/')
def add_friendly_club_fossil_po_report(request, task_id):
    heading = "Section 6: Add of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club = AdolescentFriendlyClub.objects.create(start_date = date_of_registration, panchayat_name=panchayat_name,
        hsc_name=hsc_name, subject=subject, facilitator=facilitator, designation=designation,
        no_of_sahiya=no_of_sahiya, no_of_aww=no_of_aww, pe_girls_10_14_year=pe_girls_10_14_year,
        pe_girls_15_19_year=pe_girls_15_19_year, pe_boys_10_14_year=pe_boys_10_14_year,
        pe_boys_15_19_year=pe_boys_15_19_year, task=task, site_id = current_site)
        friendly_club.save()
        return redirect('/po-report/fossil/friendly-club-listing/'+str(task_id))
    return render(request, 'po_report/fossil/friendly_club/add_friendly_club.html', locals())



@ login_required(login_url='/login/')
def edit_friendly_club_fossil_po_report(request, friendly_club_id, task_id):
    heading = "Section 6: Edit of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.get(id=friendly_club_id)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)
        
        friendly_club.start_date = date_of_registration
        friendly_club.panchayat_name_id = panchayat_name
        friendly_club.hsc_name = hsc_name
        friendly_club.subject = subject
        friendly_club.facilitator = facilitator
        friendly_club.designation = designation
        friendly_club.no_of_sahiya = no_of_sahiya
        friendly_club.no_of_aww = no_of_aww
        friendly_club.pe_girls_10_14_year = pe_girls_10_14_year
        friendly_club.pe_girls_15_19_year = pe_girls_15_19_year
        friendly_club.pe_boys_10_14_year = pe_boys_10_14_year
        friendly_club.pe_boys_15_19_year = pe_boys_15_19_year
        friendly_club.task_id = task
        friendly_club.site_id =  current_site
        friendly_club.save()
        return redirect('/po-report/fossil/friendly-club-listing/'+str(task_id))
    return render(request, 'po_report/fossil/friendly_club/edit_friendly_club.html', locals())


@ login_required(login_url='/login/')
def balsansad_meeting_listing_fossil_po_report(request, task_id):
    heading = "Section 7: Details of Bal Sansad meetings conducted"
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter(status=1, school_name__id__in=school_id, task__id = task_id)
    data = pagination_function(request, balsansad_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/bal_sansad_metting/bal_sansad_listing.html', locals())

@ login_required(login_url='/login/')
def add_balsansad_meeting_fossil_po_report(request, task_id):
    heading = "Section 7: Add of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter()
    school = School.objects.filter(status=1, id__in=school_id)
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        decision_taken = data.get('decision_taken')
        issues_discussion = data.get('issues_discussion')
        task = Task.objects.get(id=task_id)
        balsansad_meeting = BalSansadMeeting.objects.create(start_date = date_of_registration, school_name=school_name,
        no_of_participants=no_of_participants, decision_taken=decision_taken,
        task=task, site_id = current_site)
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/po-report/fossil/balsansad-listing/'+str(task_id))
    return render(request, 'po_report/fossil/bal_sansad_metting/add_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def edit_balsansad_meeting_fossil_po_report(request, balsansad_id, task_id):
    heading = "Section 7: Edit of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.get(id=balsansad_id)
    school = School.objects.filter(status=1, id__in=school_id)
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        decision_taken = data.get('decision_taken')
        issues_discussion = data.get('issues_discussion')
        task = Task.objects.get(id=task_id)
        balsansad_meeting.start_date = date_of_registration
        balsansad_meeting.school_name_id = school_name
        balsansad_meeting.no_of_participants = no_of_participants
        balsansad_meeting.decision_taken = decision_taken
        balsansad_meeting.task_id = task
        balsansad_meeting.site_id =  current_site
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/po-report/fossil/balsansad-listing/'+str(task_id))
    return render(request, 'po_report/fossil/bal_sansad_metting/edit_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def community_activities_listing_fossil_po_report(request, task_id):
    heading = "Section 8: Details of community engagement activities"
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1, village_name__id__in=village_id, task__id = task_id)
    data = pagination_function(request, activities)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/community_activities/community_activities_listing.html', locals())


@ login_required(login_url='/login/')
def add_community_activities_fossil_po_report(request, task_id):
    heading = "Section 8: Add of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1,)
    village =  Village.objects.filter(status=1, id__in=village_id )
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')
        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities =  CommunityEngagementActivities.objects.create(village_name=village_name, start_date = date_of_registration,
        name_of_event_activity=name_of_event_activity, organized_by=organized_by,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year, adult_male=adult_male,
        adult_female=adult_female, teachers=teachers, pri_members=pri_members, services_providers=services_providers,
        sms_members=sms_members, other=other, task=task, site_id = current_site)
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/po-report/fossil/community-activities-listing/'+str(task_id))
    return render(request, 'po_report/fossil/community_activities/add_community_activities.html', locals())


@ login_required(login_url='/login/')
def edit_community_activities_fossil_po_report(request, activities_id, task_id):
    heading = "Section 8: Edit of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.get(id=activities_id)
    village =  Village.objects.filter(status=1, id__in=village_id)
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        # theme_topic = data.get('theme_topic')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')

        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities.start_date = date_of_registration
        activities.village_name_id = village_name
        activities.name_of_event_activity = name_of_event_activity
        # activities.theme_topic = theme_topic
        activities.organized_by = organized_by
        activities.boys_10_14_year = boys_10_14_year
        activities.boys_15_19_year = boys_15_19_year
        activities.girls_10_14_year = girls_10_14_year
        activities.girls_15_19_year = girls_15_19_year
        activities.champions_15_19_year = champions_15_19_year
        activities.adult_male = adult_male
        activities.adult_female = adult_female
        activities.teachers = teachers
        activities.pri_members = pri_members
        activities.services_providers = services_providers
        activities.sms_members = sms_members
        activities.other = other
        activities.task_id = task
        activities.site_id =  current_site
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/po-report/fossil/community-activities-listing/'+str(task_id))
    return render(request, 'po_report/fossil/community_activities/edit_community_activities.html', locals())


@ login_required(login_url='/login/')
def champions_listing_fossil_po_report(request, task_id):
    heading = "Section 9: Details of exposure visits of adolescent champions"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, champions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/champions/champions_listing.html', locals())





@ login_required(login_url='/login/')
def add_champions_fossil_po_report(request, task_id):
    heading = "Section 9: Add of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions =  Champions.objects.create(awc_name=awc_name,date_of_visit=date_of_visit,  girls_10_14_year=girls_10_14_year,
        girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year, boys_15_19_year=boys_15_19_year,
        first_inst_visited=first_inst_visited,second_inst_visited=second_inst_visited or None,
        third_inst_visited=third_inst_visited or None, fourth_inst_visited=fourth_inst_visited or None,  task=task, site_id = current_site)
        champions.save()
        return redirect('/po-report/fossil/champions-listing/'+str(task_id))
    return render(request, 'po_report/fossil/champions/add_champions.html', locals())


@ login_required(login_url='/login/')
def edit_champions_fossil_po_report(request, champions_id, task_id):
    heading = "Section 9: Edit of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.get(id=champions_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        date_of_visit = data.get('date_of_visit')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions.awc_name_id = awc_name       
        champions.date_of_visit = date_of_visit 
        champions.girls_10_14_year = girls_10_14_year       
        champions.girls_15_19_year = girls_15_19_year     
        champions.boys_10_14_year = boys_10_14_year       
        champions.boys_15_19_year = boys_15_19_year       
        champions.first_inst_visited = first_inst_visited
        champions.second_inst_visited= second_inst_visited or None
        champions.third_inst_visited = third_inst_visited or None
        champions.fourth_inst_visited = fourth_inst_visited or None
        champions.task_id = task
        champions.site_id =  current_site       
        champions.save()
        return redirect('/po-report/fossil/champions-listing/'+str(task_id))
    return render(request, 'po_report/fossil/champions/edit_champions.html', locals())

@ login_required(login_url='/login/')
def reenrolled_listing_fossil_po_report(request, task_id):
    heading = "Section 10: Details of adolescent re-enrolled in schools"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, adolescent_reenrolled)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/re_enrolled/re_enrolled_listing.html', locals())

@ login_required(login_url='/login/')
def add_reenrolled_fossil_po_report(request, task_id):
    heading = "Section 10: Add of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # school = School.objects.filter(status=1, id__in = school_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled =  AdolescentRe_enrolled.objects.create(adolescent_name=adolescent_name,
        gender=gender, age=age, parent_guardian_name=parent_guardian_name, school_name=school_name, which_class_enrolled=which_class_enrolled,
        task=task, site_id = current_site)
        adolescent_reenrolled.save()
        return redirect('/po-report/fossil/reenrolled-listing/'+str(task_id))
    return render(request, 'po_report/fossil/re_enrolled/add_re_enrolled.html', locals())


@ login_required(login_url='/login/')
def edit_reenrolled_fossil_po_report(request, reenrolled_id, task_id):
    heading = "Section 10: Edit of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.get(id=reenrolled_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    # school = School.objects.filter()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled.adolescent_name_id = adolescent_name
        adolescent_reenrolled.gender = gender
        adolescent_reenrolled.age = age
        adolescent_reenrolled.parent_guardian_name = parent_guardian_name
        adolescent_reenrolled.school_name = school_name
        adolescent_reenrolled.which_class_enrolled = which_class_enrolled
        adolescent_reenrolled.task_id = task
        adolescent_reenrolled.site_id =  current_site
        adolescent_reenrolled.save()
        return redirect('/po-report/fossil/reenrolled-listing/'+str(task_id))
    return render(request, 'po_report/fossil/re_enrolled/edit_re_enrolled.html', locals())

@ login_required(login_url='/login/')
def stakeholders_listing_fossil_po_report(request, task_id):
    heading = "Section 11: Details of capacity building of different stakeholders"
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    stakeholders_obj = Stakeholder.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, stakeholders_obj)
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/stakeholders/stakeholders_listing.html', locals())


@ login_required(login_url='/login/')
def add_stakeholders_fossil_po_report(request, task_id):
    heading = "Section 11: Add of capacity building of different stakeholders"
    current_site = request.session.get('site_id')
    stakeholders_obj = Stakeholder.objects.filter()
    if request.method == 'POST':
        data = request.POST
        master_trainers_male = data.get('master_trainers_male')
        master_trainers_female = data.get('master_trainers_female')
        master_trainers_total = data.get('master_trainers_total')
        nodal_teachers_male = data.get('nodal_teachers_male')
        nodal_teachers_female = data.get('nodal_teachers_female')
        nodal_teachers_total = data.get('nodal_teachers_total')
        principals_male = data.get('principals_male')
        principals_female = data.get('principals_female')
        principals_total = data.get('principals_total')
        district_level_officials_male = data.get('district_level_officials_male')
        district_level_officials_female = data.get('district_level_officials_female')
        district_level_officials_total = data.get('district_level_officials_total')
        peer_educator_male = data.get('peer_educator_male')
        peer_educator_female = data.get('peer_educator_female')
        peer_educator_total = data.get('peer_educator_total')
        state_level_officials_male = data.get('state_level_officials_male')
        state_level_officials_female = data.get('state_level_officials_female')
        state_level_officials_total = data.get('state_level_officials_total')
        icds_awws_male = data.get('icds_awws_male')
        icds_awws_female = data.get('icds_awws_female')
        icds_awws_total = data.get('icds_awws_total')
        icds_supervisors_male = data.get('icds_supervisors_male')
        icds_supervisors_female = data.get('icds_supervisors_female')
        icds_supervisors_total = data.get('icds_supervisors_total')
        icds_peer_educator_male = data.get('icds_peer_educator_male')
        icds_peer_educator_female = data.get('icds_peer_educator_female')
        icds_peer_educator_total = data.get('icds_peer_educator_total')
        icds_child_developement_project_officers_male = data.get('icds_child_developement_project_officers_male')
        icds_child_developement_project_officers_female = data.get('icds_child_developement_project_officers_female')
        icds_child_developement_project_officers_total = data.get('icds_child_developement_project_officers_total')
        icds_district_level_officials_male = data.get('icds_district_level_officials_male')
        icds_district_level_officials_female = data.get('icds_district_level_officials_female')
        icds_district_level_officials_total = data.get('icds_district_level_officials_total')
        icds_state_level_officials_male = data.get('icds_state_level_officials_male')
        icds_state_level_officials_female = data.get('icds_state_level_officials_female')
        icds_state_level_officials_total = data.get('icds_state_level_officials_total')
        health_ashas_male = data.get('health_ashas_male')
        health_ashas_female = data.get('health_ashas_female')
        health_ashas_total = data.get('health_ashas_total')
        health_anms_male = data.get('health_anms_male')
        health_anms_female = data.get('health_anms_female')
        health_anms_total = data.get('health_anms_total')
        health_bpm_bhm_pheos_male = data.get('health_bpm_bhm_pheos_male')
        health_bpm_bhm_pheos_female = data.get('health_bpm_bhm_pheos_female')
        health_bpm_bhm_pheos_total = data.get('health_bpm_bhm_pheos_total')
        health_medical_officers_male = data.get('health_medical_officers_male')
        health_medical_officers_female = data.get('health_medical_officers_female')
        health_medical_officers_total = data.get('health_medical_officers_total')
        health_district_level_officials_male = data.get('health_district_level_officials_male')
        health_district_level_officials_female = data.get('health_district_level_officials_female')
        health_district_level_officials_total = data.get('health_district_level_officials_total')
        health_state_level_officials_male = data.get('health_state_level_officials_male')
        health_state_level_officials_female = data.get('health_state_level_officials_female')
        health_state_level_officials_total = data.get('health_state_level_officials_total')
        health_rsk_male = data.get('health_rsk_male')
        health_rsk_female = data.get('health_rsk_female')
        health_rsk_total = data.get('health_rsk_total')
        health_peer_educator_male = data.get('health_peer_educator_male')
        health_peer_educator_female = data.get('health_peer_educator_female')
        health_peer_educator_total = data.get('health_peer_educator_total')
        panchayat_ward_members_male = data.get('panchayat_ward_members_male')
        panchayat_ward_members_female = data.get('panchayat_ward_members_female')
        panchayat_ward_members_total = data.get('panchayat_ward_members_total')
        panchayat_up_mukhiya_up_Pramukh_male = data.get('panchayat_up_mukhiya_up_Pramukh_male')
        panchayat_up_mukhiya_up_Pramukh_female = data.get('panchayat_up_mukhiya_up_Pramukh_female')
        panchayat_up_mukhiya_up_Pramukh_total = data.get('panchayat_up_mukhiya_up_Pramukh_total')
        panchayat_mukhiya_Pramukh_male = data.get('panchayat_mukhiya_Pramukh_male')
        panchayat_mukhiya_Pramukh_female = data.get('panchayat_mukhiya_Pramukh_female')
        panchayat_mukhiya_Pramukh_total = data.get('panchayat_mukhiya_Pramukh_total')
        panchayat_samiti_member_male = data.get('panchayat_samiti_member_male')
        panchayat_samiti_member_female = data.get('panchayat_samiti_member_female')
        panchayat_samiti_member_total = data.get('panchayat_samiti_member_total')
        panchayat_zila_parishad_member_male = data.get('panchayat_zila_parishad_member_male')
        panchayat_zila_parishad_member_female = data.get('panchayat_zila_parishad_member_female')
        panchayat_zila_parishad_member_total = data.get('panchayat_zila_parishad_member_total')
        panchayat_vc_zila_parishad_male = data.get('panchayat_vc_zila_parishad_male')
        panchayat_vc_zila_parishad_female = data.get('panchayat_vc_zila_parishad_female')
        panchayat_vc_zila_parishad_total = data.get('panchayat_vc_zila_parishad_total')
        panchayat_chairman_zila_parishad_male = data.get('panchayat_chairman_zila_parishad_male')
        panchayat_chairman_zila_parishad_female = data.get('panchayat_chairman_zila_parishad_female')
        panchayat_chairman_zila_parishad_total = data.get('panchayat_chairman_zila_parishad_total')
        panchayat_block_level_officials_male = data.get('panchayat_block_level_officials_male')
        panchayat_block_level_officials_female = data.get('panchayat_block_level_officials_female')
        panchayat_block_level_officials_total = data.get('panchayat_block_level_officials_total')
        panchayat_district_level_officials_male = data.get('panchayat_district_level_officials_male')
        panchayat_district_level_officials_female = data.get('panchayat_district_level_officials_female')
        panchayat_district_level_officials_total = data.get('panchayat_district_level_officials_total')
        panchayat_state_level_officials_male = data.get('panchayat_state_level_officials_male')
        panchayat_state_level_officials_female = data.get('panchayat_state_level_officials_female')
        panchayat_state_level_officials_total = data.get('panchayat_state_level_officials_total')
        media_interns_male = data.get('media_interns_male')
        media_interns_female = data.get('media_interns_female')
        media_interns_total = data.get('media_interns_total')
        media_journalists_male = data.get('media_journalists_male')
        media_journalists_female = data.get('media_journalists_female')
        media_journalists_total = data.get('media_journalists_total')
        media_editors_male = data.get('media_editors_male')
        media_editors_female = data.get('media_editors_female')
        media_editors_total = data.get('media_editors_total')
        others_block_cluster_field_corrdinators_male = data.get('others_block_cluster_field_corrdinators_male')
        others_block_cluster_field_corrdinators_female = data.get('others_block_cluster_field_corrdinators_female')
        others_block_cluster_field_corrdinators_total = data.get('others_block_cluster_field_corrdinators_total')
        others_ngo_staff_corrdinators_male = data.get('others_ngo_staff_corrdinators_male')
        others_ngo_staff_corrdinators_female = data.get('others_ngo_staff_corrdinators_female')
        others_ngo_staff_corrdinators_total = data.get('others_ngo_staff_corrdinators_total')
        others_male = data.get('others_male')
        others_female = data.get('others_female')
        others_total = data.get('others_total')
        total_male = data.get('total_male')
        total_female = data.get('total_female')
        total = data.get('total')
        task = Task.objects.get(id=task_id)

        stakeholders_obj = Stakeholder.objects.create(user_name=request.user,
        master_trainers_male=master_trainers_male, master_trainers_female=master_trainers_female, master_trainers_total=master_trainers_total,
        nodal_teachers_male=nodal_teachers_male, nodal_teachers_female=nodal_teachers_female, nodal_teachers_total=nodal_teachers_total,
        principals_male=principals_male, principals_female=principals_female, principals_total=principals_total, 
        district_level_officials_male=district_level_officials_male, district_level_officials_female=district_level_officials_female, district_level_officials_total=district_level_officials_total,
        peer_educator_male=peer_educator_male, peer_educator_female=peer_educator_female, peer_educator_total=peer_educator_total,
        state_level_officials_male=state_level_officials_male, state_level_officials_female=state_level_officials_female, state_level_officials_total=state_level_officials_total,
        icds_awws_male=icds_awws_male, icds_awws_female=icds_awws_female, icds_awws_total=icds_awws_total,
        icds_supervisors_male=icds_supervisors_male, icds_supervisors_female=icds_supervisors_female, icds_supervisors_total=icds_supervisors_total,
        icds_peer_educator_male=icds_peer_educator_male, icds_peer_educator_female=icds_peer_educator_female, icds_peer_educator_total=icds_peer_educator_total,
        icds_child_developement_project_officers_male=icds_child_developement_project_officers_male, icds_child_developement_project_officers_female=icds_child_developement_project_officers_female, icds_child_developement_project_officers_total=icds_child_developement_project_officers_total,
        icds_district_level_officials_male=icds_district_level_officials_male, icds_district_level_officials_female=icds_district_level_officials_female, icds_district_level_officials_total=icds_district_level_officials_total,
        icds_state_level_officials_male=icds_state_level_officials_male, icds_state_level_officials_female=icds_state_level_officials_female, icds_state_level_officials_total=icds_state_level_officials_total,
        health_ashas_male=health_ashas_male, health_ashas_female=health_ashas_female, health_ashas_total=health_ashas_total,
        health_anms_male=health_anms_male, health_anms_female=health_anms_female, health_anms_total=health_anms_total,
        health_bpm_bhm_pheos_male=health_bpm_bhm_pheos_male, health_bpm_bhm_pheos_female=health_bpm_bhm_pheos_female, health_bpm_bhm_pheos_total=health_bpm_bhm_pheos_total,
        health_medical_officers_male=health_medical_officers_male, health_medical_officers_female=health_medical_officers_female, health_medical_officers_total=health_medical_officers_total,
        health_district_level_officials_male=health_district_level_officials_male, health_district_level_officials_female=health_district_level_officials_female, health_district_level_officials_total=health_district_level_officials_total,
        health_state_level_officials_male=health_state_level_officials_male, health_state_level_officials_female=health_state_level_officials_female, health_state_level_officials_total=health_state_level_officials_total,
        health_rsk_male=health_rsk_male, health_rsk_female=health_rsk_female, health_rsk_total=health_rsk_total,
        health_peer_educator_male=health_peer_educator_male, health_peer_educator_female=health_peer_educator_female, health_peer_educator_total=health_peer_educator_total,
        panchayat_ward_members_male=panchayat_ward_members_male, panchayat_ward_members_female=panchayat_ward_members_female, panchayat_ward_members_total=panchayat_ward_members_total,
        panchayat_up_mukhiya_up_Pramukh_male=panchayat_up_mukhiya_up_Pramukh_male, panchayat_up_mukhiya_up_Pramukh_female=panchayat_up_mukhiya_up_Pramukh_female, panchayat_up_mukhiya_up_Pramukh_total=panchayat_up_mukhiya_up_Pramukh_total,
        panchayat_mukhiya_Pramukh_male=panchayat_mukhiya_Pramukh_male, panchayat_mukhiya_Pramukh_female=panchayat_mukhiya_Pramukh_female, panchayat_mukhiya_Pramukh_total=panchayat_mukhiya_Pramukh_total,
        panchayat_samiti_member_male=panchayat_samiti_member_male, panchayat_samiti_member_female=panchayat_samiti_member_female, panchayat_samiti_member_total=panchayat_samiti_member_total,
        panchayat_zila_parishad_member_male=panchayat_zila_parishad_member_male, panchayat_zila_parishad_member_female=panchayat_zila_parishad_member_female, panchayat_zila_parishad_member_total=panchayat_zila_parishad_member_total,
        panchayat_vc_zila_parishad_male=panchayat_vc_zila_parishad_male, panchayat_vc_zila_parishad_female=panchayat_vc_zila_parishad_female, panchayat_vc_zila_parishad_total=panchayat_vc_zila_parishad_total,
        panchayat_chairman_zila_parishad_male=panchayat_chairman_zila_parishad_male, panchayat_chairman_zila_parishad_female=panchayat_chairman_zila_parishad_female, panchayat_chairman_zila_parishad_total=panchayat_chairman_zila_parishad_total,
        panchayat_block_level_officials_male=panchayat_block_level_officials_male, panchayat_block_level_officials_female=panchayat_block_level_officials_female, panchayat_block_level_officials_total=panchayat_block_level_officials_total,
        panchayat_district_level_officials_male=panchayat_district_level_officials_male, panchayat_district_level_officials_female=panchayat_district_level_officials_female, panchayat_district_level_officials_total=panchayat_district_level_officials_total,
        panchayat_state_level_officials_male=panchayat_state_level_officials_male, panchayat_state_level_officials_female=panchayat_state_level_officials_female, panchayat_state_level_officials_total=panchayat_state_level_officials_total,
        media_interns_male=media_interns_male, media_interns_female=media_interns_female, media_interns_total=media_interns_total,
        media_journalists_male=media_journalists_male, media_journalists_female=media_journalists_female, media_journalists_total=media_journalists_total,
        media_editors_male=media_editors_male, media_editors_female=media_editors_female, media_editors_total=media_editors_total,
        others_block_cluster_field_corrdinators_male=others_block_cluster_field_corrdinators_male, others_block_cluster_field_corrdinators_female=others_block_cluster_field_corrdinators_female, others_block_cluster_field_corrdinators_total=others_block_cluster_field_corrdinators_total,
        others_ngo_staff_corrdinators_male=others_ngo_staff_corrdinators_male, others_ngo_staff_corrdinators_female=others_ngo_staff_corrdinators_female, others_ngo_staff_corrdinators_total=others_ngo_staff_corrdinators_total,
        others_male=others_male, others_female=others_female, others_total=others_total,
        total_male=total_male, total_female=total_female, total=total, task=task, site_id = current_site,
        )
        stakeholders_obj.save()
        return redirect('/po-report/fossil/stakeholders-listing/'+str(task_id))
    return render(request, 'po_report/fossil/stakeholders/add_stakeholders.html', locals())


@ login_required(login_url='/login/')
def edit_stakeholders_fossil_po_report(request, stakeholders_id, task_id):
    heading = "Section 11: Edit of capacity building of different stakeholders"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    stakeholders_obj = Stakeholder.objects.get(id=stakeholders_id)
    if request.method == 'POST':
        data = request.POST
        master_trainers_male = data.get('master_trainers_male')
        master_trainers_female = data.get('master_trainers_female')
        master_trainers_total = data.get('master_trainers_total')
        nodal_teachers_male = data.get('nodal_teachers_male')
        nodal_teachers_female = data.get('nodal_teachers_female')
        nodal_teachers_total = data.get('nodal_teachers_total')
        principals_male = data.get('principals_male')
        principals_female = data.get('principals_female')
        principals_total = data.get('principals_total')
        district_level_officials_male = data.get('district_level_officials_male')
        district_level_officials_female = data.get('district_level_officials_female')
        district_level_officials_total = data.get('district_level_officials_total')
        peer_educator_male = data.get('peer_educator_male')
        peer_educator_female = data.get('peer_educator_female')
        peer_educator_total = data.get('peer_educator_total')
        state_level_officials_male = data.get('state_level_officials_male')
        state_level_officials_female = data.get('state_level_officials_female')
        state_level_officials_total = data.get('state_level_officials_total')
        icds_awws_male = data.get('icds_awws_male')
        icds_awws_female = data.get('icds_awws_female')
        icds_awws_total = data.get('icds_awws_total')
        icds_supervisors_male = data.get('icds_supervisors_male')
        icds_supervisors_female = data.get('icds_supervisors_female')
        icds_supervisors_total = data.get('icds_supervisors_total')
        icds_peer_educator_male = data.get('icds_peer_educator_male')
        icds_peer_educator_female = data.get('icds_peer_educator_female')
        icds_peer_educator_total = data.get('icds_peer_educator_total')
        icds_child_developement_project_officers_male = data.get('icds_child_developement_project_officers_male')
        icds_child_developement_project_officers_female = data.get('icds_child_developement_project_officers_female')
        icds_child_developement_project_officers_total = data.get('icds_child_developement_project_officers_total')
        icds_district_level_officials_male = data.get('icds_district_level_officials_male')
        icds_district_level_officials_female = data.get('icds_district_level_officials_female')
        icds_district_level_officials_total = data.get('icds_district_level_officials_total')
        icds_state_level_officials_male = data.get('icds_state_level_officials_male')
        icds_state_level_officials_female = data.get('icds_state_level_officials_female')
        icds_state_level_officials_total = data.get('icds_state_level_officials_total')
        health_ashas_male = data.get('health_ashas_male')
        health_ashas_female = data.get('health_ashas_female')
        health_ashas_total = data.get('health_ashas_total')
        health_anms_male = data.get('health_anms_male')
        health_anms_female = data.get('health_anms_female')
        health_anms_total = data.get('health_anms_total')
        health_bpm_bhm_pheos_male = data.get('health_bpm_bhm_pheos_male')
        health_bpm_bhm_pheos_female = data.get('health_bpm_bhm_pheos_female')
        health_bpm_bhm_pheos_total = data.get('health_bpm_bhm_pheos_total')
        health_medical_officers_male = data.get('health_medical_officers_male')
        health_medical_officers_female = data.get('health_medical_officers_female')
        health_medical_officers_total = data.get('health_medical_officers_total')
        health_district_level_officials_male = data.get('health_district_level_officials_male')
        health_district_level_officials_female = data.get('health_district_level_officials_female')
        health_district_level_officials_total = data.get('health_district_level_officials_total')
        health_state_level_officials_male = data.get('health_state_level_officials_male')
        health_state_level_officials_female = data.get('health_state_level_officials_female')
        health_state_level_officials_total = data.get('health_state_level_officials_total')
        health_rsk_male = data.get('health_rsk_male')
        health_rsk_female = data.get('health_rsk_female')
        health_rsk_total = data.get('health_rsk_total')
        health_peer_educator_male = data.get('health_peer_educator_male')
        health_peer_educator_female = data.get('health_peer_educator_female')
        health_peer_educator_total = data.get('health_peer_educator_total')
        panchayat_ward_members_male = data.get('panchayat_ward_members_male')
        panchayat_ward_members_female = data.get('panchayat_ward_members_female')
        panchayat_ward_members_total = data.get('panchayat_ward_members_total')
        panchayat_up_mukhiya_up_Pramukh_male = data.get('panchayat_up_mukhiya_up_Pramukh_male')
        panchayat_up_mukhiya_up_Pramukh_female = data.get('panchayat_up_mukhiya_up_Pramukh_female')
        panchayat_up_mukhiya_up_Pramukh_total = data.get('panchayat_up_mukhiya_up_Pramukh_total')
        panchayat_mukhiya_Pramukh_male = data.get('panchayat_mukhiya_Pramukh_male')
        panchayat_mukhiya_Pramukh_female = data.get('panchayat_mukhiya_Pramukh_female')
        panchayat_mukhiya_Pramukh_total = data.get('panchayat_mukhiya_Pramukh_total')
        panchayat_samiti_member_male = data.get('panchayat_samiti_member_male')
        panchayat_samiti_member_female = data.get('panchayat_samiti_member_female')
        panchayat_samiti_member_total = data.get('panchayat_samiti_member_total')
        panchayat_zila_parishad_member_male = data.get('panchayat_zila_parishad_member_male')
        panchayat_zila_parishad_member_female = data.get('panchayat_zila_parishad_member_female')
        panchayat_zila_parishad_member_total = data.get('panchayat_zila_parishad_member_total')
        panchayat_vc_zila_parishad_male = data.get('panchayat_vc_zila_parishad_male')
        panchayat_vc_zila_parishad_female = data.get('panchayat_vc_zila_parishad_female')
        panchayat_vc_zila_parishad_total = data.get('panchayat_vc_zila_parishad_total')
        panchayat_chairman_zila_parishad_male = data.get('panchayat_chairman_zila_parishad_male')
        panchayat_chairman_zila_parishad_female = data.get('panchayat_chairman_zila_parishad_female')
        panchayat_chairman_zila_parishad_total = data.get('panchayat_chairman_zila_parishad_total')
        panchayat_block_level_officials_male = data.get('panchayat_block_level_officials_male')
        panchayat_block_level_officials_female = data.get('panchayat_block_level_officials_female')
        panchayat_block_level_officials_total = data.get('panchayat_block_level_officials_total')
        panchayat_district_level_officials_male = data.get('panchayat_district_level_officials_male')
        panchayat_district_level_officials_female = data.get('panchayat_district_level_officials_female')
        panchayat_district_level_officials_total = data.get('panchayat_district_level_officials_total')
        panchayat_state_level_officials_male = data.get('panchayat_state_level_officials_male')
        panchayat_state_level_officials_female = data.get('panchayat_state_level_officials_female')
        panchayat_state_level_officials_total = data.get('panchayat_state_level_officials_total')
        media_interns_male = data.get('media_interns_male')
        media_interns_female = data.get('media_interns_female')
        media_interns_total = data.get('media_interns_total')
        media_journalists_male = data.get('media_journalists_male')
        media_journalists_female = data.get('media_journalists_female')
        media_journalists_total = data.get('media_journalists_total')
        media_editors_male = data.get('media_editors_male')
        media_editors_female = data.get('media_editors_female')
        media_editors_total = data.get('media_editors_total')
        others_block_cluster_field_corrdinators_male = data.get('others_block_cluster_field_corrdinators_male')
        others_block_cluster_field_corrdinators_female = data.get('others_block_cluster_field_corrdinators_female')
        others_block_cluster_field_corrdinators_total = data.get('others_block_cluster_field_corrdinators_total')
        others_ngo_staff_corrdinators_male = data.get('others_ngo_staff_corrdinators_male')
        others_ngo_staff_corrdinators_female = data.get('others_ngo_staff_corrdinators_female')
        others_ngo_staff_corrdinators_total = data.get('others_ngo_staff_corrdinators_total')
        others_male = data.get('others_male')
        others_female = data.get('others_female')
        others_total = data.get('others_total')
        total_male = data.get('total_male')
        total_female = data.get('total_female')
        total = data.get('total')
        task = Task.objects.get(id=task_id)

        stakeholders_obj.user_name = request.user
        stakeholders_obj.master_trainers_male = master_trainers_male
        stakeholders_obj.master_trainers_female = master_trainers_female
        stakeholders_obj.master_trainers_total = master_trainers_total
        stakeholders_obj.nodal_teachers_male = nodal_teachers_male
        stakeholders_obj.nodal_teachers_female = nodal_teachers_female
        stakeholders_obj.nodal_teachers_total = nodal_teachers_total
        stakeholders_obj.principals_male = principals_male
        stakeholders_obj.principals_female = principals_female
        stakeholders_obj.principals_total = principals_total
        stakeholders_obj.district_level_officials_male = district_level_officials_male
        stakeholders_obj.district_level_officials_female = district_level_officials_female
        stakeholders_obj.district_level_officials_total = district_level_officials_total
        stakeholders_obj.peer_educator_male = peer_educator_male
        stakeholders_obj.peer_educator_female = peer_educator_female
        stakeholders_obj.peer_educator_total = peer_educator_total
        stakeholders_obj.state_level_officials_male = state_level_officials_male
        stakeholders_obj.state_level_officials_female = state_level_officials_female
        stakeholders_obj.state_level_officials_total = state_level_officials_total
        stakeholders_obj.icds_awws_male = icds_awws_male
        stakeholders_obj.icds_awws_female = icds_awws_female
        stakeholders_obj.icds_awws_total = icds_awws_total
        stakeholders_obj.icds_supervisors_male = icds_supervisors_male
        stakeholders_obj.icds_supervisors_female = icds_supervisors_female
        stakeholders_obj.icds_supervisors_total = icds_supervisors_total
        stakeholders_obj.icds_peer_educator_male = icds_peer_educator_male
        stakeholders_obj.icds_peer_educator_female = icds_peer_educator_female
        stakeholders_obj.icds_peer_educator_total = icds_peer_educator_total
        stakeholders_obj.icds_child_developement_project_officers_male = icds_child_developement_project_officers_male
        stakeholders_obj.icds_child_developement_project_officers_female = icds_child_developement_project_officers_female
        stakeholders_obj.icds_child_developement_project_officers_total = icds_child_developement_project_officers_total
        stakeholders_obj.icds_district_level_officials_male = icds_district_level_officials_male
        stakeholders_obj.icds_district_level_officials_female = icds_district_level_officials_female
        stakeholders_obj.icds_district_level_officials_total = icds_district_level_officials_total
        stakeholders_obj.icds_state_level_officials_male = icds_state_level_officials_male
        stakeholders_obj.icds_state_level_officials_female = icds_state_level_officials_female
        stakeholders_obj.icds_state_level_officials_total = icds_state_level_officials_total
        stakeholders_obj.health_ashas_male = health_ashas_male
        stakeholders_obj.health_ashas_female = health_ashas_female
        stakeholders_obj.health_ashas_total = health_ashas_total
        stakeholders_obj.health_anms_male = health_anms_male
        stakeholders_obj.health_anms_female = health_anms_female
        stakeholders_obj.health_anms_total = health_anms_total
        stakeholders_obj.health_bpm_bhm_pheos_male = health_bpm_bhm_pheos_male
        stakeholders_obj.health_bpm_bhm_pheos_female = health_bpm_bhm_pheos_female
        stakeholders_obj.health_bpm_bhm_pheos_total = health_bpm_bhm_pheos_total
        stakeholders_obj.health_medical_officers_male = health_medical_officers_male
        stakeholders_obj.health_medical_officers_female = health_medical_officers_female
        stakeholders_obj.health_medical_officers_total = health_medical_officers_total
        stakeholders_obj.health_district_level_officials_male = health_district_level_officials_male
        stakeholders_obj.health_district_level_officials_female = health_district_level_officials_female
        stakeholders_obj.health_district_level_officials_total = health_district_level_officials_total
        stakeholders_obj.health_state_level_officials_male = health_state_level_officials_male
        stakeholders_obj.health_state_level_officials_female = health_state_level_officials_female
        stakeholders_obj.health_state_level_officials_total = health_state_level_officials_total
        stakeholders_obj.health_rsk_male = health_rsk_male
        stakeholders_obj.health_rsk_female = health_rsk_female
        stakeholders_obj.health_rsk_total = health_rsk_total
        stakeholders_obj.health_peer_educator_male = health_peer_educator_male
        stakeholders_obj.health_peer_educator_female = health_peer_educator_female
        stakeholders_obj.health_peer_educator_total = health_peer_educator_total
        stakeholders_obj.panchayat_ward_members_male = panchayat_ward_members_male
        stakeholders_obj.panchayat_ward_members_female = panchayat_ward_members_female
        stakeholders_obj.panchayat_ward_members_total = panchayat_ward_members_total
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_male = panchayat_up_mukhiya_up_Pramukh_male
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_female = panchayat_up_mukhiya_up_Pramukh_female
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_total = panchayat_up_mukhiya_up_Pramukh_total
        stakeholders_obj.panchayat_mukhiya_Pramukh_male = panchayat_mukhiya_Pramukh_male
        stakeholders_obj.panchayat_mukhiya_Pramukh_female = panchayat_mukhiya_Pramukh_female
        stakeholders_obj.panchayat_mukhiya_Pramukh_total = panchayat_mukhiya_Pramukh_total
        stakeholders_obj.panchayat_samiti_member_male = panchayat_samiti_member_male
        stakeholders_obj.panchayat_samiti_member_female = panchayat_samiti_member_female
        stakeholders_obj.panchayat_samiti_member_male = panchayat_samiti_member_total
        stakeholders_obj.panchayat_zila_parishad_member_male = panchayat_zila_parishad_member_male
        stakeholders_obj.panchayat_zila_parishad_member_female = panchayat_zila_parishad_member_female
        stakeholders_obj.panchayat_zila_parishad_member_total = panchayat_zila_parishad_member_total
        stakeholders_obj.panchayat_vc_zila_parishad_male = panchayat_vc_zila_parishad_male
        stakeholders_obj.panchayat_vc_zila_parishad_female = panchayat_vc_zila_parishad_female
        stakeholders_obj.panchayat_vc_zila_parishad_total = panchayat_vc_zila_parishad_total
        stakeholders_obj.panchayat_chairman_zila_parishad_male = panchayat_chairman_zila_parishad_male
        stakeholders_obj.panchayat_chairman_zila_parishad_female = panchayat_chairman_zila_parishad_female
        stakeholders_obj.panchayat_chairman_zila_parishad_total = panchayat_chairman_zila_parishad_total
        stakeholders_obj.panchayat_block_level_officials_male = panchayat_block_level_officials_male
        stakeholders_obj.panchayat_block_level_officials_female = panchayat_block_level_officials_female
        stakeholders_obj.panchayat_block_level_officials_total = panchayat_block_level_officials_total
        stakeholders_obj.panchayat_district_level_officials_male = panchayat_district_level_officials_male
        stakeholders_obj.panchayat_district_level_officials_female = panchayat_district_level_officials_female
        stakeholders_obj.panchayat_district_level_officials_total = panchayat_district_level_officials_total
        stakeholders_obj.panchayat_state_level_officials_male = panchayat_state_level_officials_male
        stakeholders_obj.panchayat_state_level_officials_female = panchayat_state_level_officials_female
        stakeholders_obj.panchayat_state_level_officials_total = panchayat_state_level_officials_total
        stakeholders_obj.media_interns_male = media_interns_male
        stakeholders_obj.media_interns_female = media_interns_female
        stakeholders_obj.media_interns_total = media_interns_total
        stakeholders_obj.media_journalists_male = media_journalists_male
        stakeholders_obj.media_journalists_female = media_journalists_female
        stakeholders_obj.media_journalists_total = media_journalists_total
        stakeholders_obj.media_editors_male = media_editors_male
        stakeholders_obj.media_editors_female = media_editors_female
        stakeholders_obj.media_editors_total = media_editors_total
        stakeholders_obj.others_block_cluster_field_corrdinators_male = others_block_cluster_field_corrdinators_male
        stakeholders_obj.others_block_cluster_field_corrdinators_female = others_block_cluster_field_corrdinators_female
        stakeholders_obj.others_block_cluster_field_corrdinators_total = others_block_cluster_field_corrdinators_total
        stakeholders_obj.others_ngo_staff_corrdinators_male = others_ngo_staff_corrdinators_male
        stakeholders_obj.others_ngo_staff_corrdinators_female = others_ngo_staff_corrdinators_female
        stakeholders_obj.others_ngo_staff_corrdinators_total = others_ngo_staff_corrdinators_total
        stakeholders_obj.others_male = others_male
        stakeholders_obj.others_female = others_female
        stakeholders_obj.others_total = others_total
        stakeholders_obj.total_male = total_male
        stakeholders_obj.total_female = total_female
        stakeholders_obj.total = total
        stakeholders_obj.task_id = task
        stakeholders_obj.site_id =  current_site
        stakeholders_obj.save()
        return redirect('/po-report/fossil/stakeholders-listing/'+str(task_id))
    return render(request, 'po_report/fossil/stakeholders/edit_stakeholders.html', locals())


@ login_required(login_url='/login/')
def sessions_monitoring_listing_fossil_po_report(request, task_id):
    heading = "Section 12: Details of sessions monitoring and handholding support at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    village_id =CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, sessions_monitoring)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/sessions_monitoring/sessions_monitoring_listing.html', locals())


@ login_required(login_url='/login/')
def add_sessions_monitoring_fossil_po_report(request, task_id):
    heading = "Section 12: Add of sessions monitoring and handholding support at block level"
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
      
        sessions = data.getlist('session_attended')
        session_attended = ", ".join(sessions)
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        sessions_monitoring = SessionMonitoring.objects.create(name_of_visited=name_of_visited, session_attended=session_attended,
        date=date,
        observation=observation, recommendation=recommendation, task=task, site_id = current_site)
        
        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            sessions_monitoring.content_type=content_type
            sessions_monitoring.object_id=selected_object_id
        
        if name_of_visited in ['4','5']:
            sessions_monitoring.name_of_place_visited = selected_field_other

        sessions_monitoring.save()
        return redirect('/po-report/fossil/sessions-monitoring-listing/'+str(task_id))
    return render(request, 'po_report/fossil/sessions_monitoring/add_sessions_monitoring.html', locals())


@ login_required(login_url='/login/')
def edit_sessions_monitoring_fossil_po_report(request, sessions_id, task_id):
    heading = "Section 12: Edit of sessions monitoring and handholding support at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.get(id=sessions_id)
    session_choice = sessions_monitoring.session_attended.split(', ')
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        selected_field_other = data.get('selected_field_other')
        name_of_visited = data.get('name_of_visited')
        
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        content_type = ContentType.objects.get(model=content_type_model)
        date = data.get('date')
        sessions = data.getlist('session_attended')
        session_attended = ", ".join(sessions)
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        sessions_monitoring.name_of_visited = name_of_visited

        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            sessions_monitoring.content_type=content_type
            sessions_monitoring.object_id=selected_object_id

        if name_of_visited in ['4','5']:
            sessions_monitoring.name_of_place_visited = selected_field_other

        sessions_monitoring.date = date
        sessions_monitoring.session_attended = session_attended
        sessions_monitoring.observation = observation
        sessions_monitoring.recommendation = recommendation
        sessions_monitoring.task_id = task
        sessions_monitoring.site_id =  current_site
        sessions_monitoring.save()
        return redirect('/po-report/fossil/sessions-monitoring-listing/'+str(task_id))
    return render(request, 'po_report/fossil/sessions_monitoring/edit_sessions_monitoring.html', locals())



@ login_required(login_url='/login/')
def facility_visits_listing_fossil_po_report(request, task_id):
    heading = "Section 13: Details of events & facility visits at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    village_id =CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    facility_visits = Events.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, facility_visits)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/facility_visits/facility_visits_listing.html', locals())


@ login_required(login_url='/login/')
def add_facility_visits_fossil_po_report(request, task_id):
    heading = "Section 13: Add of events & facility visits at block level"
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    facility_visits = Events.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
        purpose_visited = data.get('purpose_visited')
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        
        facility_visits = Events.objects.create(name_of_visited=name_of_visited, purpose_visited=purpose_visited,
        date=date,
        observation=observation, recommendation=recommendation, task=task, site_id = current_site)
        
        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            facility_visits.content_type=content_type
            facility_visits.object_id=selected_object_id

        if name_of_visited in ['4','5','6','7','8','9','10','11']:
            facility_visits.name_of_place_visited = selected_field_other

        facility_visits.save()
        return redirect('/po-report/fossil/facility-visits-listing/'+str(task_id))
    return render(request, 'po_report/fossil/facility_visits/add_facility_visits.html', locals())


@ login_required(login_url='/login/')
def edit_facility_visits_fossil_po_report(request, facility_id, task_id):
    heading = "Section 13: Edit of events & facility visits at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    facility_visits = Events.objects.get(id=facility_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
        purpose_visited = data.get('purpose_visited')
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        facility_visits.name_of_visited = name_of_visited

        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            facility_visits.content_type = content_type
            facility_visits.object_id = selected_object_id
        
        if name_of_visited in ['4','5','6','7','8','9','10','11',]:
            facility_visits.name_of_place_visited = selected_field_other

        facility_visits.date = date
        facility_visits.purpose_visited = purpose_visited
        facility_visits.observation = observation
        facility_visits.recommendation = recommendation
        facility_visits.task_id = task
        facility_visits.site_id =  current_site
        facility_visits.save()
        return redirect('/po-report/fossil/facility-visits-listing/'+str(task_id))
    return render(request, 'po_report/fossil/facility_visits/edit_facility_visits.html', locals())



@ login_required(login_url='/login/')
def followup_liaision_listing_fossil_po_report(request, task_id):
    heading = "Section 15: Details of one to one (Follow up/ Liaison) meetings at district & Block Level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    followup_liaision = FollowUP_LiaisionMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, followup_liaision)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/followup_liaision/followup_liaision_listing.html', locals())


@ login_required(login_url='/login/')
def add_followup_liaision_fossil_po_report(request, task_id):
    heading = "Section 15: Add of one to one (Follow up/ Liaison) meetings at district & Block Level"
    current_site = request.session.get('site_id')
    followup_liaision = FollowUP_LiaisionMeeting.objects.filter()
    meeting_obj = MasterLookUp.objects.filter(parent__slug = 'meeting-with-designation')
    if request.method == 'POST':
        data = request.POST
        date = data.get('date')
        district_block_level = data.get('district_block_level')
        meeting_id = data.get('meeting')
        meeting = MasterLookUp.objects.get(id = meeting_id)
        departments = data.get('departments')
        point_of_discussion = data.get('point_of_discussion')
        outcome = data.get('outcome')
        decision_taken = data.get('decision_taken')
        remarks = data.get('remarks')
        task = Task.objects.get(id=task_id)

        followup_liaision = FollowUP_LiaisionMeeting.objects.create(user_name=request.user, date=date,
        district_block_level=district_block_level, meeting_name=meeting, departments=departments, point_of_discussion=point_of_discussion,
        outcome=outcome, decision_taken=decision_taken, remarks=remarks, site_id = current_site, task=task)
        followup_liaision.save()
        return redirect('/po-report/fossil/followup-liaision-listing/'+str(task_id))
    return render(request, 'po_report/fossil/followup_liaision/add_followup_liaision.html', locals())


@ login_required(login_url='/login/')
def edit_followup_liaision_fossil_po_report(request, followup_liaision_id, task_id):
    heading = "Section 15: Edit of one to one (Follow up/ Liaison) meetings at district & Block Level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    followup_liaision = FollowUP_LiaisionMeeting.objects.get(id=followup_liaision_id)
    meeting_obj = MasterLookUp.objects.filter(parent__slug = 'meeting-with-designation')
    if request.method == 'POST':
        data = request.POST
        date = data.get('date')
        district_block_level = data.get('district_block_level')
        meeting_id = data.get('meeting')
        meeting = MasterLookUp.objects.get(id = meeting_id)
        departments = data.get('departments')
        point_of_discussion = data.get('point_of_discussion')
        outcome = data.get('outcome')
        decision_taken = data.get('decision_taken')
        remarks = data.get('remarks')
        task = Task.objects.get(id=task_id)


        followup_liaision.user_name = request.user
        followup_liaision.date = date
        followup_liaision.district_block_level = district_block_level
        followup_liaision.meeting_name = meeting
        followup_liaision.departments = departments
        followup_liaision.point_of_discussion = point_of_discussion
        followup_liaision.outcome = outcome
        followup_liaision.decision_taken = decision_taken
        followup_liaision.remarks = remarks
        followup_liaision.task_id = task
        followup_liaision.site_id =  current_site
        followup_liaision.save()
        return redirect('/po-report/fossil/followup-liaision-listing/'+str(task_id))
    return render(request, 'po_report/fossil/followup_liaision/edit_followup_liaision.html', locals())



@ login_required(login_url='/login/')
def participating_meeting_listing_fossil_po_report(request, task_id):
    heading = "Section 14: Details of participating in meetings at district and block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    participating_meeting = ParticipatingMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, participating_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/participating_meeting/participating_meeting_listing.html', locals())

@ login_required(login_url='/login/')
def add_participating_meeting_fossil_po_report(request, task_id):
    heading = "Section 14: Add of participating in meetings at district and block level"
    current_site = request.session.get('site_id')
    participating_meeting = ParticipatingMeeting.objects.filter()
    if request.method == 'POST':
        data = request.POST
        type_of_meeting = data.get('type_of_meeting')
        department = data.get('department')
        district_block_level = data.get('district_block_level')
        point_of_discussion = data.get('point_of_discussion')
        districit_level_officials = data.get('districit_level_officials')
        block_level = data.get('block_level')
        cluster_level = data.get('cluster_level')
        no_of_pri = data.get('no_of_pri')
        no_of_others = data.get('no_of_others')
        date = data.get('date')
        task = Task.objects.get(id=task_id)
        participating_meeting = ParticipatingMeeting.objects.create(user_name=request.user, type_of_meeting=type_of_meeting,
        department=department, point_of_discussion=point_of_discussion, districit_level_officials=districit_level_officials,
        block_level=block_level, cluster_level=cluster_level, no_of_pri=no_of_pri, no_of_others=no_of_others,
        district_block_level=district_block_level, date=date, task=task, site_id = current_site,)
        participating_meeting.save()
        return redirect('/po-report/fossil/participating-meeting-listing/'+str(task_id))
    return render(request, 'po_report/fossil/participating_meeting/add_participating_meeting.html', locals())

@ login_required(login_url='/login/')
def edit_participating_meeting_fossil_po_report(request, participating_id, task_id):
    heading = "Section 14: Edit of participating in meetings at district and block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    participating_meeting = ParticipatingMeeting.objects.get(id=participating_id)
    if request.method == 'POST':
        data = request.POST
        type_of_meeting = data.get('type_of_meeting')
        department = data.get('department')
        district_block_level = data.get('district_block_level')
        point_of_discussion = data.get('point_of_discussion')
        districit_level_officials = data.get('districit_level_officials')
        block_level = data.get('block_level')
        cluster_level = data.get('cluster_level')
        no_of_pri = data.get('no_of_pri')
        no_of_others = data.get('no_of_others')
        date = data.get('date')
        task = Task.objects.get(id=task_id)

        participating_meeting.user_name_id = request.user
        participating_meeting.type_of_meeting = type_of_meeting
        participating_meeting.district_block_level = district_block_level
        participating_meeting.department = department
        participating_meeting.point_of_discussion = point_of_discussion
        participating_meeting.districit_level_officials = districit_level_officials
        participating_meeting.block_level = block_level
        participating_meeting.cluster_level = cluster_level
        participating_meeting.no_of_pri = no_of_pri
        participating_meeting.no_of_others = no_of_others
        participating_meeting.date = date
        participating_meeting.task_id = task
        participating_meeting.site_id =  current_site
        participating_meeting.save()
        return redirect('/po-report/fossil/participating-meeting-listing/'+str(task_id))
    return render(request, 'po_report/fossil/participating_meeting/edit_participating_meeting.html', locals())

@ login_required(login_url='/login/')
def faced_related_listing_fossil_po_report(request, task_id):
    heading = "Section 16: Details of faced related"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    faced_related = FacedRelatedOperation.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, faced_related)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/fossil/faced_related/faced_related_listing.html', locals())

@ login_required(login_url='/login/')
def add_faced_related_fossil_po_report(request, task_id):
    heading = "Section 16: Add of faced related"
    current_site = request.session.get('site_id')
    faced_related = FacedRelatedOperation.objects.filter()
    if request.method == 'POST':
        data = request.POST
        challenges = data.get('challenges')
        proposed_solution = data.get('proposed_solution')
        task = Task.objects.get(id=task_id)
        if FacedRelatedOperation.objects.filter(Q(challenges__isnull=challenges) & Q(proposed_solution__isnull=proposed_solution)).exists():
            return redirect('/po-report/fossil/faced-related-listing/'+str(task_id))
        else:
            faced_related = FacedRelatedOperation.objects.create(user_name=request.user, challenges=challenges,
            proposed_solution=proposed_solution, task=task, site_id = current_site)
            faced_related.save()
        return redirect('/po-report/fossil/faced-related-listing/'+str(task_id))
    return render(request, 'po_report/fossil/faced_related/add_faced_related.html', locals())


@ login_required(login_url='/login/')
def edit_faced_related_fossil_po_report(request, faced_related_id, task_id):
    heading = "Section 16: Edit of faced related"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    faced_related = FacedRelatedOperation.objects.get(id=faced_related_id)
    if request.method == 'POST':
        data = request.POST
        challenges = data.get('challenges')
        proposed_solution = data.get('proposed_solution')
        task = Task.objects.get(id=task_id)

        if FacedRelatedOperation.objects.filter(Q(challenges__isnull=challenges) & Q(proposed_solution__isnull=proposed_solution)).exists():
            return redirect('/po-report/fossil/faced-related-listing/'+str(task_id))
        else:
            faced_related.user_name_id = request.user
            faced_related.challenges = challenges
            faced_related.proposed_solution = proposed_solution
            faced_related.task_id = task
            faced_related.site_id =  current_site
            faced_related.save()
        return redirect('/po-report/fossil/faced-related-listing/'+str(task_id))
    return render(request, 'po_report/fossil/faced_related/edit_faced_related.html', locals())


#--- ---------po-report-rnp--------------

@ login_required(login_url='/login/')
def health_sessions_listing_rnp_po_report(request, task_id):
    heading = "Section 1: Details of transaction of sessions on health & nutrition"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, health_sessions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/health_sessions/health_sessions_listing.html', locals())

@ login_required(login_url='/login/')
def add_health_sessions_rnp_po_report(request, task_id):
    heading = "Section 1: Add of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    adolescent_obj =  Adolescent.objects.filter()
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1)
  
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id,)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session_selected_id = data.get('fossil_ah_session_category')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        fossil_ah_session_obj =  FossilAHSession.objects.filter(fossil_ah_session_category__id = fossil_ah_session_selected_id)
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'po_report/rnp/health_sessions/add_health_sessions.html', locals())
        else:
            health_sessions = AHSession.objects.create(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
            date_of_session=date_of_session, session_day=session_day,designation_data = designations,
            age=age, gender=gender, facilitator_name = facilitator_name, task=task, site_id = current_site)
            health_sessions.save()
        return redirect('/po-report/rnp/health-sessions-listing/'+str(task_id))
    return render(request, 'po_report/rnp/health_sessions/add_health_sessions.html', locals())


@ login_required(login_url='/login/')
def edit_health_sessions_rnp_po_report(request, ahsession_id, task_id):
    heading = "Section 1: Edit of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.get(id=ahsession_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=health_sessions.adolescent_name.awc.id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    fossil_ah_session_obj =  FossilAHSession.objects.filter(status=1, fossil_ah_session_category__id=health_sessions.fossil_ah_session.fossil_ah_session_category.id)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1,)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exclude(id=ahsession_id).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request, 'po_report/rnp/health_sessions/edit_health_sessions.html', locals())
        else:
            health_sessions.adolescent_name_id = adolescent_name
            health_sessions.fossil_ah_session_id = fossil_ah_session
            health_sessions.age = age
            health_sessions.gender = gender
            health_sessions.date_of_session = date_of_session
            health_sessions.session_day = session_day
            health_sessions.designation_data = designations
            health_sessions.facilitator_name = facilitator_name
            health_sessions.task_id = task
            health_sessions.site_id =  current_site
            health_sessions.save()
        return redirect('/po-report/rnp/health-sessions-listing/'+str(task_id))
    return render(request, 'po_report/rnp/health_sessions/edit_health_sessions.html', locals())


@ login_required(login_url='/login/')
def girls_ahwd_listing_rnp_po_report(request, task_id):
    heading = "Section 3(a): Details of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, girls_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/girls_ahwd/girls_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_girls_ahwd_rnp_po_report(request, task_id):
    heading = "Section 3(a): Add of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')

        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd = GirlsAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        tt_10_14_years=tt_10_14_years, tt_15_19_years=tt_15_19_years, counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        girls_ahwd.save()
        return redirect('/po-report/rnp/girls-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/rnp/girls_ahwd/add_girls_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_girls_ahwd_rnp_po_report(request, girls_ahwd_id, task_id):
    heading = "Section 3(a): Edit of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.get(id=girls_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd.place_of_ahwd = place_of_ahwd
        girls_ahwd.content_type = content_type
        girls_ahwd.object_id = selected_object_id
        girls_ahwd.hwc_name = hwc_name
        girls_ahwd.date_of_ahwd = date_of_ahwd
        girls_ahwd.participated_10_14_years = participated_10_14_years
        girls_ahwd.participated_15_19_years = participated_15_19_years
        girls_ahwd.bmi_10_14_years = bmi_10_14_years
        girls_ahwd.bmi_15_19_years = bmi_15_19_years
        girls_ahwd.hb_10_14_years = hb_10_14_years
        girls_ahwd.hb_15_19_years = hb_15_19_years
        girls_ahwd.tt_10_14_years = tt_10_14_years
        girls_ahwd.tt_15_19_years = tt_15_19_years
        girls_ahwd.counselling_10_14_years = counselling_10_14_years
        girls_ahwd.counselling_15_19_years = counselling_15_19_years
        girls_ahwd.referral_10_14_years = referral_10_14_years
        girls_ahwd.referral_15_19_years = referral_15_19_years
        girls_ahwd.task_id = task
        girls_ahwd.site_id =  current_site
        girls_ahwd.save()
        return redirect('/po-report/rnp/girls-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/rnp/girls_ahwd/edit_girls_ahwd.html', locals())




@ login_required(login_url='/login/')
def boys_ahwd_listing_rnp_po_report(request, task_id):
    heading = "Section 3(b): Details of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, boys_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/boys_ahwd/boys_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_boys_ahwd_rnp_po_report(request, task_id):
    heading = "Section 3(b): Add of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd = BoysAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        boys_ahwd.save()
        return redirect('/po-report/rnp/boys-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/rnp/boys_ahwd/add_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_boys_ahwd_rnp_po_report(request, boys_ahwd_id, task_id):
    heading = "Section 3(b): Edit of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.get(id=boys_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd.place_of_ahwd = place_of_ahwd
        boys_ahwd.content_type = content_type
        boys_ahwd.object_id = selected_object_id
        boys_ahwd.hwc_name = hwc_name
        boys_ahwd.date_of_ahwd = date_of_ahwd
        boys_ahwd.participated_10_14_years = participated_10_14_years
        boys_ahwd.participated_15_19_years = participated_15_19_years
        boys_ahwd.bmi_10_14_years = bmi_10_14_years
        boys_ahwd.bmi_15_19_years = bmi_15_19_years
        boys_ahwd.hb_10_14_years = hb_10_14_years
        boys_ahwd.hb_15_19_years = hb_15_19_years
        boys_ahwd.counselling_10_14_years = counselling_10_14_years
        boys_ahwd.counselling_15_19_years = counselling_15_19_years
        boys_ahwd.referral_10_14_years = referral_10_14_years
        boys_ahwd.referral_15_19_years = referral_15_19_years
        boys_ahwd.task_id = task
        boys_ahwd.site_id =  current_site
        boys_ahwd.save()
        return redirect('/po-report/rnp/boys-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/rnp/boys_ahwd/edit_boys_ahwd.html', locals())



@ login_required(login_url='/login/')
def vocation_listing_rnp_po_report(request, task_id):
    heading = "Section 2: Details of adolescent boys linked with vocational training & placement"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, vocation_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_vocation_rnp_po_report(request, task_id):
    heading = "Section 2: Add of adolescent boys linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id=training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        vocation_obj = AdolescentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age or None, parent_guardian_name=parent_guardian_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered or None, placement_accepted=placement_accepted or None, type_of_employment=type_of_employment or None,
        task=task, site_id = current_site)

        vocation_obj.save()
        return redirect('/po-report/rnp/vocation-listing/'+str(task_id))
    return render(request, 'po_report/rnp/voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_vocation_rnp_po_report(request, vocation_id, task_id):
    heading = "Section 2: Edit of adolescent boys linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.get(id=vocation_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
       

        vocation_obj.adolescent_name_id = adolescent_name
        vocation_obj.date_of_registration = date_of_registration
        vocation_obj.age = age or None
        vocation_obj.parent_guardian_name = parent_guardian_name
        vocation_obj.training_subject = training_subject
        vocation_obj.training_providing_by = training_providing_by
        vocation_obj.duration_days = duration_days
        vocation_obj.training_complated = training_complated
        vocation_obj.placement_offered = placement_offered or None
        vocation_obj.placement_accepted = placement_accepted or None
        vocation_obj.type_of_employment = type_of_employment or None
        vocation_obj.task_id = task
        vocation_obj.site_id =  current_site
        vocation_obj.save()
        return redirect('/po-report/rnp/vocation-listing/'+str(task_id))
    return render(request, 'po_report/rnp/voctional_training/edit_vocation_training.html', locals())



@ login_required(login_url='/login/')
def adolescents_referred_listing_rnp_po_report(request, task_id):
    heading = "Section 4: Details of adolescents referred"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, adolescents_referred)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/adolescent_referred/adolescent_referred_listing.html', locals())

@ login_required(login_url='/login/')
def add_adolescents_referred_rnp_po_report(request, task_id):
    heading = "Section 4: Add of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')
        task = Task.objects.get(id=task_id)
        adolescents_referred = AdolescentsReferred.objects.create(awc_name=awc_name, girls_referred_10_14_year=girls_referred_10_14_year, 
        girls_referred_15_19_year=girls_referred_15_19_year, boys_referred_10_14_year=boys_referred_10_14_year, boys_referred_15_19_year=boys_referred_15_19_year,
        girls_hwc_referred=girls_hwc_referred, girls_hwc_visited=girls_hwc_visited, girls_afhc_referred=girls_afhc_referred, girls_afhc_visited=girls_afhc_visited,
        girls_dh_referred=girls_dh_referred, girls_dh_visited=girls_dh_visited, boys_hwc_referred=boys_hwc_referred, boys_hwc_visited=boys_hwc_visited,
        boys_afhc_referred=boys_afhc_referred, boys_afhc_visited=boys_afhc_visited, 
        boys_dh_referred=boys_dh_referred, boys_dh_visited=boys_dh_visited, task=task, site_id = current_site)
        adolescents_referred.save()
        return redirect('/po-report/rnp/adolescent-referred-listing/'+str(task_id))
    return render(request, 'po_report/rnp/adolescent_referred/add_adolescen_referred.html', locals())


@ login_required(login_url='/login/')
def edit_adolescents_referred_rnp_po_report(request, adolescents_referred_id, task_id):
    heading = "Section 4: Edit of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.get(id=adolescents_referred_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')  
        task = Task.objects.get(id=task_id)

        adolescents_referred.awc_name_id = awc_name
        adolescents_referred.girls_referred_10_14_year = girls_referred_10_14_year
        adolescents_referred.girls_referred_15_19_year = girls_referred_15_19_year
        adolescents_referred.boys_referred_10_14_year = boys_referred_10_14_year
        adolescents_referred.boys_referred_15_19_year = boys_referred_15_19_year
        adolescents_referred.girls_hwc_referred = girls_hwc_referred
        adolescents_referred.girls_hwc_visited = girls_hwc_visited
        adolescents_referred.girls_afhc_referred = girls_afhc_referred
        adolescents_referred.girls_afhc_visited = girls_afhc_visited
        adolescents_referred.girls_dh_referred = girls_dh_referred
        adolescents_referred.girls_dh_visited = girls_dh_visited
        adolescents_referred.boys_hwc_referred = boys_hwc_referred
        adolescents_referred.boys_hwc_visited = boys_hwc_visited
        adolescents_referred.boys_afhc_referred = boys_afhc_referred
        adolescents_referred.boys_afhc_visited = boys_afhc_visited
        adolescents_referred.boys_dh_referred = boys_dh_referred
        adolescents_referred.boys_dh_visited = boys_dh_visited
        adolescents_referred.task_id = task
        adolescents_referred.site_id =  current_site
        adolescents_referred.save()
        return redirect('/po-report/rnp/adolescent-referred-listing/'+str(task_id))
    return render(request, 'po_report/rnp/adolescent_referred/edit_adolescent_referred.html', locals())



@ login_required(login_url='/login/')
def friendly_club_listing_rnp_po_report(request, task_id):
    heading = "Section 5: Details of Adolescent Friendly Club (AFC)"
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1, panchayat_name__id__in=panchayat_id, task__id = task_id)
    data = pagination_function(request, friendly_club)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/friendly_club/friendly_club_listing.html', locals())

@ login_required(login_url='/login/')
def add_friendly_club_rnp_po_report(request, task_id):
    heading = "Section 5: Add of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club = AdolescentFriendlyClub.objects.create(start_date = date_of_registration, panchayat_name=panchayat_name,
        hsc_name=hsc_name, subject=subject, facilitator=facilitator, designation=designation,
        no_of_sahiya=no_of_sahiya, no_of_aww=no_of_aww, pe_girls_10_14_year=pe_girls_10_14_year,
        pe_girls_15_19_year=pe_girls_15_19_year, pe_boys_10_14_year=pe_boys_10_14_year,
        pe_boys_15_19_year=pe_boys_15_19_year, task=task, site_id = current_site)
        friendly_club.save()
        return redirect('/po-report/rnp/friendly-club-listing/'+str(task_id))
    return render(request, 'po_report/rnp/friendly_club/add_friendly_club.html', locals())



@ login_required(login_url='/login/')
def edit_friendly_club_rnp_po_report(request, friendly_club_id, task_id):
    heading = "Section 5: Edit of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.get(id=friendly_club_id)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club.start_date = date_of_registration
        friendly_club.panchayat_name_id = panchayat_name
        friendly_club.hsc_name = hsc_name
        friendly_club.subject = subject
        friendly_club.facilitator = facilitator
        friendly_club.designation = designation
        friendly_club.no_of_sahiya = no_of_sahiya
        friendly_club.no_of_aww = no_of_aww
        friendly_club.pe_girls_10_14_year = pe_girls_10_14_year
        friendly_club.pe_girls_15_19_year = pe_girls_15_19_year
        friendly_club.pe_boys_10_14_year = pe_boys_10_14_year
        friendly_club.pe_boys_15_19_year = pe_boys_15_19_year
        friendly_club.task_id = task
        friendly_club.site_id =  current_site
        friendly_club.save()
        return redirect('/po-report/rnp/friendly-club-listing/'+str(task_id))
    return render(request, 'po_report/rnp/friendly_club/edit_friendly_club.html', locals())



@ login_required(login_url='/login/')
def balsansad_meeting_listing_rnp_po_report(request, task_id):
    heading = "Section 6: Details of Bal Sansad meetings conducted"
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter(status=1, school_name__id__in=school_id, task__id = task_id)
    data = pagination_function(request, balsansad_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/bal_sansad_metting/bal_sansad_listing.html', locals())

@ login_required(login_url='/login/')
def add_balsansad_meeting_rnp_po_report(request, task_id):
    heading = "Section 6: Add of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter()
    school = School.objects.filter(status=1, id__in=school_id)
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        decision_taken = data.get('decision_taken')
        issues_discussion = data.get('issues_discussion')
        task = Task.objects.get(id=task_id)
        balsansad_meeting = BalSansadMeeting.objects.create(start_date = date_of_registration, school_name=school_name,
        no_of_participants=no_of_participants, decision_taken=decision_taken,
        task=task, site_id = current_site)
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/po-report/rnp/balsansad-listing/'+str(task_id))
    return render(request, 'po_report/rnp/bal_sansad_metting/add_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def edit_balsansad_meeting_rnp_po_report(request, balsansad_id, task_id):
    heading = "Section 6: Edit of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.get(id=balsansad_id)
    school = School.objects.filter(status=1, id__in=school_id)
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        decision_taken = data.get('decision_taken')
        issues_discussion = data.get('issues_discussion')
        task = Task.objects.get(id=task_id)
        balsansad_meeting.start_date = date_of_registration
        balsansad_meeting.school_name_id = school_name
        balsansad_meeting.no_of_participants = no_of_participants
        balsansad_meeting.decision_taken = decision_taken
        balsansad_meeting.task_id = task
        balsansad_meeting.site_id =  current_site
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/po-report/rnp/balsansad-listing/'+str(task_id))
    return render(request, 'po_report/rnp/bal_sansad_metting/edit_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def community_activities_listing_rnp_po_report(request, task_id):
    heading = "Section 7: Details of community engagement activities"
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1, village_name__id__in=village_id, task__id = task_id)
    data = pagination_function(request, activities)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/community_activities/community_activities_listing.html', locals())


@ login_required(login_url='/login/')
def add_community_activities_rnp_po_report(request, task_id):
    heading = "Section 7: Add of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1,)
    village =  Village.objects.filter(status=1, id__in=village_id)
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')
        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities =  CommunityEngagementActivities.objects.create(village_name=village_name, start_date = date_of_registration,
        name_of_event_activity=name_of_event_activity, organized_by=organized_by,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year, adult_male=adult_male,
        adult_female=adult_female, teachers=teachers, pri_members=pri_members, services_providers=services_providers,
        sms_members=sms_members, other=other, task=task, site_id = current_site)
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/po-report/rnp/community-activities-listing/'+str(task_id))
    return render(request, 'po_report/rnp/community_activities/add_community_activities.html', locals())


@ login_required(login_url='/login/')
def edit_community_activities_rnp_po_report(request, activities_id, task_id):
    heading = "Section 7: Edit of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.get(id=activities_id)
    village =  Village.objects.filter(status=1, id__in=village_id)
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        # theme_topic = data.get('theme_topic')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')

        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities.start_date = date_of_registration
        activities.village_name_id = village_name
        activities.name_of_event_activity = name_of_event_activity
        # activities.theme_topic = theme_topic
        activities.organized_by = organized_by
        activities.boys_10_14_year = boys_10_14_year
        activities.boys_15_19_year = boys_15_19_year
        activities.girls_10_14_year = girls_10_14_year
        activities.girls_15_19_year = girls_15_19_year
        activities.champions_15_19_year = champions_15_19_year
        activities.adult_male = adult_male
        activities.adult_female = adult_female
        activities.teachers = teachers
        activities.pri_members = pri_members
        activities.services_providers = services_providers
        activities.sms_members = sms_members
        activities.other = other
        activities.task_id = task
        activities.site_id =  current_site
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/po-report/rnp/community-activities-listing/'+str(task_id))
    return render(request, 'po_report/rnp/community_activities/edit_community_activities.html', locals())


@ login_required(login_url='/login/')
def champions_listing_rnp_po_report(request, task_id):
    heading = "Section 8: Details of exposure visits of adolescent champions"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, champions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/champions/champions_listing.html', locals())




@ login_required(login_url='/login/')
def add_champions_rnp_po_report(request, task_id):
    heading = "Section 8: Add of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions =  Champions.objects.create(awc_name=awc_name, date_of_visit=date_of_visit, girls_10_14_year=girls_10_14_year,
        girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year, boys_15_19_year=boys_15_19_year,
        first_inst_visited=first_inst_visited,second_inst_visited=second_inst_visited or None,
        third_inst_visited=third_inst_visited or None, fourth_inst_visited=fourth_inst_visited or None, task=task, site_id = current_site)
        champions.save()
        return redirect('/po-report/rnp/champions-listing/'+str(task_id))
    return render(request, 'po_report/rnp/champions/add_champions.html', locals())


@ login_required(login_url='/login/')
def edit_champions_rnp_po_report(request, champions_id, task_id):
    heading = "Section 8: Edit of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.get(id=champions_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        date_of_visit = data.get('date_of_visit')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions.awc_name_id = awc_name       
        champions.date_of_visit = date_of_visit 
        champions.girls_10_14_year = girls_10_14_year       
        champions.girls_15_19_year = girls_15_19_year     
        champions.boys_10_14_year = boys_10_14_year       
        champions.boys_15_19_year = boys_15_19_year       
        champions.first_inst_visited = first_inst_visited
        champions.second_inst_visited= second_inst_visited or None
        champions.third_inst_visited = third_inst_visited or None
        champions.fourth_inst_visited = fourth_inst_visited or None
        champions.task_id = task
        champions.site_id =  current_site        
        champions.save()
        return redirect('/po-report/rnp/champions-listing/'+str(task_id))
    return render(request, 'po_report/rnp/champions/edit_champions.html', locals())

@ login_required(login_url='/login/')
def reenrolled_listing_rnp_po_report(request, task_id):
    heading = "Section 9: Details of adolescent re-enrolled in schools"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, adolescent_reenrolled)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/re_enrolled/re_enrolled_listing.html', locals())

@ login_required(login_url='/login/')
def add_reenrolled_rnp_po_report(request, task_id):
    heading = "Section 9: Add of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # school = School.objects.filter(status=1, id__in = school_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled =  AdolescentRe_enrolled.objects.create(adolescent_name=adolescent_name,
        gender=gender, age=age, parent_guardian_name=parent_guardian_name, school_name=school_name, which_class_enrolled=which_class_enrolled,
        task=task, site_id = current_site)
        adolescent_reenrolled.save()
        return redirect('/po-report/rnp/reenrolled-listing/'+str(task_id))
    return render(request, 'po_report/rnp/re_enrolled/add_re_enrolled.html', locals())


@ login_required(login_url='/login/')
def edit_reenrolled_rnp_po_report(request, reenrolled_id, task_id):
    heading = "Section 9: Edit of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.get(id=reenrolled_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    # school = School.objects.filter()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled.adolescent_name_id = adolescent_name
        adolescent_reenrolled.gender = gender
        adolescent_reenrolled.age = age
        adolescent_reenrolled.parent_guardian_name = parent_guardian_name
        adolescent_reenrolled.school_name = school_name
        adolescent_reenrolled.which_class_enrolled = which_class_enrolled
        adolescent_reenrolled.task_id = task
        adolescent_reenrolled.site_id =  current_site
        adolescent_reenrolled.save()
        return redirect('/po-report/rnp/reenrolled-listing/'+str(task_id))
    return render(request, 'po_report/rnp/re_enrolled/edit_re_enrolled.html', locals())


@ login_required(login_url='/login/')
def stakeholders_listing_rnp_po_report(request, task_id):
    heading = "Section 10: Details of capacity building of different stakeholders"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    stakeholders_obj = Stakeholder.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, stakeholders_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/stakeholders/stakeholders_listing.html', locals())


@ login_required(login_url='/login/')
def add_stakeholders_rnp_po_report(request, task_id):
    heading = "Section 10: Add of capacity building of different stakeholders"
    current_site = request.session.get('site_id')
    stakeholders_obj = Stakeholder.objects.filter()
    if request.method == 'POST':
        data = request.POST
        master_trainers_male = data.get('master_trainers_male')
        master_trainers_female = data.get('master_trainers_female')
        master_trainers_total = data.get('master_trainers_total')
        nodal_teachers_male = data.get('nodal_teachers_male')
        nodal_teachers_female = data.get('nodal_teachers_female')
        nodal_teachers_total = data.get('nodal_teachers_total')
        principals_male = data.get('principals_male')
        principals_female = data.get('principals_female')
        principals_total = data.get('principals_total')
        district_level_officials_male = data.get('district_level_officials_male')
        district_level_officials_female = data.get('district_level_officials_female')
        district_level_officials_total = data.get('district_level_officials_total')
        peer_educator_male = data.get('peer_educator_male')
        peer_educator_female = data.get('peer_educator_female')
        peer_educator_total = data.get('peer_educator_total')
        state_level_officials_male = data.get('state_level_officials_male')
        state_level_officials_female = data.get('state_level_officials_female')
        state_level_officials_total = data.get('state_level_officials_total')
        icds_awws_male = data.get('icds_awws_male')
        icds_awws_female = data.get('icds_awws_female')
        icds_awws_total = data.get('icds_awws_total')
        icds_supervisors_male = data.get('icds_supervisors_male')
        icds_supervisors_female = data.get('icds_supervisors_female')
        icds_supervisors_total = data.get('icds_supervisors_total')
        icds_peer_educator_male = data.get('icds_peer_educator_male')
        icds_peer_educator_female = data.get('icds_peer_educator_female')
        icds_peer_educator_total = data.get('icds_peer_educator_total')
        icds_child_developement_project_officers_male = data.get('icds_child_developement_project_officers_male')
        icds_child_developement_project_officers_female = data.get('icds_child_developement_project_officers_female')
        icds_child_developement_project_officers_total = data.get('icds_child_developement_project_officers_total')
        icds_district_level_officials_male = data.get('icds_district_level_officials_male')
        icds_district_level_officials_female = data.get('icds_district_level_officials_female')
        icds_district_level_officials_total = data.get('icds_district_level_officials_total')
        icds_state_level_officials_male = data.get('icds_state_level_officials_male')
        icds_state_level_officials_female = data.get('icds_state_level_officials_female')
        icds_state_level_officials_total = data.get('icds_state_level_officials_total')
        health_ashas_male = data.get('health_ashas_male')
        health_ashas_female = data.get('health_ashas_female')
        health_ashas_total = data.get('health_ashas_total')
        health_anms_male = data.get('health_anms_male')
        health_anms_female = data.get('health_anms_female')
        health_anms_total = data.get('health_anms_total')
        health_bpm_bhm_pheos_male = data.get('health_bpm_bhm_pheos_male')
        health_bpm_bhm_pheos_female = data.get('health_bpm_bhm_pheos_female')
        health_bpm_bhm_pheos_total = data.get('health_bpm_bhm_pheos_total')
        health_medical_officers_male = data.get('health_medical_officers_male')
        health_medical_officers_female = data.get('health_medical_officers_female')
        health_medical_officers_total = data.get('health_medical_officers_total')
        health_district_level_officials_male = data.get('health_district_level_officials_male')
        health_district_level_officials_female = data.get('health_district_level_officials_female')
        health_district_level_officials_total = data.get('health_district_level_officials_total')
        health_state_level_officials_male = data.get('health_state_level_officials_male')
        health_state_level_officials_female = data.get('health_state_level_officials_female')
        health_state_level_officials_total = data.get('health_state_level_officials_total')
        health_rsk_male = data.get('health_rsk_male')
        health_rsk_female = data.get('health_rsk_female')
        health_rsk_total = data.get('health_rsk_total')
        health_peer_educator_male = data.get('health_peer_educator_male')
        health_peer_educator_female = data.get('health_peer_educator_female')
        health_peer_educator_total = data.get('health_peer_educator_total')
        panchayat_ward_members_male = data.get('panchayat_ward_members_male')
        panchayat_ward_members_female = data.get('panchayat_ward_members_female')
        panchayat_ward_members_total = data.get('panchayat_ward_members_total')
        panchayat_up_mukhiya_up_Pramukh_male = data.get('panchayat_up_mukhiya_up_Pramukh_male')
        panchayat_up_mukhiya_up_Pramukh_female = data.get('panchayat_up_mukhiya_up_Pramukh_female')
        panchayat_up_mukhiya_up_Pramukh_total = data.get('panchayat_up_mukhiya_up_Pramukh_total')
        panchayat_mukhiya_Pramukh_male = data.get('panchayat_mukhiya_Pramukh_male')
        panchayat_mukhiya_Pramukh_female = data.get('panchayat_mukhiya_Pramukh_female')
        panchayat_mukhiya_Pramukh_total = data.get('panchayat_mukhiya_Pramukh_total')
        panchayat_samiti_member_male = data.get('panchayat_samiti_member_male')
        panchayat_samiti_member_female = data.get('panchayat_samiti_member_female')
        panchayat_samiti_member_total = data.get('panchayat_samiti_member_total')
        panchayat_zila_parishad_member_male = data.get('panchayat_zila_parishad_member_male')
        panchayat_zila_parishad_member_female = data.get('panchayat_zila_parishad_member_female')
        panchayat_zila_parishad_member_total = data.get('panchayat_zila_parishad_member_total')
        panchayat_vc_zila_parishad_male = data.get('panchayat_vc_zila_parishad_male')
        panchayat_vc_zila_parishad_female = data.get('panchayat_vc_zila_parishad_female')
        panchayat_vc_zila_parishad_total = data.get('panchayat_vc_zila_parishad_total')
        panchayat_chairman_zila_parishad_male = data.get('panchayat_chairman_zila_parishad_male')
        panchayat_chairman_zila_parishad_female = data.get('panchayat_chairman_zila_parishad_female')
        panchayat_chairman_zila_parishad_total = data.get('panchayat_chairman_zila_parishad_total')
        panchayat_block_level_officials_male = data.get('panchayat_block_level_officials_male')
        panchayat_block_level_officials_female = data.get('panchayat_block_level_officials_female')
        panchayat_block_level_officials_total = data.get('panchayat_block_level_officials_total')
        panchayat_district_level_officials_male = data.get('panchayat_district_level_officials_male')
        panchayat_district_level_officials_female = data.get('panchayat_district_level_officials_female')
        panchayat_district_level_officials_total = data.get('panchayat_district_level_officials_total')
        panchayat_state_level_officials_male = data.get('panchayat_state_level_officials_male')
        panchayat_state_level_officials_female = data.get('panchayat_state_level_officials_female')
        panchayat_state_level_officials_total = data.get('panchayat_state_level_officials_total')
        media_interns_male = data.get('media_interns_male')
        media_interns_female = data.get('media_interns_female')
        media_interns_total = data.get('media_interns_total')
        media_journalists_male = data.get('media_journalists_male')
        media_journalists_female = data.get('media_journalists_female')
        media_journalists_total = data.get('media_journalists_total')
        media_editors_male = data.get('media_editors_male')
        media_editors_female = data.get('media_editors_female')
        media_editors_total = data.get('media_editors_total')
        others_block_cluster_field_corrdinators_male = data.get('others_block_cluster_field_corrdinators_male')
        others_block_cluster_field_corrdinators_female = data.get('others_block_cluster_field_corrdinators_female')
        others_block_cluster_field_corrdinators_total = data.get('others_block_cluster_field_corrdinators_total')
        others_ngo_staff_corrdinators_male = data.get('others_ngo_staff_corrdinators_male')
        others_ngo_staff_corrdinators_female = data.get('others_ngo_staff_corrdinators_female')
        others_ngo_staff_corrdinators_total = data.get('others_ngo_staff_corrdinators_total')
        others_male = data.get('others_male')
        others_female = data.get('others_female')
        others_total = data.get('others_total')
        total_male = data.get('total_male')
        total_female = data.get('total_female')
        total = data.get('total')
        task = Task.objects.get(id=task_id)

        stakeholders_obj = Stakeholder.objects.create(user_name=request.user,
        master_trainers_male=master_trainers_male, master_trainers_female=master_trainers_female, master_trainers_total=master_trainers_total,
        nodal_teachers_male=nodal_teachers_male, nodal_teachers_female=nodal_teachers_female, nodal_teachers_total=nodal_teachers_total,
        principals_male=principals_male, principals_female=principals_female, principals_total=principals_total, 
        district_level_officials_male=district_level_officials_male, district_level_officials_female=district_level_officials_female, district_level_officials_total=district_level_officials_total,
        peer_educator_male=peer_educator_male, peer_educator_female=peer_educator_female, peer_educator_total=peer_educator_total,
        state_level_officials_male=state_level_officials_male, state_level_officials_female=state_level_officials_female, state_level_officials_total=state_level_officials_total,
        icds_awws_male=icds_awws_male, icds_awws_female=icds_awws_female, icds_awws_total=icds_awws_total,
        icds_supervisors_male=icds_supervisors_male, icds_supervisors_female=icds_supervisors_female, icds_supervisors_total=icds_supervisors_total,
        icds_peer_educator_male=icds_peer_educator_male, icds_peer_educator_female=icds_peer_educator_female, icds_peer_educator_total=icds_peer_educator_total,
        icds_child_developement_project_officers_male=icds_child_developement_project_officers_male, icds_child_developement_project_officers_female=icds_child_developement_project_officers_female, icds_child_developement_project_officers_total=icds_child_developement_project_officers_total,
        icds_district_level_officials_male=icds_district_level_officials_male, icds_district_level_officials_female=icds_district_level_officials_female, icds_district_level_officials_total=icds_district_level_officials_total,
        icds_state_level_officials_male=icds_state_level_officials_male, icds_state_level_officials_female=icds_state_level_officials_female, icds_state_level_officials_total=icds_state_level_officials_total,
        health_ashas_male=health_ashas_male, health_ashas_female=health_ashas_female, health_ashas_total=health_ashas_total,
        health_anms_male=health_anms_male, health_anms_female=health_anms_female, health_anms_total=health_anms_total,
        health_bpm_bhm_pheos_male=health_bpm_bhm_pheos_male, health_bpm_bhm_pheos_female=health_bpm_bhm_pheos_female, health_bpm_bhm_pheos_total=health_bpm_bhm_pheos_total,
        health_medical_officers_male=health_medical_officers_male, health_medical_officers_female=health_medical_officers_female, health_medical_officers_total=health_medical_officers_total,
        health_district_level_officials_male=health_district_level_officials_male, health_district_level_officials_female=health_district_level_officials_female, health_district_level_officials_total=health_district_level_officials_total,
        health_state_level_officials_male=health_state_level_officials_male, health_state_level_officials_female=health_state_level_officials_female, health_state_level_officials_total=health_state_level_officials_total,
        health_rsk_male=health_rsk_male, health_rsk_female=health_rsk_female, health_rsk_total=health_rsk_total,
        health_peer_educator_male=health_peer_educator_male, health_peer_educator_female=health_peer_educator_female, health_peer_educator_total=health_peer_educator_total,
        panchayat_ward_members_male=panchayat_ward_members_male, panchayat_ward_members_female=panchayat_ward_members_female, panchayat_ward_members_total=panchayat_ward_members_total,
        panchayat_up_mukhiya_up_Pramukh_male=panchayat_up_mukhiya_up_Pramukh_male, panchayat_up_mukhiya_up_Pramukh_female=panchayat_up_mukhiya_up_Pramukh_female, panchayat_up_mukhiya_up_Pramukh_total=panchayat_up_mukhiya_up_Pramukh_total,
        panchayat_mukhiya_Pramukh_male=panchayat_mukhiya_Pramukh_male, panchayat_mukhiya_Pramukh_female=panchayat_mukhiya_Pramukh_female, panchayat_mukhiya_Pramukh_total=panchayat_mukhiya_Pramukh_total,
        panchayat_samiti_member_male=panchayat_samiti_member_male, panchayat_samiti_member_female=panchayat_samiti_member_female, panchayat_samiti_member_total=panchayat_samiti_member_total,
        panchayat_zila_parishad_member_male=panchayat_zila_parishad_member_male, panchayat_zila_parishad_member_female=panchayat_zila_parishad_member_female, panchayat_zila_parishad_member_total=panchayat_zila_parishad_member_total,
        panchayat_vc_zila_parishad_male=panchayat_vc_zila_parishad_male, panchayat_vc_zila_parishad_female=panchayat_vc_zila_parishad_female, panchayat_vc_zila_parishad_total=panchayat_vc_zila_parishad_total,
        panchayat_chairman_zila_parishad_male=panchayat_chairman_zila_parishad_male, panchayat_chairman_zila_parishad_female=panchayat_chairman_zila_parishad_female, panchayat_chairman_zila_parishad_total=panchayat_chairman_zila_parishad_total,
        panchayat_block_level_officials_male=panchayat_block_level_officials_male, panchayat_block_level_officials_female=panchayat_block_level_officials_female, panchayat_block_level_officials_total=panchayat_block_level_officials_total,
        panchayat_district_level_officials_male=panchayat_district_level_officials_male, panchayat_district_level_officials_female=panchayat_district_level_officials_female, panchayat_district_level_officials_total=panchayat_district_level_officials_total,
        panchayat_state_level_officials_male=panchayat_state_level_officials_male, panchayat_state_level_officials_female=panchayat_state_level_officials_female, panchayat_state_level_officials_total=panchayat_state_level_officials_total,
        media_interns_male=media_interns_male, media_interns_female=media_interns_female, media_interns_total=media_interns_total,
        media_journalists_male=media_journalists_male, media_journalists_female=media_journalists_female, media_journalists_total=media_journalists_total,
        media_editors_male=media_editors_male, media_editors_female=media_editors_female, media_editors_total=media_editors_total,
        others_block_cluster_field_corrdinators_male=others_block_cluster_field_corrdinators_male, others_block_cluster_field_corrdinators_female=others_block_cluster_field_corrdinators_female, others_block_cluster_field_corrdinators_total=others_block_cluster_field_corrdinators_total,
        others_ngo_staff_corrdinators_male=others_ngo_staff_corrdinators_male, others_ngo_staff_corrdinators_female=others_ngo_staff_corrdinators_female, others_ngo_staff_corrdinators_total=others_ngo_staff_corrdinators_total,
        others_male=others_male, others_female=others_female, others_total=others_total,
        total_male=total_male, total_female=total_female, total=total, task=task, site_id = current_site,
        )
        stakeholders_obj.save()
        return redirect('/po-report/rnp/stakeholders-listing/'+str(task_id))
    return render(request, 'po_report/rnp/stakeholders/add_stakeholders.html', locals())


@ login_required(login_url='/login/')
def edit_stakeholders_rnp_po_report(request, stakeholders_id, task_id):
    heading = "Section 10: Edit of capacity building of different stakeholders"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    stakeholders_obj = Stakeholder.objects.get(id=stakeholders_id)
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    if request.method == 'POST':
        data = request.POST
        master_trainers_male = data.get('master_trainers_male')
        master_trainers_female = data.get('master_trainers_female')
        master_trainers_total = data.get('master_trainers_total')
        nodal_teachers_male = data.get('nodal_teachers_male')
        nodal_teachers_female = data.get('nodal_teachers_female')
        nodal_teachers_total = data.get('nodal_teachers_total')
        principals_male = data.get('principals_male')
        principals_female = data.get('principals_female')
        principals_total = data.get('principals_total')
        district_level_officials_male = data.get('district_level_officials_male')
        district_level_officials_female = data.get('district_level_officials_female')
        district_level_officials_total = data.get('district_level_officials_total')
        peer_educator_male = data.get('peer_educator_male')
        peer_educator_female = data.get('peer_educator_female')
        peer_educator_total = data.get('peer_educator_total')
        state_level_officials_male = data.get('state_level_officials_male')
        state_level_officials_female = data.get('state_level_officials_female')
        state_level_officials_total = data.get('state_level_officials_total')
        icds_awws_male = data.get('icds_awws_male')
        icds_awws_female = data.get('icds_awws_female')
        icds_awws_total = data.get('icds_awws_total')
        icds_supervisors_male = data.get('icds_supervisors_male')
        icds_supervisors_female = data.get('icds_supervisors_female')
        icds_supervisors_total = data.get('icds_supervisors_total')
        icds_peer_educator_male = data.get('icds_peer_educator_male')
        icds_peer_educator_female = data.get('icds_peer_educator_female')
        icds_peer_educator_total = data.get('icds_peer_educator_total')
        icds_child_developement_project_officers_male = data.get('icds_child_developement_project_officers_male')
        icds_child_developement_project_officers_female = data.get('icds_child_developement_project_officers_female')
        icds_child_developement_project_officers_total = data.get('icds_child_developement_project_officers_total')
        icds_district_level_officials_male = data.get('icds_district_level_officials_male')
        icds_district_level_officials_female = data.get('icds_district_level_officials_female')
        icds_district_level_officials_total = data.get('icds_district_level_officials_total')
        icds_state_level_officials_male = data.get('icds_state_level_officials_male')
        icds_state_level_officials_female = data.get('icds_state_level_officials_female')
        icds_state_level_officials_total = data.get('icds_state_level_officials_total')
        health_ashas_male = data.get('health_ashas_male')
        health_ashas_female = data.get('health_ashas_female')
        health_ashas_total = data.get('health_ashas_total')
        health_anms_male = data.get('health_anms_male')
        health_anms_female = data.get('health_anms_female')
        health_anms_total = data.get('health_anms_total')
        health_bpm_bhm_pheos_male = data.get('health_bpm_bhm_pheos_male')
        health_bpm_bhm_pheos_female = data.get('health_bpm_bhm_pheos_female')
        health_bpm_bhm_pheos_total = data.get('health_bpm_bhm_pheos_total')
        health_medical_officers_male = data.get('health_medical_officers_male')
        health_medical_officers_female = data.get('health_medical_officers_female')
        health_medical_officers_total = data.get('health_medical_officers_total')
        health_district_level_officials_male = data.get('health_district_level_officials_male')
        health_district_level_officials_female = data.get('health_district_level_officials_female')
        health_district_level_officials_total = data.get('health_district_level_officials_total')
        health_state_level_officials_male = data.get('health_state_level_officials_male')
        health_state_level_officials_female = data.get('health_state_level_officials_female')
        health_state_level_officials_total = data.get('health_state_level_officials_total')
        health_rsk_male = data.get('health_rsk_male')
        health_rsk_female = data.get('health_rsk_female')
        health_rsk_total = data.get('health_rsk_total')
        health_peer_educator_male = data.get('health_peer_educator_male')
        health_peer_educator_female = data.get('health_peer_educator_female')
        health_peer_educator_total = data.get('health_peer_educator_total')
        panchayat_ward_members_male = data.get('panchayat_ward_members_male')
        panchayat_ward_members_female = data.get('panchayat_ward_members_female')
        panchayat_ward_members_total = data.get('panchayat_ward_members_total')
        panchayat_up_mukhiya_up_Pramukh_male = data.get('panchayat_up_mukhiya_up_Pramukh_male')
        panchayat_up_mukhiya_up_Pramukh_female = data.get('panchayat_up_mukhiya_up_Pramukh_female')
        panchayat_up_mukhiya_up_Pramukh_total = data.get('panchayat_up_mukhiya_up_Pramukh_total')
        panchayat_mukhiya_Pramukh_male = data.get('panchayat_mukhiya_Pramukh_male')
        panchayat_mukhiya_Pramukh_female = data.get('panchayat_mukhiya_Pramukh_female')
        panchayat_mukhiya_Pramukh_total = data.get('panchayat_mukhiya_Pramukh_total')
        panchayat_samiti_member_male = data.get('panchayat_samiti_member_male')
        panchayat_samiti_member_female = data.get('panchayat_samiti_member_female')
        panchayat_samiti_member_total = data.get('panchayat_samiti_member_total')
        panchayat_zila_parishad_member_male = data.get('panchayat_zila_parishad_member_male')
        panchayat_zila_parishad_member_female = data.get('panchayat_zila_parishad_member_female')
        panchayat_zila_parishad_member_total = data.get('panchayat_zila_parishad_member_total')
        panchayat_vc_zila_parishad_male = data.get('panchayat_vc_zila_parishad_male')
        panchayat_vc_zila_parishad_female = data.get('panchayat_vc_zila_parishad_female')
        panchayat_vc_zila_parishad_total = data.get('panchayat_vc_zila_parishad_total')
        panchayat_chairman_zila_parishad_male = data.get('panchayat_chairman_zila_parishad_male')
        panchayat_chairman_zila_parishad_female = data.get('panchayat_chairman_zila_parishad_female')
        panchayat_chairman_zila_parishad_total = data.get('panchayat_chairman_zila_parishad_total')
        panchayat_block_level_officials_male = data.get('panchayat_block_level_officials_male')
        panchayat_block_level_officials_female = data.get('panchayat_block_level_officials_female')
        panchayat_block_level_officials_total = data.get('panchayat_block_level_officials_total')
        panchayat_district_level_officials_male = data.get('panchayat_district_level_officials_male')
        panchayat_district_level_officials_female = data.get('panchayat_district_level_officials_female')
        panchayat_district_level_officials_total = data.get('panchayat_district_level_officials_total')
        panchayat_state_level_officials_male = data.get('panchayat_state_level_officials_male')
        panchayat_state_level_officials_female = data.get('panchayat_state_level_officials_female')
        panchayat_state_level_officials_total = data.get('panchayat_state_level_officials_total')
        media_interns_male = data.get('media_interns_male')
        media_interns_female = data.get('media_interns_female')
        media_interns_total = data.get('media_interns_total')
        media_journalists_male = data.get('media_journalists_male')
        media_journalists_female = data.get('media_journalists_female')
        media_journalists_total = data.get('media_journalists_total')
        media_editors_male = data.get('media_editors_male')
        media_editors_female = data.get('media_editors_female')
        media_editors_total = data.get('media_editors_total')
        others_block_cluster_field_corrdinators_male = data.get('others_block_cluster_field_corrdinators_male')
        others_block_cluster_field_corrdinators_female = data.get('others_block_cluster_field_corrdinators_female')
        others_block_cluster_field_corrdinators_total = data.get('others_block_cluster_field_corrdinators_total')
        others_ngo_staff_corrdinators_male = data.get('others_ngo_staff_corrdinators_male')
        others_ngo_staff_corrdinators_female = data.get('others_ngo_staff_corrdinators_female')
        others_ngo_staff_corrdinators_total = data.get('others_ngo_staff_corrdinators_total')
        others_male = data.get('others_male')
        others_female = data.get('others_female')
        others_total = data.get('others_total')
        total_male = data.get('total_male')
        total_female = data.get('total_female')
        total = data.get('total')
        task = Task.objects.get(id=task_id)

        stakeholders_obj.user_name_id = request.user
        stakeholders_obj.master_trainers_male = master_trainers_male
        stakeholders_obj.master_trainers_female = master_trainers_female
        stakeholders_obj.master_trainers_total = master_trainers_total
        stakeholders_obj.nodal_teachers_male = nodal_teachers_male
        stakeholders_obj.nodal_teachers_female = nodal_teachers_female
        stakeholders_obj.nodal_teachers_total = nodal_teachers_total
        stakeholders_obj.principals_male = principals_male
        stakeholders_obj.principals_female = principals_female
        stakeholders_obj.principals_total = principals_total
        stakeholders_obj.district_level_officials_male = district_level_officials_male
        stakeholders_obj.district_level_officials_female = district_level_officials_female
        stakeholders_obj.district_level_officials_total = district_level_officials_total
        stakeholders_obj.peer_educator_male = peer_educator_male
        stakeholders_obj.peer_educator_female = peer_educator_female
        stakeholders_obj.peer_educator_total = peer_educator_total
        stakeholders_obj.state_level_officials_male = state_level_officials_male
        stakeholders_obj.state_level_officials_female = state_level_officials_female
        stakeholders_obj.state_level_officials_total = state_level_officials_total
        stakeholders_obj.icds_awws_male = icds_awws_male
        stakeholders_obj.icds_awws_female = icds_awws_female
        stakeholders_obj.icds_awws_total = icds_awws_total
        stakeholders_obj.icds_supervisors_male = icds_supervisors_male
        stakeholders_obj.icds_supervisors_female = icds_supervisors_female
        stakeholders_obj.icds_supervisors_total = icds_supervisors_total
        stakeholders_obj.icds_peer_educator_male = icds_peer_educator_male
        stakeholders_obj.icds_peer_educator_female = icds_peer_educator_female
        stakeholders_obj.icds_peer_educator_total = icds_peer_educator_total
        stakeholders_obj.icds_child_developement_project_officers_male = icds_child_developement_project_officers_male
        stakeholders_obj.icds_child_developement_project_officers_female = icds_child_developement_project_officers_female
        stakeholders_obj.icds_child_developement_project_officers_total = icds_child_developement_project_officers_total
        stakeholders_obj.icds_district_level_officials_male = icds_district_level_officials_male
        stakeholders_obj.icds_district_level_officials_female = icds_district_level_officials_female
        stakeholders_obj.icds_district_level_officials_total = icds_district_level_officials_total
        stakeholders_obj.icds_state_level_officials_male = icds_state_level_officials_male
        stakeholders_obj.icds_state_level_officials_female = icds_state_level_officials_female
        stakeholders_obj.icds_state_level_officials_total = icds_state_level_officials_total
        stakeholders_obj.health_ashas_male = health_ashas_male
        stakeholders_obj.health_ashas_female = health_ashas_female
        stakeholders_obj.health_ashas_total = health_ashas_total
        stakeholders_obj.health_anms_male = health_anms_male
        stakeholders_obj.health_anms_female = health_anms_female
        stakeholders_obj.health_anms_total = health_anms_total
        stakeholders_obj.health_bpm_bhm_pheos_male = health_bpm_bhm_pheos_male
        stakeholders_obj.health_bpm_bhm_pheos_female = health_bpm_bhm_pheos_female
        stakeholders_obj.health_bpm_bhm_pheos_total = health_bpm_bhm_pheos_total
        stakeholders_obj.health_medical_officers_male = health_medical_officers_male
        stakeholders_obj.health_medical_officers_female = health_medical_officers_female
        stakeholders_obj.health_medical_officers_total = health_medical_officers_total
        stakeholders_obj.health_district_level_officials_male = health_district_level_officials_male
        stakeholders_obj.health_district_level_officials_female = health_district_level_officials_female
        stakeholders_obj.health_district_level_officials_total = health_district_level_officials_total
        stakeholders_obj.health_state_level_officials_male = health_state_level_officials_male
        stakeholders_obj.health_state_level_officials_female = health_state_level_officials_female
        stakeholders_obj.health_state_level_officials_total = health_state_level_officials_total
        stakeholders_obj.health_rsk_male = health_rsk_male
        stakeholders_obj.health_rsk_female = health_rsk_female
        stakeholders_obj.health_rsk_total = health_rsk_total
        stakeholders_obj.health_peer_educator_male = health_peer_educator_male
        stakeholders_obj.health_peer_educator_female = health_peer_educator_female
        stakeholders_obj.health_peer_educator_total = health_peer_educator_total
        stakeholders_obj.panchayat_ward_members_male = panchayat_ward_members_male
        stakeholders_obj.panchayat_ward_members_female = panchayat_ward_members_female
        stakeholders_obj.panchayat_ward_members_total = panchayat_ward_members_total
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_male = panchayat_up_mukhiya_up_Pramukh_male
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_female = panchayat_up_mukhiya_up_Pramukh_female
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_total = panchayat_up_mukhiya_up_Pramukh_total
        stakeholders_obj.panchayat_mukhiya_Pramukh_male = panchayat_mukhiya_Pramukh_male
        stakeholders_obj.panchayat_mukhiya_Pramukh_female = panchayat_mukhiya_Pramukh_female
        stakeholders_obj.panchayat_mukhiya_Pramukh_total = panchayat_mukhiya_Pramukh_total
        stakeholders_obj.panchayat_samiti_member_male = panchayat_samiti_member_male
        stakeholders_obj.panchayat_samiti_member_female = panchayat_samiti_member_female
        stakeholders_obj.panchayat_samiti_member_male = panchayat_samiti_member_total
        stakeholders_obj.panchayat_zila_parishad_member_male = panchayat_zila_parishad_member_male
        stakeholders_obj.panchayat_zila_parishad_member_female = panchayat_zila_parishad_member_female
        stakeholders_obj.panchayat_zila_parishad_member_total = panchayat_zila_parishad_member_total
        stakeholders_obj.panchayat_vc_zila_parishad_male = panchayat_vc_zila_parishad_male
        stakeholders_obj.panchayat_vc_zila_parishad_female = panchayat_vc_zila_parishad_female
        stakeholders_obj.panchayat_vc_zila_parishad_total = panchayat_vc_zila_parishad_total
        stakeholders_obj.panchayat_chairman_zila_parishad_male = panchayat_chairman_zila_parishad_male
        stakeholders_obj.panchayat_chairman_zila_parishad_female = panchayat_chairman_zila_parishad_female
        stakeholders_obj.panchayat_chairman_zila_parishad_total = panchayat_chairman_zila_parishad_total
        stakeholders_obj.panchayat_block_level_officials_male = panchayat_block_level_officials_male
        stakeholders_obj.panchayat_block_level_officials_female = panchayat_block_level_officials_female
        stakeholders_obj.panchayat_block_level_officials_total = panchayat_block_level_officials_total
        stakeholders_obj.panchayat_district_level_officials_male = panchayat_district_level_officials_male
        stakeholders_obj.panchayat_district_level_officials_female = panchayat_district_level_officials_female
        stakeholders_obj.panchayat_district_level_officials_total = panchayat_district_level_officials_total
        stakeholders_obj.panchayat_state_level_officials_male = panchayat_state_level_officials_male
        stakeholders_obj.panchayat_state_level_officials_female = panchayat_state_level_officials_female
        stakeholders_obj.panchayat_state_level_officials_total = panchayat_state_level_officials_total
        stakeholders_obj.media_interns_male = media_interns_male
        stakeholders_obj.media_interns_female = media_interns_female
        stakeholders_obj.media_interns_total = media_interns_total
        stakeholders_obj.media_journalists_male = media_journalists_male
        stakeholders_obj.media_journalists_female = media_journalists_female
        stakeholders_obj.media_journalists_total = media_journalists_total
        stakeholders_obj.media_editors_male = media_editors_male
        stakeholders_obj.media_editors_female = media_editors_female
        stakeholders_obj.media_editors_total = media_editors_total
        stakeholders_obj.others_block_cluster_field_corrdinators_male = others_block_cluster_field_corrdinators_male
        stakeholders_obj.others_block_cluster_field_corrdinators_female = others_block_cluster_field_corrdinators_female
        stakeholders_obj.others_block_cluster_field_corrdinators_total = others_block_cluster_field_corrdinators_total
        stakeholders_obj.others_ngo_staff_corrdinators_male = others_ngo_staff_corrdinators_male
        stakeholders_obj.others_ngo_staff_corrdinators_female = others_ngo_staff_corrdinators_female
        stakeholders_obj.others_ngo_staff_corrdinators_total = others_ngo_staff_corrdinators_total
        stakeholders_obj.others_male = others_male
        stakeholders_obj.others_female = others_female
        stakeholders_obj.others_total = others_total
        stakeholders_obj.total_male = total_male
        stakeholders_obj.total_female = total_female
        stakeholders_obj.total = total
        stakeholders_obj.task_id = task
        stakeholders_obj.site_id =  current_site
        stakeholders_obj.save()
        return redirect('/po-report/rnp/stakeholders-listing/'+str(task_id))
    return render(request, 'po_report/rnp/stakeholders/edit_stakeholders.html', locals())




@ login_required(login_url='/login/')
def sessions_monitoring_listing_rnp_po_report(request, task_id):
    heading = "Section 11: Details of sessions monitoring and handholding support at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    village_id =CC_AWC_AH.objects.filter(status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, sessions_monitoring)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/sessions_monitoring/sessions_monitoring_listing.html', locals())


@ login_required(login_url='/login/')
def add_sessions_monitoring_rnp_po_report(request, task_id):
    heading = "Section 11: Add of sessions monitoring and handholding support at block level"
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')

    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
        sessions = data.getlist('session_attended')
        session_attended = ", ".join(sessions)
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        sessions_monitoring = SessionMonitoring.objects.create(name_of_visited=name_of_visited, session_attended=session_attended,
        date=date,
        observation=observation, recommendation=recommendation, task=task, site_id = current_site)
        
        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            sessions_monitoring.content_type=content_type
            sessions_monitoring.object_id=selected_object_id
        
        if name_of_visited in ['4','5']:
            sessions_monitoring.name_of_place_visited = selected_field_other

        sessions_monitoring.save()
        return redirect('/po-report/rnp/sessions-monitoring-listing/'+str(task_id))
    return render(request, 'po_report/rnp/sessions_monitoring/add_sessions_monitoring.html', locals())


@ login_required(login_url='/login/')
def edit_sessions_monitoring_rnp_po_report(request, sessions_id, task_id):
    heading = "Section 11: Edit of sessions monitoring and handholding support at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.get(id=sessions_id)
    session_choice = sessions_monitoring.session_attended.split(', ')
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        selected_field_other = data.get('selected_field_other')
        name_of_visited = data.get('name_of_visited')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        content_type = ContentType.objects.get(model=content_type_model)
        date = data.get('date')
        sessions = data.getlist('session_attended')
        session_attended = ", ".join(sessions)
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        sessions_monitoring.name_of_visited = name_of_visited

        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            sessions_monitoring.content_type=content_type
            sessions_monitoring.object_id=selected_object_id

        if name_of_visited in ['4','5']:
            sessions_monitoring.name_of_place_visited = selected_field_other

        sessions_monitoring.date = date
        sessions_monitoring.session_attended = session_attended
        sessions_monitoring.observation = observation
        sessions_monitoring.recommendation = recommendation
        sessions_monitoring.task_id = task
        sessions_monitoring.site_id =  current_site
        sessions_monitoring.save()
        return redirect('/po-report/rnp/sessions-monitoring-listing/'+str(task_id))
    return render(request, 'po_report/rnp/sessions_monitoring/edit_sessions_monitoring.html', locals())



@ login_required(login_url='/login/')
def facility_visits_listing_rnp_po_report(request, task_id):
    heading = "Section 12: Details of events & facility visits at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    user_report = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    village_id =CC_AWC_AH.objects.filter(status=1, user=user_report).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=user_report).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=user_report).values_list('school__id')
    facility_visits = Events.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, facility_visits)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/facility_visits/facility_visits_listing.html', locals())


@ login_required(login_url='/login/')
def add_facility_visits_rnp_po_report(request, task_id):
    heading = "Section 12: Add of events & facility visits at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    facility_visits = Events.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
        purpose_visited = data.get('purpose_visited')
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        
        facility_visits = Events.objects.create(name_of_visited=name_of_visited, purpose_visited=purpose_visited,
        date=date,
        observation=observation, recommendation=recommendation, task=task, site_id = current_site)
        
        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            facility_visits.content_type=content_type
            facility_visits.object_id=selected_object_id

        if name_of_visited in ['4','5','6','7','8','9','10','11']:
            facility_visits.name_of_place_visited = selected_field_other

        facility_visits.save()
        return redirect('/po-report/rnp/facility-visits-listing/'+str(task_id))
    return render(request, 'po_report/rnp/facility_visits/add_facility_visits.html', locals())


@ login_required(login_url='/login/')
def edit_facility_visits_rnp_po_report(request, facility_id, task_id):
    heading = "Section 12: Edit of events & facility visits at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    facility_visits = Events.objects.get(id=facility_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
        purpose_visited = data.get('purpose_visited')
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        facility_visits.name_of_visited = name_of_visited

        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            facility_visits.content_type = content_type
            facility_visits.object_id = selected_object_id
        
        if name_of_visited in ['4','5','6','7','8','9','10','11']:
            facility_visits.name_of_place_visited = selected_field_other

        facility_visits.date = date
        facility_visits.purpose_visited = purpose_visited
        facility_visits.observation = observation
        facility_visits.recommendation = recommendation
        facility_visits.task_id = task
        facility_visits.site_id =  current_site
        facility_visits.save()
        return redirect('/po-report/rnp/facility-visits-listing/'+str(task_id))
    return render(request, 'po_report/rnp/facility_visits/edit_facility_visits.html', locals())



@ login_required(login_url='/login/')
def followup_liaision_listing_rnp_po_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    heading = "Section 14: Details of one to one (Follow up/ Liaison) meetings at district & Block Level"
    followup_liaision = FollowUP_LiaisionMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, followup_liaision)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/followup_liaision/followup_liaision_listing.html', locals())


@ login_required(login_url='/login/')
def add_followup_liaision_rnp_po_report(request, task_id):
    heading = "Section 14: Add of one to one (Follow up/ Liaison) meetings at district & Block Level"
    current_site = request.session.get('site_id')
    followup_liaision = FollowUP_LiaisionMeeting.objects.filter()
    meeting_obj = MasterLookUp.objects.filter(parent__slug = 'meeting-with-designation')
    if request.method == 'POST':
        data = request.POST
        date = data.get('date')
        district_block_level = data.get('district_block_level')
        meeting_id = data.get('meeting')
        meeting = MasterLookUp.objects.get(id = meeting_id)
        departments = data.get('departments')
        point_of_discussion = data.get('point_of_discussion')
        outcome = data.get('outcome')
        decision_taken = data.get('decision_taken')
        remarks = data.get('remarks')
        task = Task.objects.get(id=task_id)

        followup_liaision = FollowUP_LiaisionMeeting.objects.create(user_name=request.user, date=date,
        district_block_level=district_block_level, meeting_name=meeting, departments=departments, point_of_discussion=point_of_discussion,
        outcome=outcome, decision_taken=decision_taken, remarks=remarks, site_id = current_site, task=task)
        followup_liaision.save()
        return redirect('/po-report/rnp/followup-liaision-listing/'+str(task_id))
    return render(request, 'po_report/rnp/followup_liaision/add_followup_liaision.html', locals())


@ login_required(login_url='/login/')
def edit_followup_liaision_rnp_po_report(request, followup_liaision_id, task_id):
    heading = "Section 14: Edit of one to one (Follow up/ Liaison) meetings at district & Block Level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    followup_liaision = FollowUP_LiaisionMeeting.objects.get(id=followup_liaision_id)
    meeting_obj = MasterLookUp.objects.filter(parent__slug = 'meeting-with-designation')
    if request.method == 'POST':
        data = request.POST
        date = data.get('date')
        district_block_level = data.get('district_block_level')
        meeting_id = data.get('meeting')
        meeting = MasterLookUp.objects.get(id = meeting_id)
        departments = data.get('departments')
        point_of_discussion = data.get('point_of_discussion')
        outcome = data.get('outcome')
        decision_taken = data.get('decision_taken')
        remarks = data.get('remarks')
        task = Task.objects.get(id=task_id)


        followup_liaision.user_name = request.user
        followup_liaision.date = date
        followup_liaision.district_block_level = district_block_level
        followup_liaision.meeting_name = meeting
        followup_liaision.departments = departments
        followup_liaision.point_of_discussion = point_of_discussion
        followup_liaision.outcome = outcome
        followup_liaision.decision_taken = decision_taken
        followup_liaision.remarks = remarks
        followup_liaision.task_id = task
        followup_liaision.site_id =  current_site
        followup_liaision.save()
        return redirect('/po-report/rnp/followup-liaision-listing/'+str(task_id))
    return render(request, 'po_report/rnp/followup_liaision/edit_followup_liaision.html', locals())



@ login_required(login_url='/login/')
def participating_meeting_listing_rnp_po_report(request, task_id):
    heading = "Section 13: Details of participating in meetings at district and block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    participating_meeting = ParticipatingMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, participating_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/participating_meeting/participating_meeting_listing.html', locals())

@ login_required(login_url='/login/')
def add_participating_meeting_rnp_po_report(request, task_id):
    heading = "Section 13: Add of participating in meetings at district and block level"
    current_site = request.session.get('site_id')
    participating_meeting = ParticipatingMeeting.objects.filter()
    if request.method == 'POST':
        data = request.POST
        type_of_meeting = data.get('type_of_meeting')
        district_block_level = data.get('district_block_level')
        department = data.get('department')
        point_of_discussion = data.get('point_of_discussion')
        districit_level_officials = data.get('districit_level_officials')
        block_level = data.get('block_level')
        cluster_level = data.get('cluster_level')
        no_of_pri = data.get('no_of_pri')
        no_of_others = data.get('no_of_others')
        date = data.get('date')
        task = Task.objects.get(id=task_id)
        participating_meeting = ParticipatingMeeting.objects.create(user_name=request.user, type_of_meeting=type_of_meeting,
        department=department, point_of_discussion=point_of_discussion, districit_level_officials=districit_level_officials,
        block_level=block_level, cluster_level=cluster_level, no_of_pri=no_of_pri, no_of_others=no_of_others,
        district_block_level=district_block_level, date=date, task=task, site_id = current_site,)
        participating_meeting.save()
        return redirect('/po-report/rnp/participating-meeting-listing/'+str(task_id))
    return render(request, 'po_report/rnp/participating_meeting/add_participating_meeting.html', locals())

@ login_required(login_url='/login/')
def edit_participating_meeting_rnp_po_report(request, participating_id, task_id):
    heading = "Section 13: Edit of participating in meetings at district and block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    participating_meeting = ParticipatingMeeting.objects.get(id=participating_id)
    if request.method == 'POST':
        data = request.POST
        type_of_meeting = data.get('type_of_meeting')
        department = data.get('department')
        district_block_level = data.get('district_block_level')
        point_of_discussion = data.get('point_of_discussion')
        districit_level_officials = data.get('districit_level_officials')
        block_level = data.get('block_level')
        cluster_level = data.get('cluster_level')
        no_of_pri = data.get('no_of_pri')
        no_of_others = data.get('no_of_others')
        date = data.get('date')
        task = Task.objects.get(id=task_id)

        participating_meeting.user_name = request.user
        participating_meeting.type_of_meeting = type_of_meeting
        participating_meeting.district_block_level = district_block_level
        participating_meeting.department = department
        participating_meeting.point_of_discussion = point_of_discussion
        participating_meeting.districit_level_officials = districit_level_officials
        participating_meeting.block_level = block_level
        participating_meeting.cluster_level = cluster_level
        participating_meeting.no_of_pri = no_of_pri
        participating_meeting.no_of_others = no_of_others
        participating_meeting.date = date
        participating_meeting.task_id = task
        participating_meeting.site_id =  current_site
        participating_meeting.save()
        return redirect('/po-report/rnp/participating-meeting-listing/'+str(task_id))
    return render(request, 'po_report/rnp/participating_meeting/edit_participating_meeting.html', locals())


@ login_required(login_url='/login/')
def faced_related_listing_rnp_po_report(request, task_id):
    heading = "Section 15: Details of faced related"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    faced_related = FacedRelatedOperation.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, faced_related)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/rnp/faced_related/faced_related_listing.html', locals())

@ login_required(login_url='/login/')
def add_faced_related_rnp_po_report(request, task_id):
    heading = "Section 15: Add of faced related"
    current_site = request.session.get('site_id')
    faced_related = FacedRelatedOperation.objects.filter()
    if request.method == 'POST':
        data = request.POST
        challenges = data.get('challenges')
        proposed_solution = data.get('proposed_solution')
        task = Task.objects.get(id=task_id)

        if FacedRelatedOperation.objects.filter(Q(challenges__isnull=challenges) & Q(proposed_solution__isnull=proposed_solution)).exists():
            return redirect('/po-report/rnp/faced-related-listing/'+str(task_id))
        else:
            faced_related = FacedRelatedOperation.objects.create(user_name=request.user, challenges=challenges,
            proposed_solution=proposed_solution, task=task, site_id = current_site)
            faced_related.save()
        return redirect('/po-report/rnp/faced-related-listing/'+str(task_id))
    return render(request, 'po_report/rnp/faced_related/add_faced_related.html', locals())


@ login_required(login_url='/login/')
def edit_faced_related_rnp_po_report(request, faced_related_id, task_id):
    heading = "Section 15: Edit of faced related"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    faced_related = FacedRelatedOperation.objects.get(id=faced_related_id)
    if request.method == 'POST':
        data = request.POST
        challenges = data.get('challenges')
        proposed_solution = data.get('proposed_solution')
        task = Task.objects.get(id=task_id)

        if FacedRelatedOperation.objects.filter(Q(challenges__isnull=challenges) & Q(proposed_solution__isnull=proposed_solution)).exists():
            return redirect('/po-report/fossil/faced-related-listing/'+str(task_id))
        else:
            faced_related.user_name = request.user
            faced_related.challenges = challenges
            faced_related.proposed_solution = proposed_solution
            faced_related.task_id = task
            faced_related.site_id =  current_site
            faced_related.save()
        return redirect('/po-report/rnp/faced-related-listing/'+str(task_id))
    return render(request, 'po_report/rnp/faced_related/edit_faced_related.html', locals())


#--- ---------po-report-un-trust--------------

@ login_required(login_url='/login/')
def health_sessions_listing_untrust_po_report(request, task_id):
    heading = "Section 1: Details of transaction of sessions on health & nutrition"
    # awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, health_sessions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/health_sessions/health_sessions_listing.html', locals())

@ login_required(login_url='/login/')
def add_health_sessions_untrust_po_report(request, task_id):
    heading = "Section 1: Add of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1)
  
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_selected_id = data.get('awc_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id,)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session_selected_id = data.get('fossil_ah_session_category')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        adolescent_obj =  Adolescent.objects.filter(awc__id=adolescent_selected_id)
        fossil_ah_session_obj =  FossilAHSession.objects.filter(fossil_ah_session_category__id = fossil_ah_session_selected_id)
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'po_report/untrust/health_sessions/add_health_sessions.html', locals())
        else:
            health_sessions = AHSession.objects.create(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
            date_of_session=date_of_session, session_day=session_day,designation_data = designations,
            age=age, gender=gender, facilitator_name = facilitator_name, task=task, site_id = current_site)
            health_sessions.save()
        return redirect('/po-report/untrust/health-sessions-listing/'+str(task_id))
    return render(request, 'po_report/untrust/health_sessions/add_health_sessions.html', locals())


@ login_required(login_url='/login/')
def edit_health_sessions_untrust_po_report(request, ahsession_id, task_id):
    heading = "Section 1: Edit of transaction of sessions on health & nutrition"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    health_sessions = AHSession.objects.get(id=ahsession_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id=health_sessions.adolescent_name.awc.id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    fossil_ah_session_obj =  FossilAHSession.objects.filter(status=1, fossil_ah_session_category__id=health_sessions.fossil_ah_session.fossil_ah_session_category.id)
    fossil_ah_session_category_obj =  FossilAHSessionCategory.objects.filter(status=1,)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        fossil_ah_session_id = data.get('fossil_ah_session')
        fossil_ah_session = FossilAHSession.objects.get(id=fossil_ah_session_id)
        date_of_session = data.get('date_of_session')
        session_day = data.get('session_day')
        age = data.get('age')
        gender = data.get('gender')
        facilitator_name = data.get('facilitator_name')
        designations = data.get('designations')
        task = Task.objects.get(id=task_id)
        if AHSession.objects.filter(adolescent_name=adolescent_name, fossil_ah_session=fossil_ah_session,
                                    date_of_session=date_of_session,  status=1).exclude(id=ahsession_id).exists():
            exist_error = "Please try again this data already exists!!!"
            return render(request,'po_report/untrust/health_sessions/edit_health_sessions.html', locals())
        else:
            health_sessions.adolescent_name_id = adolescent_name
            health_sessions.fossil_ah_session_id = fossil_ah_session
            health_sessions.date_of_session = date_of_session
            health_sessions.age = age
            health_sessions.gender = gender
            health_sessions.session_day = session_day
            health_sessions.designation_data = designations
            health_sessions.facilitator_name = facilitator_name
            health_sessions.task_id = task
            health_sessions.site_id =  current_site
            health_sessions.save()
        return redirect('/po-report/untrust/health-sessions-listing/'+str(task_id))
    return render(request, 'po_report/untrust/health_sessions/edit_health_sessions.html', locals())


@ login_required(login_url='/login/')
def girls_ahwd_listing_untrust_po_report(request, task_id):
    heading = "Section 3(a): Details of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, girls_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/girls_ahwd/girls_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_girls_ahwd_untrust_po_report(request, task_id):
    heading = "Section 3(a): Add of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd = GirlsAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        tt_10_14_years=tt_10_14_years, tt_15_19_years=tt_15_19_years, counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        girls_ahwd.save()
        return redirect('/po-report/untrust/girls-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/untrust/girls_ahwd/add_girls_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_girls_ahwd_untrust_po_report(request, girls_ahwd_id, task_id):
    heading = "Section 3(a): Edit of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    girls_ahwd = GirlsAHWD.objects.get(id=girls_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        tt_10_14_years = data.get('tt_10_14_years')
        tt_15_19_years = data.get('tt_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        girls_ahwd.place_of_ahwd = place_of_ahwd
        girls_ahwd.content_type = content_type
        girls_ahwd.object_id = selected_object_id
        girls_ahwd.hwc_name = hwc_name
        girls_ahwd.date_of_ahwd = date_of_ahwd
        girls_ahwd.participated_10_14_years = participated_10_14_years
        girls_ahwd.participated_15_19_years = participated_15_19_years
        girls_ahwd.bmi_10_14_years = bmi_10_14_years
        girls_ahwd.bmi_15_19_years = bmi_15_19_years
        girls_ahwd.hb_10_14_years = hb_10_14_years
        girls_ahwd.hb_15_19_years = hb_15_19_years
        girls_ahwd.tt_10_14_years = tt_10_14_years
        girls_ahwd.tt_15_19_years = tt_15_19_years
        girls_ahwd.counselling_10_14_years = counselling_10_14_years
        girls_ahwd.counselling_15_19_years = counselling_15_19_years
        girls_ahwd.referral_10_14_years = referral_10_14_years
        girls_ahwd.referral_15_19_years = referral_15_19_years
        girls_ahwd.task_id = task
        girls_ahwd.site_id =  current_site
        girls_ahwd.save()
        return redirect('/po-report/untrust/girls-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/untrust/girls_ahwd/edit_girls_ahwd.html', locals())




@ login_required(login_url='/login/')
def boys_ahwd_listing_untrust_po_report(request, task_id):
    heading = "Section 3(b): Details of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, boys_ahwd)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/boys_ahwd/boys_ahwd_listing.html', locals())


@ login_required(login_url='/login/')
def add_boys_ahwd_untrust_po_report(request, task_id):
    heading = "Section 3(b): Add of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd = BoysAHWD.objects.create(place_of_ahwd=place_of_ahwd, content_type=content_type, object_id=selected_object_id,
        participated_10_14_years=participated_10_14_years, date_of_ahwd=date_of_ahwd, hwc_name=hwc_name,
        participated_15_19_years=participated_15_19_years, bmi_10_14_years=bmi_10_14_years,
        bmi_15_19_years=bmi_15_19_years, hb_10_14_years=hb_10_14_years, hb_15_19_years=hb_15_19_years,
        counselling_10_14_years=counselling_10_14_years,
        counselling_15_19_years=counselling_15_19_years, referral_10_14_years=referral_10_14_years,
        referral_15_19_years=referral_15_19_years, task=task, site_id = current_site)
        boys_ahwd.save()
        return redirect('/po-report/untrust/boys-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/untrust/boys_ahwd/add_boys_ahwd.html', locals())


@ login_required(login_url='/login/')
def edit_boys_ahwd_untrust_po_report(request, boys_ahwd_id, task_id):
    heading = "Section 3(b): Edit of participation of adolescent boys in Adolescent Health Wellness Day (AHWD)"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    boys_ahwd = BoysAHWD.objects.get(id=boys_ahwd_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id)
    school_obj = School.objects.filter(status=1, id__in=school_id)
    if request.method == 'POST':
        data = request.POST
        place_of_ahwd = data.get('place_of_ahwd')
        if place_of_ahwd == '1':
            selected_object_id=data.get('selected_field_awc')
            content_type_model='awc'
            hwc_name = None
        elif place_of_ahwd == '2':
            selected_object_id=data.get('selected_field_school')
            content_type_model='school'
            hwc_name = None
        else:
            selected_object_id = None
            content_type_model = None
            hwc_name = data.get('hwc_name')
       
        content_type = ContentType.objects.get(model=content_type_model) if content_type_model != None else None
        date_of_ahwd = data.get('date_of_ahwd')
        participated_10_14_years = data.get('participated_10_14_years')
        participated_15_19_years = data.get('participated_15_19_years')
        bmi_10_14_years = data.get('bmi_10_14_years')
        bmi_15_19_years = data.get('bmi_15_19_years')
        hb_10_14_years = data.get('hb_10_14_years')
        hb_15_19_years = data.get('hb_15_19_years')
        counselling_10_14_years = data.get('counselling_10_14_years')
        counselling_15_19_years = data.get('counselling_15_19_years')
        referral_10_14_years = data.get('referral_10_14_years')
        referral_15_19_years = data.get('referral_15_19_years')
        task = Task.objects.get(id=task_id)

        boys_ahwd.place_of_ahwd = place_of_ahwd
        boys_ahwd.content_type = content_type
        boys_ahwd.object_id = selected_object_id
        boys_ahwd.hwc_name = hwc_name
        boys_ahwd.hwc_name = hwc_name
        boys_ahwd.date_of_ahwd = date_of_ahwd
        boys_ahwd.participated_10_14_years = participated_10_14_years
        boys_ahwd.participated_15_19_years = participated_15_19_years
        boys_ahwd.bmi_10_14_years = bmi_10_14_years
        boys_ahwd.bmi_15_19_years = bmi_15_19_years
        boys_ahwd.hb_10_14_years = hb_10_14_years
        boys_ahwd.hb_15_19_years = hb_15_19_years
        boys_ahwd.counselling_10_14_years = counselling_10_14_years
        boys_ahwd.counselling_15_19_years = counselling_15_19_years
        boys_ahwd.referral_10_14_years = referral_10_14_years
        boys_ahwd.referral_15_19_years = referral_15_19_years
        boys_ahwd.task_id = task
        boys_ahwd.site_id =  current_site
        boys_ahwd.save()
        return redirect('/po-report/untrust/boys-ahwd-listing/'+str(task_id))
    return render(request, 'po_report/untrust/boys_ahwd/edit_boys_ahwd.html', locals())




@ login_required(login_url='/login/')
def vocation_listing_untrust_po_report(request, task_id):
    heading = "Section 2(a): Details of adolescent linked with vocational training & placement"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj = AdolescentVocationalTraining.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, vocation_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_vocation_untrust_po_report(request, task_id):
    heading = "Section 2(a): Add of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id=training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        vocation_obj = AdolescentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age, parent_guardian_name=parent_guardian_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered or None, placement_accepted=placement_accepted or None, type_of_employment=type_of_employment or None,
        task=task, site_id = current_site)
        vocation_obj.save()
        return redirect('/po-report/untrust/vocation-listing/'+str(task_id))
    return render(request, 'po_report/untrust/voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_vocation_untrust_po_report(request, vocation_id, task_id):
    heading = "Section 2(a): Edit of adolescent linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vocation_obj =  AdolescentVocationalTraining.objects.get(id=vocation_id)
    adolescent_obj =  Adolescent.objects.filter(awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.all()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)

        vocation_obj.adolescent_name_id = adolescent_name
        vocation_obj.date_of_registration = date_of_registration
        vocation_obj.age = age
        vocation_obj.parent_guardian_name = parent_guardian_name
        vocation_obj.training_subject = training_subject
        vocation_obj.training_providing_by = training_providing_by
        vocation_obj.duration_days = duration_days
        vocation_obj.training_complated = training_complated
        vocation_obj.placement_offered = placement_offered or None
        vocation_obj.placement_accepted = placement_accepted or None
        vocation_obj.type_of_employment = type_of_employment or None
        vocation_obj.task_id = task
        vocation_obj.site_id =  current_site
        vocation_obj.save()
        return redirect('/po-report/untrust/vocation-listing/'+str(task_id))
    return render(request, 'po_report/untrust/voctional_training/edit_vocation_training.html', locals())

@ login_required(login_url='/login/')
def parents_vocation_listing_untrust_po_report(request, task_id):
    heading = "Section 2(b): Details of parents linked with vocational training & placement"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    parents_vocation =  ParentVocationalTraining.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, parents_vocation)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/parents_voctional_training/vocation_listing.html', locals())

@ login_required(login_url='/login/')
def add_parents_vocation_untrust_po_report(request, task_id):
    heading = "Section 2(b): Edit of parents linked with vocational training & placement"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    parents_vocation =  ParentVocationalTraining.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.filter(status=1, )

    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_name = data.get('parent_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)
        parents_vocation = ParentVocationalTraining.objects.create(adolescent_name=adolescent_name, date_of_registration=date_of_registration, 
        age=age, parent_name=parent_name, training_subject=training_subject,
        training_providing_by=training_providing_by, duration_days=duration_days, training_complated=training_complated, 
        placement_offered=placement_offered  or None, placement_accepted=placement_accepted  or None, type_of_employment=type_of_employment  or None,
        task=task, site_id = current_site)
        parents_vocation.save()
        return redirect('/po-report/untrust/parents-vocation-listing/'+str(task_id))
    return render(request, 'po_report/untrust/parents_voctional_training/add_vocation_training.html', locals())


@ login_required(login_url='/login/')
def edit_parents_vocation_untrust_po_report(request, parent_id, task_id):
    current_site = request.session.get('site_id')
    heading = "Section 2(b): Edit of parents linked with vocational training & placement"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    parents_vocation =  ParentVocationalTraining.objects.get(id=parent_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    tranining_sub_obj = TrainingSubject.objects.filter(status=1)

    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        date_of_registration = data.get('date_of_registration')
        age = data.get('age')
        parent_name = data.get('parent_name')
        training_subject_id = data.get('training_subject')
        training_subject = TrainingSubject.objects.get(id = training_subject_id)
        training_providing_by = data.get('training_providing_by')
        duration_days = data.get('duration_days')
        training_complated = data.get('training_complated')
        placement_offered = data.get('placement_offered')
        placement_accepted = data.get('placement_accepted')
        type_of_employment = data.get('type_of_employment')
        task = Task.objects.get(id=task_id)

        parents_vocation.adolescent_name_id = adolescent_name
        parents_vocation.date_of_registration = date_of_registration
        parents_vocation.age = age
        parents_vocation.parent_name = parent_name
        parents_vocation.training_subject = training_subject
        parents_vocation.training_providing_by = training_providing_by
        parents_vocation.duration_days = duration_days
        parents_vocation.training_complated = training_complated
        parents_vocation.placement_offered = placement_offered  or None
        parents_vocation.placement_accepted = placement_accepted  or None
        parents_vocation.type_of_employment = type_of_employment  or None
        parents_vocation.task_id = task
        parents_vocation.site_id =  current_site
        parents_vocation.save()
        return redirect('/po-report/untrust/parents-vocation-listing/'+str(task_id))
    return render(request, 'po_report/untrust/parents_voctional_training/edit_vocation_training.html', locals())

@ login_required(login_url='/login/')
def adolescents_referred_listing_untrust_po_report(request, task_id):
    heading = "Section 4: Details of adolescents referred"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, adolescents_referred)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/adolescent_referred/adolescent_referred_listing.html', locals())

@ login_required(login_url='/login/')
def add_adolescents_referred_untrust_po_report(request, task_id):
    heading = "Section 4: Add of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')
        
        task = Task.objects.get(id=task_id)
        adolescents_referred = AdolescentsReferred.objects.create(awc_name=awc_name, girls_referred_10_14_year=girls_referred_10_14_year, 
        girls_referred_15_19_year=girls_referred_15_19_year, boys_referred_10_14_year=boys_referred_10_14_year, boys_referred_15_19_year=boys_referred_15_19_year,
        girls_hwc_referred=girls_hwc_referred, girls_hwc_visited=girls_hwc_visited, girls_afhc_referred=girls_afhc_referred, girls_afhc_visited=girls_afhc_visited,
        girls_dh_referred=girls_dh_referred, girls_dh_visited=girls_dh_visited, boys_hwc_referred=boys_hwc_referred, boys_hwc_visited=boys_hwc_visited,
        boys_afhc_referred=boys_afhc_referred, boys_afhc_visited=boys_afhc_visited, 
        boys_dh_referred=boys_dh_referred, boys_dh_visited=boys_dh_visited, task=task, site_id = current_site)
        adolescents_referred.save()
        return redirect('/po-report/untrust/adolescent-referred-listing/'+str(task_id))
    return render(request, 'po_report/untrust/adolescent_referred/add_adolescen_referred.html', locals())


@ login_required(login_url='/login/')
def edit_adolescents_referred_untrust_po_report(request, adolescents_referred_id, task_id):
    heading = "Section 4: Edit of adolescents referred"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescents_referred =  AdolescentsReferred.objects.get(id=adolescents_referred_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_referred_10_14_year = data.get('girls_referred_10_14_year')
        girls_referred_15_19_year = data.get('girls_referred_15_19_year')
        boys_referred_10_14_year = data.get('boys_referred_10_14_year')
        boys_referred_15_19_year = data.get('boys_referred_15_19_year')
        girls_hwc_referred = data.get('girls_hwc_referred')
        girls_hwc_visited = data.get('girls_hwc_visited')
        girls_afhc_referred = data.get('girls_afhc_referred')
        girls_afhc_visited = data.get('girls_afhc_visited')
        girls_dh_referred = data.get('girls_dh_referred')
        girls_dh_visited = data.get('girls_dh_visited')
        boys_hwc_referred = data.get('boys_hwc_referred')
        boys_hwc_visited = data.get('boys_hwc_visited')
        boys_afhc_referred = data.get('boys_afhc_referred')
        boys_afhc_visited = data.get('boys_afhc_visited')
        boys_dh_referred = data.get('boys_dh_referred')
        boys_dh_visited = data.get('boys_dh_visited')  
        task = Task.objects.get(id=task_id)

        adolescents_referred.awc_name_id = awc_name
        adolescents_referred.girls_referred_10_14_year = girls_referred_10_14_year
        adolescents_referred.girls_referred_15_19_year = girls_referred_15_19_year
        adolescents_referred.boys_referred_10_14_year = boys_referred_10_14_year
        adolescents_referred.boys_referred_15_19_year = boys_referred_15_19_year
        adolescents_referred.girls_hwc_referred = girls_hwc_referred
        adolescents_referred.girls_hwc_visited = girls_hwc_visited
        adolescents_referred.girls_afhc_referred = girls_afhc_referred
        adolescents_referred.girls_afhc_visited = girls_afhc_visited
        adolescents_referred.girls_dh_referred = girls_dh_referred
        adolescents_referred.girls_dh_visited = girls_dh_visited
        adolescents_referred.boys_hwc_referred = boys_hwc_referred
        adolescents_referred.boys_hwc_visited = boys_hwc_visited
        adolescents_referred.boys_afhc_referred = boys_afhc_referred
        adolescents_referred.boys_afhc_visited = boys_afhc_visited
        adolescents_referred.boys_dh_referred = boys_dh_referred
        adolescents_referred.boys_dh_visited = boys_dh_visited
        adolescents_referred.task_id = task
        adolescents_referred.site_id =  current_site
        adolescents_referred.save()
        return redirect('/po-report/untrust/adolescent-referred-listing/'+str(task_id))
    return render(request, 'po_report/untrust/adolescent_referred/edit_adolescent_referred.html', locals())


@ login_required(login_url='/login/')
def friendly_club_listing_untrust_po_report(request, task_id):
    heading = "Section 5: Details of Adolescent Friendly Club (AFC)"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(task__id = task_id)
    data = pagination_function(request, friendly_club)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/friendly_club/friendly_club_listing.html', locals())

@ login_required(login_url='/login/')
def add_friendly_club_untrust_po_report(request, task_id):
    heading = "Section 5: Add of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1)
    gramapanchayat = GramaPanchayat.objects.filter(status=1)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club = AdolescentFriendlyClub.objects.create(start_date = date_of_registration, panchayat_name=panchayat_name,
        hsc_name=hsc_name, subject=subject, facilitator=facilitator, designation=designation,
        no_of_sahiya=no_of_sahiya, no_of_aww=no_of_aww, pe_girls_10_14_year=pe_girls_10_14_year,
        pe_girls_15_19_year=pe_girls_15_19_year, pe_boys_10_14_year=pe_boys_10_14_year,
        pe_boys_15_19_year=pe_boys_15_19_year, task=task, site_id = current_site)
        friendly_club.save()
        return redirect('/cc-report/untrust/friendly-club-listing/'+str(task_id))
    return render(request, 'cc_report/untrust/friendly_club/add_friendly_club.html', locals())



@ login_required(login_url='/login/')
def edit_friendly_club_untrust_po_report(request, friendly_club_id, task_id):
    heading = "Section 5: Edit of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    friendly_club =  AdolescentFriendlyClub.objects.get(id=friendly_club_id)
    gramapanchayat = GramaPanchayat.objects.filter(status=1)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club.start_date = date_of_registration
        friendly_club.panchayat_name_id = panchayat_name
        friendly_club.hsc_name = hsc_name
        friendly_club.subject = subject
        friendly_club.facilitator = facilitator
        friendly_club.designation = designation
        friendly_club.no_of_sahiya = no_of_sahiya
        friendly_club.no_of_aww = no_of_aww
        friendly_club.pe_girls_10_14_year = pe_girls_10_14_year
        friendly_club.pe_girls_15_19_year = pe_girls_15_19_year
        friendly_club.pe_boys_10_14_year = pe_boys_10_14_year
        friendly_club.pe_boys_15_19_year = pe_boys_15_19_year
        friendly_club.task_id = task
        friendly_club.site_id =  current_site
        friendly_club.save()
        return redirect('/po-report/untrust/friendly-club-listing/'+str(task_id))
    return render(request, 'po_report/untrust/friendly_club/edit_friendly_club.html', locals())

@ login_required(login_url='/login/')
def balsansad_meeting_listing_untrust_po_report(request, task_id):
    heading = "Section 6: Details of Bal Sansad meetings conducted"
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter(status=1, school_name__id__in=school_id, task__id = task_id)
    data = pagination_function(request, balsansad_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/bal_sansad_metting/bal_sansad_listing.html', locals())

@ login_required(login_url='/login/')
def add_balsansad_meeting_untrust_po_report(request, task_id):
    heading = "Section 6: Add of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.filter()
    school = School.objects.filter(status=1, id__in=school_id)
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        decision_taken = data.get('decision_taken')
        issues_discussion = data.get('issues_discussion')
        task = Task.objects.get(id=task_id)
        balsansad_meeting = BalSansadMeeting.objects.create(start_date = date_of_registration, school_name=school_name,
        no_of_participants=no_of_participants, decision_taken=decision_taken,
        task=task, site_id = current_site)
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/po-report/untrust/balsansad-listing/'+str(task_id))
    return render(request, 'po_report/untrust/bal_sansad_metting/add_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def edit_balsansad_meeting_untrust_po_report(request, balsansad_id, task_id):
    heading = "Section 6: Edit of Bal Sansad meetings conducted"
    current_site = request.session.get('site_id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    balsansad_meeting =  BalSansadMeeting.objects.get(id=balsansad_id)
    school = School.objects.filter(status=1, id__in=school_id)
    masterlookups_issues_discussion = MasterLookUp.objects.filter(parent__slug = 'issues_discussion')

    if request.method == 'POST':
        data = request.POST
        school_name_id = data.get('school_name')
        school_name = School.objects.get(id=school_name_id)
        no_of_participants = data.get('no_of_participants')
        issues_discussion = data.get('issues_discussion')
        decision_taken = data.get('decision_taken')
        task = Task.objects.get(id=task_id)
        balsansad_meeting.school_name_id = school_name
        balsansad_meeting.no_of_participants = no_of_participants
        balsansad_meeting.decision_taken = decision_taken
        balsansad_meeting.task_id = task
        balsansad_meeting.site_id =  current_site
        if issues_discussion:
            issues_discussion = MasterLookUp.objects.get(id=issues_discussion)
            balsansad_meeting.issues_discussion = issues_discussion
        balsansad_meeting.save()
        return redirect('/po-report/untrust/balsansad-listing/'+str(task_id))
    return render(request, 'po_report/untrust/bal_sansad_metting/edit_bal_sansad.html', locals())


@ login_required(login_url='/login/')
def friendly_club_listing_untrust_po_report(request, task_id):
    heading = "Section 6: Details of Adolescent Friendly Club (AFC)"
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1, panchayat_name__id__in=panchayat_id, task__id = task_id)
    data = pagination_function(request, friendly_club)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/friendly_club/friendly_club_listing.html', locals())

@ login_required(login_url='/login/')
def add_friendly_club_untrust_po_report(request, task_id):
    heading = "Section 6: Add of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.filter(status=1)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club = AdolescentFriendlyClub.objects.create(start_date = date_of_registration, panchayat_name=panchayat_name,
        hsc_name=hsc_name, subject=subject, facilitator=facilitator, designation=designation,
        no_of_sahiya=no_of_sahiya, no_of_aww=no_of_aww, pe_girls_10_14_year=pe_girls_10_14_year,
        pe_girls_15_19_year=pe_girls_15_19_year, pe_boys_10_14_year=pe_boys_10_14_year,
        pe_boys_15_19_year=pe_boys_15_19_year, task=task, site_id = current_site)
        friendly_club.save()
        return redirect('/po-report/untrust/friendly-club-listing/'+str(task_id))
    return render(request, 'po_report/untrust/friendly_club/add_friendly_club.html', locals())



@ login_required(login_url='/login/')
def edit_friendly_club_untrust_po_report(request, friendly_club_id, task_id):
    heading = "Section 6: Details of Adolescent Friendly Club (AFC)"
    current_site = request.session.get('site_id')
    panchayat_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__id')
    friendly_club =  AdolescentFriendlyClub.objects.get(id=friendly_club_id)
    gramapanchayat = GramaPanchayat.objects.filter(status=1, id__in=panchayat_id)
    if request.method == 'POST':
        data = request.POST
        date_of_registration = data.get('date_of_registration')
        panchayat_name_id = data.get('panchayat_name')
        panchayat_name = GramaPanchayat.objects.get(id=panchayat_name_id)
        hsc_name = data.get('hsc_name')
        subject = data.get('subject')
        facilitator = data.get('facilitator')
        designation = data.get('designation')
        no_of_sahiya = data.get('no_of_sahiya')
        no_of_aww = data.get('no_of_aww')
        pe_girls_10_14_year = data.get('pe_girls_10_14_year')
        pe_girls_15_19_year = data.get('pe_girls_15_19_year')
        pe_boys_10_14_year = data.get('pe_boys_10_14_year')
        pe_boys_15_19_year = data.get('pe_boys_15_19_year')
        task = Task.objects.get(id=task_id)

        friendly_club.start_date = date_of_registration
        friendly_club.panchayat_name_id = panchayat_name
        friendly_club.hsc_name = hsc_name
        friendly_club.subject = subject
        friendly_club.facilitator = facilitator
        friendly_club.designation = designation
        friendly_club.no_of_sahiya = no_of_sahiya
        friendly_club.no_of_aww = no_of_aww
        friendly_club.pe_girls_10_14_year = pe_girls_10_14_year
        friendly_club.pe_girls_15_19_year = pe_girls_15_19_year
        friendly_club.pe_boys_10_14_year = pe_boys_10_14_year
        friendly_club.pe_boys_15_19_year = pe_boys_15_19_year
        friendly_club.task_id = task
        friendly_club.site_id =  current_site
        friendly_club.save()
        return redirect('/po-report/untrust/friendly-club-listing/'+str(task_id))
    return render(request, 'po_report/untrust/friendly_club/edit_friendly_club.html', locals())


@ login_required(login_url='/login/')
def community_activities_listing_untrust_po_report(request, task_id):
    heading = "Section 7: Details of community engagement activities"
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1, village_name__id__in=village_id, task__id = task_id)
    data = pagination_function(request, activities)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/community_activities/community_activities_listing.html', locals())


@ login_required(login_url='/login/')
def add_community_activities_untrust_po_report(request, task_id):
    heading = "Section 7: Add of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.filter(status=1,)
    village =  Village.objects.filter(status=1, id__in=village_id)

    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')
        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities =  CommunityEngagementActivities.objects.create(village_name=village_name, start_date = date_of_registration,
        name_of_event_activity=name_of_event_activity, organized_by=organized_by,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year, adult_male=adult_male,
        adult_female=adult_female, teachers=teachers, pri_members=pri_members, services_providers=services_providers,
        sms_members=sms_members, other=other, task=task, site_id = current_site)
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/po-report/untrust/community-activities-listing/'+str(task_id))
    return render(request, 'po_report/untrust/community_activities/add_community_activities.html', locals())


@ login_required(login_url='/login/')
def edit_community_activities_untrust_po_report(request, activities_id, task_id):
    heading = "Section 7: Edit of community engagement activities"
    current_site = request.session.get('site_id')
    village_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    activities =  CommunityEngagementActivities.objects.get(id=activities_id)
    village =  Village.objects.filter(status=1, id__in=village_id)
    masterlookups_event = MasterLookUp.objects.filter(parent__slug = 'event')
    masterlookups_activity = MasterLookUp.objects.filter(parent__slug = 'activities')

    if request.method == 'POST':
        data = request.POST
        village_name_id = data.get('village_name')
        date_of_registration = data.get('date_of_registration')
        village_name = Village.objects.get(id=village_name_id)
        name_of_event_activity = data.get('name_of_event_activity')
        # theme_topic = data.get('theme_topic')
        name_of_event_id = data.get('name_of_event')
        name_of_activity_id = data.get('name_of_activity')

        organized_by = data.get('organized_by')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)

        activities.start_date = date_of_registration
        activities.village_name_id = village_name
        activities.name_of_event_activity = name_of_event_activity
        # activities.theme_topic = theme_topic
        activities.organized_by = organized_by
        activities.boys_10_14_year = boys_10_14_year
        activities.boys_15_19_year = boys_15_19_year
        activities.girls_10_14_year = girls_10_14_year
        activities.girls_15_19_year = girls_15_19_year
        activities.champions_15_19_year = champions_15_19_year
        activities.adult_male = adult_male
        activities.adult_female = adult_female
        activities.teachers = teachers
        activities.pri_members = pri_members
        activities.services_providers = services_providers
        activities.sms_members = sms_members
        activities.other = other
        activities.task_id = task
        activities.site_id =  current_site
        
        if name_of_event_id:
            name_of_event = MasterLookUp.objects.get(id = name_of_event_id)
            activities.event_name = name_of_event

        if name_of_activity_id:
            name_of_activity = MasterLookUp.objects.get(id = name_of_activity_id)
            activities.activity_name = name_of_activity
        activities.save()
        return redirect('/po-report/untrust/community-activities-listing/'+str(task_id))
    return render(request, 'po_report/untrust/community_activities/edit_community_activities.html', locals())

@ login_required(login_url='/login/')
def champions_listing_untrust_po_report(request, task_id):
    heading = "Section 8: Details of exposure visits of adolescent champions"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, champions)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/champions/champions_listing.html', locals())




@ login_required(login_url='/login/')
def add_champions_untrust_po_report(request, task_id):
    heading = "Section 8: Add of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions =  Champions.objects.create(awc_name=awc_name, date_of_visit=date_of_visit, girls_10_14_year=girls_10_14_year,
        girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year, boys_15_19_year=boys_15_19_year,
        first_inst_visited=first_inst_visited,second_inst_visited=second_inst_visited or None,
        third_inst_visited=third_inst_visited or None, fourth_inst_visited=fourth_inst_visited or None, task=task, site_id = current_site)
        champions.save()
        return redirect('/po-report/untrust/champions-listing/'+str(task_id))
    return render(request, 'po_report/untrust/champions/add_champions.html', locals())


@ login_required(login_url='/login/')
def edit_champions_untrust_po_report(request, champions_id, task_id):
    heading = "Section 8: Edit of exposure visits of adolescent champions"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    champions =  Champions.objects.get(id=champions_id)
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        date_of_visit = data.get('date_of_visit')
        awc_name = AWC.objects.get(id=awc_name_id)
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        first_inst_visited = data.get('first_inst_visited')
        second_inst_visited = data.get('second_inst_visited')
        third_inst_visited = data.get('third_inst_visited')
        fourth_inst_visited = data.get('fourth_inst_visited')
        task = Task.objects.get(id=task_id)

        champions.awc_name_id = awc_name   
        champions.date_of_visit = date_of_visit     
        champions.girls_10_14_year = girls_10_14_year       
        champions.girls_15_19_year = girls_15_19_year     
        champions.boys_10_14_year = boys_10_14_year       
        champions.boys_15_19_year = boys_15_19_year       
        champions.first_inst_visited = first_inst_visited
        champions.second_inst_visited= second_inst_visited or None
        champions.third_inst_visited = third_inst_visited or None
        champions.fourth_inst_visited = fourth_inst_visited or None
        champions.task_id = task
        champions.site_id =  current_site       
        champions.save()
        return redirect('/po-report/untrust/champions-listing/'+str(task_id))
    return render(request, 'po_report/untrust/champions/edit_champions.html', locals())

@ login_required(login_url='/login/')
def reenrolled_listing_untrust_po_report(request, task_id):
    heading = "Section 9: Details of adolescent re-enrolled in schools"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, adolescent_reenrolled)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/re_enrolled/re_enrolled_listing.html', locals())

@ login_required(login_url='/login/')
def add_reenrolled_untrust_po_report(request, task_id):
    heading = "Section 9: Add of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.filter()
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    # school = School.objects.filter(status=1, id__in = school_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled =  AdolescentRe_enrolled.objects.create(adolescent_name=adolescent_name,
        gender=gender, age=age, parent_guardian_name=parent_guardian_name, school_name=school_name, which_class_enrolled=which_class_enrolled,
        task=task, site_id = current_site)
        adolescent_reenrolled.save()
        return redirect('/po-report/untrust/reenrolled-listing/'+str(task_id))
    return render(request, 'po_report/untrust/re_enrolled/add_re_enrolled.html', locals())


@ login_required(login_url='/login/')
def edit_reenrolled_untrust_po_report(request, reenrolled_id, task_id):
    heading = "Section 9: Edit of adolescent re-enrolled in schools"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    adolescent_reenrolled =  AdolescentRe_enrolled.objects.get(id=reenrolled_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    # school = School.objects.filter()
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        gender = data.get('gender')
        age = data.get('age')
        parent_guardian_name = data.get('parent_guardian_name')
        school_name = data.get('school_name')
        # school_name = School.objects.get(id=school_name_id)
        which_class_enrolled = data.get('which_class_enrolled')
        task = Task.objects.get(id=task_id)

        adolescent_reenrolled.adolescent_name_id = adolescent_name
        adolescent_reenrolled.gender = gender
        adolescent_reenrolled.age = age
        adolescent_reenrolled.parent_guardian_name = parent_guardian_name
        adolescent_reenrolled.school_name = school_name
        adolescent_reenrolled.which_class_enrolled = which_class_enrolled
        adolescent_reenrolled.task_id = task
        adolescent_reenrolled.site_id =  current_site
        adolescent_reenrolled.save()
        return redirect('/po-report/untrust/reenrolled-listing/'+str(task_id))
    return render(request, 'po_report/untrust/re_enrolled/edit_re_enrolled.html', locals())

@ login_required(login_url='/login/')
def vlcpc_meeting_listing_untrust_po_report(request, task_id):
    heading = "Section 10: Details of VLCPC meetings"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vlcpc_metting =  VLCPCMetting.objects.filter(status=1, awc_name__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, vlcpc_metting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/vlcpc_meetings/vlcpc_meeting_listing.html', locals())

@ login_required(login_url='/login/')
def add_vlcpc_meeting_untrust_po_report(request, task_id):
    heading = "Section 10: Add of VLCPC meetings"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vlcpc_metting =  VLCPCMetting.objects.filter()
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        date_of_meeting = data.get('date_of_meeting')
        issues_discussed = data.get('issues_discussed')
        decision_taken = data.get('decision_taken')
        no_of_participants_planned = data.get('no_of_participants_planned')
        no_of_participants_attended = data.get('no_of_participants_attended')
        task = Task.objects.get(id=task_id)

        vlcpc_metting = VLCPCMetting.objects.create(awc_name=awc_name, date_of_meeting=date_of_meeting,
        issues_discussed=issues_discussed, decision_taken=decision_taken, no_of_participants_planned=no_of_participants_planned,
        no_of_participants_attended=no_of_participants_attended, task=task, site_id = current_site)
        vlcpc_metting.save()
        return redirect('/po-report/untrust/vlcpc-meeting-listing/'+str(task_id))
    return render(request, 'po_report/untrust/vlcpc_meetings/add_vlcpc_meeting.html', locals())


@ login_required(login_url='/login/')
def edit_vlcpc_meeting_untrust_po_report(request, vlcpc_metting, task_id):
    heading = "Section 10: Edit of VLCPC meetings"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    vlcpc_metting =  VLCPCMetting.objects.get(id=vlcpc_metting)
    awc =  AWC.objects.filter(status=1, id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        awc_name_id = data.get('awc_name')
        awc_name = AWC.objects.get(id=awc_name_id)
        date_of_meeting = data.get('date_of_meeting')
        issues_discussed = data.get('issues_discussed')
        decision_taken = data.get('decision_taken')
        no_of_participants_planned = data.get('no_of_participants_planned')
        no_of_participants_attended = data.get('no_of_participants_attended')
        task = Task.objects.get(id=task_id)

        vlcpc_metting.awc_name_id = awc_name
        vlcpc_metting.date_of_meeting = date_of_meeting
        vlcpc_metting.issues_discussed = issues_discussed
        vlcpc_metting.decision_taken = decision_taken
        vlcpc_metting.no_of_participants_planned = no_of_participants_planned
        vlcpc_metting.no_of_participants_attended = no_of_participants_attended
        vlcpc_metting.task_id = task
        vlcpc_metting.site_id =  current_site
        vlcpc_metting.save()
        return redirect('/po-report/untrust/vlcpc-meeting-listing/'+str(task_id))
    return render(request, 'po_report/untrust/vlcpc_meetings/edit_vlcpc_meeting.html', locals())


@ login_required(login_url='/login/')
def dcpu_bcpu_listing_untrust_po_report(request, task_id):
    heading = "Section 11: Details of DCPU/BCPU engagement at community and institutional level"
    block_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__block__id')
    dcpu_bcpu = DCPU_BCPU.objects.filter(status=1, block_name__id__in=block_id, task__id = task_id)
    data = pagination_function(request, dcpu_bcpu)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/dcpu_bcpu/dcpu_bcpu_listing.html', locals())

@ login_required(login_url='/login/')
def add_dcpu_bcpu_untrust_po_report(request, task_id):
    heading = "Section 11: Add of DCPU/BCPU engagement at community and institutional level"
    current_site = request.session.get('site_id')
    block_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__block__id')
    dcpu_bcpu = DCPU_BCPU.objects.filter(status=1)
    block_obj = Block.objects.filter(status=1, id__in=block_id)
    if request.method == 'POST':
        data = request.POST
        block_name_id = data.get('block_name')
        block_name = Block.objects.get(id=block_name_id)
        name_of_institution = data.get('name_of_institution')
        date_of_visit = data.get('date_of_visit')
        name_of_lead = data.get('name_of_lead')
        designation = data.get('designation')
        issues_discussed = data.get('issues_discussed')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)
        
        dcpu_bcpu = DCPU_BCPU.objects.create(block_name=block_name, name_of_institution=name_of_institution,
        date_of_visit=date_of_visit, name_of_lead=name_of_lead, designation=designation, issues_discussed=issues_discussed,
        girls_10_14_year=girls_10_14_year, girls_15_19_year=girls_15_19_year, boys_10_14_year=boys_10_14_year,
        boys_15_19_year=boys_15_19_year, champions_15_19_year=champions_15_19_year,
        adult_male=adult_male, adult_female=adult_female, teachers=teachers, pri_members=pri_members, 
        services_providers=services_providers, sms_members=sms_members, other=other,
        task=task, site_id = current_site)
        dcpu_bcpu.save()
        return redirect('/po-report/untrust/dcpu-bcpu-listing/'+str(task_id))
    return render(request, 'po_report/untrust/dcpu_bcpu/add_dcpu_bcpu.html', locals())



@ login_required(login_url='/login/')
def edit_dcpu_bcpu_untrust_po_report(request, dcpu_bcpu_id, task_id):
    heading = "Section 11: Edit of DCPU/BCPU engagement at community and institutional level"
    current_site = request.session.get('site_id')
    block_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__grama_panchayat__block__id')
    dcpu_bcpu = DCPU_BCPU.objects.get(id=dcpu_bcpu_id)
    block_obj = Block.objects.filter(status=1, id__in=block_id)
    if request.method == 'POST':
        data = request.POST
        block_name_id = data.get('block_name')
        block_name = Block.objects.get(id=block_name_id)
        name_of_institution = data.get('name_of_institution')
        date_of_visit = data.get('date_of_visit')
        name_of_lead = data.get('name_of_lead')
        designation = data.get('designation')
        issues_discussed = data.get('issues_discussed')
        girls_10_14_year = data.get('girls_10_14_year')
        girls_15_19_year = data.get('girls_15_19_year')
        boys_10_14_year = data.get('boys_10_14_year')
        boys_15_19_year = data.get('boys_15_19_year')
        champions_15_19_year = data.get('champions_15_19_year')
        adult_male = data.get('adult_male')
        adult_female = data.get('adult_female')
        teachers = data.get('teachers')
        pri_members = data.get('pri_members')
        services_providers = data.get('services_providers')
        sms_members = data.get('sms_members')
        other = data.get('other')
        task = Task.objects.get(id=task_id)


        dcpu_bcpu.block_name_id = block_name
        dcpu_bcpu.name_of_institution = name_of_institution 
        dcpu_bcpu.date_of_visit = date_of_visit 
        dcpu_bcpu.name_of_lead = name_of_lead 
        dcpu_bcpu.designation = designation 
        dcpu_bcpu.issues_discussed = issues_discussed 
        dcpu_bcpu.girls_10_14_year = girls_10_14_year 
        dcpu_bcpu.girls_15_19_year = girls_15_19_year 
        dcpu_bcpu.boys_10_14_year = boys_10_14_year 
        dcpu_bcpu.boys_15_19_year = boys_15_19_year 
        dcpu_bcpu.champions_15_19_year = champions_15_19_year 
        dcpu_bcpu.adult_male = adult_male 
        dcpu_bcpu.adult_female = adult_female 
        dcpu_bcpu.teachers = teachers 
        dcpu_bcpu.pri_members = pri_members 
        dcpu_bcpu.services_providers = services_providers 
        dcpu_bcpu.sms_members = sms_members 
        dcpu_bcpu.other = other 
        dcpu_bcpu.task_id = task 
        dcpu_bcpu.site_id =  current_site 
        dcpu_bcpu.save()
        return redirect('/po-report/untrust/dcpu-bcpu-listing/'+str(task_id))
    return render(request, 'po_report/untrust/dcpu_bcpu/edit_dcpu_bcpu.html', locals())


@ login_required(login_url='/login/')
def educational_enrichment_listing_untrust_po_report(request, task_id):
    heading = "Section 12: Details of educational enrichment support provided"
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    education_enrichment =  EducatinalEnrichmentSupportProvided.objects.filter(status=1, adolescent_name__awc__id__in=awc_id, task__id = task_id)
    data = pagination_function(request, education_enrichment)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/educational_enrichment/educational_enrichment_listing.html', locals())



@ login_required(login_url='/login/')
def add_educational_enrichment_untrust_po_report(request, task_id):
    heading = "Section 12: Add of educational enrichment support provided"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    education_enrichment =  EducatinalEnrichmentSupportProvided.objects.filter(status=1, )
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        parent_guardian_name = data.get('parent_guardian_name')
        enrolment_date = data.get('enrolment_date')
        standard = data.get('standard')
        duration_of_coaching_support = data.get('duration_of_coaching_support')
        task = Task.objects.get(id=task_id)
        education_enrichment =  EducatinalEnrichmentSupportProvided.objects.create(adolescent_name=adolescent_name,
        parent_guardian_name=parent_guardian_name, standard=standard, enrolment_date=enrolment_date,
        duration_of_coaching_support=duration_of_coaching_support, task=task, site_id = current_site)
        education_enrichment.save()
        return redirect('/po-report/untrust/educational-enrichment-listing/'+str(task_id))
    return render(request, 'po_report/untrust/educational_enrichment/add_educational_enrichment.html', locals())


@ login_required(login_url='/login/')
def edit_educational_enrichment_untrust_po_report(request, educational_id, task_id):
    heading = "Section 12: Edit of educational enrichment support provided"
    current_site = request.session.get('site_id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    education_enrichment =  EducatinalEnrichmentSupportProvided.objects.get(id=educational_id)
    adolescent_obj =  Adolescent.objects.filter(status=1, awc__id__in=awc_id)
    if request.method == 'POST':
        data = request.POST
        adolescent_name_id = data.get('adolescent_name')
        adolescent_name = Adolescent.objects.get(id=adolescent_name_id)
        parent_guardian_name = data.get('parent_guardian_name')
        enrolment_date = data.get('enrolment_date')
        standard = data.get('standard')
        duration_of_coaching_support = data.get('duration_of_coaching_support')
        task = Task.objects.get(id=task_id)

        education_enrichment.adolescent_name_id = adolescent_name
        education_enrichment.parent_guardian_name = parent_guardian_name
        education_enrichment.enrolment_date = enrolment_date
        education_enrichment.standard = standard
        education_enrichment.duration_of_coaching_support = duration_of_coaching_support
        education_enrichment.task_id = task
        education_enrichment.site_id =  current_site
        education_enrichment.save()
        return redirect('/po-report/untrust/educational-enrichment-listing/'+str(task_id))
    return render(request, 'po_report/untrust/educational_enrichment/edit_educational_enrichment.html', locals())


@ login_required(login_url='/login/')
def stakeholders_listing_untrust_po_report(request, task_id):
    heading = "Section 13: Details of capacity building of different stakeholders"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    if Stakeholder.objects.filter(task=task_id).exists():
        error="disabled"
    stakeholders_obj = Stakeholder.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, stakeholders_obj)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/stakeholders/stakeholders_listing.html', locals())


@ login_required(login_url='/login/')
def add_stakeholders_untrust_po_report(request, task_id):
    heading = "Section 13: Add of capacity building of different stakeholders"
    current_site = request.session.get('site_id')
    stakeholders_obj = Stakeholder.objects.filter()
    if request.method == 'POST':
        data = request.POST
        master_trainers_male = data.get('master_trainers_male')
        master_trainers_female = data.get('master_trainers_female')
        master_trainers_total = data.get('master_trainers_total')
        nodal_teachers_male = data.get('nodal_teachers_male')
        nodal_teachers_female = data.get('nodal_teachers_female')
        nodal_teachers_total = data.get('nodal_teachers_total')
        principals_male = data.get('principals_male')
        principals_female = data.get('principals_female')
        principals_total = data.get('principals_total')
        district_level_officials_male = data.get('district_level_officials_male')
        district_level_officials_female = data.get('district_level_officials_female')
        district_level_officials_total = data.get('district_level_officials_total')
        peer_educator_male = data.get('peer_educator_male')
        peer_educator_female = data.get('peer_educator_female')
        peer_educator_total = data.get('peer_educator_total')
        state_level_officials_male = data.get('state_level_officials_male')
        state_level_officials_female = data.get('state_level_officials_female')
        state_level_officials_total = data.get('state_level_officials_total')
        icds_awws_male = data.get('icds_awws_male')
        icds_awws_female = data.get('icds_awws_female')
        icds_awws_total = data.get('icds_awws_total')
        icds_supervisors_male = data.get('icds_supervisors_male')
        icds_supervisors_female = data.get('icds_supervisors_female')
        icds_supervisors_total = data.get('icds_supervisors_total')
        icds_peer_educator_male = data.get('icds_peer_educator_male')
        icds_peer_educator_female = data.get('icds_peer_educator_female')
        icds_peer_educator_total = data.get('icds_peer_educator_total')
        icds_child_developement_project_officers_male = data.get('icds_child_developement_project_officers_male')
        icds_child_developement_project_officers_female = data.get('icds_child_developement_project_officers_female')
        icds_child_developement_project_officers_total = data.get('icds_child_developement_project_officers_total')
        icds_district_level_officials_male = data.get('icds_district_level_officials_male')
        icds_district_level_officials_female = data.get('icds_district_level_officials_female')
        icds_district_level_officials_total = data.get('icds_district_level_officials_total')
        icds_state_level_officials_male = data.get('icds_state_level_officials_male')
        icds_state_level_officials_female = data.get('icds_state_level_officials_female')
        icds_state_level_officials_total = data.get('icds_state_level_officials_total')
        health_ashas_male = data.get('health_ashas_male')
        health_ashas_female = data.get('health_ashas_female')
        health_ashas_total = data.get('health_ashas_total')
        health_anms_male = data.get('health_anms_male')
        health_anms_female = data.get('health_anms_female')
        health_anms_total = data.get('health_anms_total')
        health_bpm_bhm_pheos_male = data.get('health_bpm_bhm_pheos_male')
        health_bpm_bhm_pheos_female = data.get('health_bpm_bhm_pheos_female')
        health_bpm_bhm_pheos_total = data.get('health_bpm_bhm_pheos_total')
        health_medical_officers_male = data.get('health_medical_officers_male')
        health_medical_officers_female = data.get('health_medical_officers_female')
        health_medical_officers_total = data.get('health_medical_officers_total')
        health_district_level_officials_male = data.get('health_district_level_officials_male')
        health_district_level_officials_female = data.get('health_district_level_officials_female')
        health_district_level_officials_total = data.get('health_district_level_officials_total')
        health_state_level_officials_male = data.get('health_state_level_officials_male')
        health_state_level_officials_female = data.get('health_state_level_officials_female')
        health_state_level_officials_total = data.get('health_state_level_officials_total')
        health_rsk_male = data.get('health_rsk_male')
        health_rsk_female = data.get('health_rsk_female')
        health_rsk_total = data.get('health_rsk_total')
        health_peer_educator_male = data.get('health_peer_educator_male')
        health_peer_educator_female = data.get('health_peer_educator_female')
        health_peer_educator_total = data.get('health_peer_educator_total')
        panchayat_ward_members_male = data.get('panchayat_ward_members_male')
        panchayat_ward_members_female = data.get('panchayat_ward_members_female')
        panchayat_ward_members_total = data.get('panchayat_ward_members_total')
        panchayat_up_mukhiya_up_Pramukh_male = data.get('panchayat_up_mukhiya_up_Pramukh_male')
        panchayat_up_mukhiya_up_Pramukh_female = data.get('panchayat_up_mukhiya_up_Pramukh_female')
        panchayat_up_mukhiya_up_Pramukh_total = data.get('panchayat_up_mukhiya_up_Pramukh_total')
        panchayat_mukhiya_Pramukh_male = data.get('panchayat_mukhiya_Pramukh_male')
        panchayat_mukhiya_Pramukh_female = data.get('panchayat_mukhiya_Pramukh_female')
        panchayat_mukhiya_Pramukh_total = data.get('panchayat_mukhiya_Pramukh_total')
        panchayat_samiti_member_male = data.get('panchayat_samiti_member_male')
        panchayat_samiti_member_female = data.get('panchayat_samiti_member_female')
        panchayat_samiti_member_total = data.get('panchayat_samiti_member_total')
        panchayat_zila_parishad_member_male = data.get('panchayat_zila_parishad_member_male')
        panchayat_zila_parishad_member_female = data.get('panchayat_zila_parishad_member_female')
        panchayat_zila_parishad_member_total = data.get('panchayat_zila_parishad_member_total')
        panchayat_vc_zila_parishad_male = data.get('panchayat_vc_zila_parishad_male')
        panchayat_vc_zila_parishad_female = data.get('panchayat_vc_zila_parishad_female')
        panchayat_vc_zila_parishad_total = data.get('panchayat_vc_zila_parishad_total')
        panchayat_chairman_zila_parishad_male = data.get('panchayat_chairman_zila_parishad_male')
        panchayat_chairman_zila_parishad_female = data.get('panchayat_chairman_zila_parishad_female')
        panchayat_chairman_zila_parishad_total = data.get('panchayat_chairman_zila_parishad_total')
        panchayat_block_level_officials_male = data.get('panchayat_block_level_officials_male')
        panchayat_block_level_officials_female = data.get('panchayat_block_level_officials_female')
        panchayat_block_level_officials_total = data.get('panchayat_block_level_officials_total')
        panchayat_district_level_officials_male = data.get('panchayat_district_level_officials_male')
        panchayat_district_level_officials_female = data.get('panchayat_district_level_officials_female')
        panchayat_district_level_officials_total = data.get('panchayat_district_level_officials_total')
        panchayat_state_level_officials_male = data.get('panchayat_state_level_officials_male')
        panchayat_state_level_officials_female = data.get('panchayat_state_level_officials_female')
        panchayat_state_level_officials_total = data.get('panchayat_state_level_officials_total')
        media_interns_male = data.get('media_interns_male')
        media_interns_female = data.get('media_interns_female')
        media_interns_total = data.get('media_interns_total')
        media_journalists_male = data.get('media_journalists_male')
        media_journalists_female = data.get('media_journalists_female')
        media_journalists_total = data.get('media_journalists_total')
        media_editors_male = data.get('media_editors_male')
        media_editors_female = data.get('media_editors_female')
        media_editors_total = data.get('media_editors_total')
        others_block_cluster_field_corrdinators_male = data.get('others_block_cluster_field_corrdinators_male')
        others_block_cluster_field_corrdinators_female = data.get('others_block_cluster_field_corrdinators_female')
        others_block_cluster_field_corrdinators_total = data.get('others_block_cluster_field_corrdinators_total')
        others_ngo_staff_corrdinators_male = data.get('others_ngo_staff_corrdinators_male')
        others_ngo_staff_corrdinators_female = data.get('others_ngo_staff_corrdinators_female')
        others_ngo_staff_corrdinators_total = data.get('others_ngo_staff_corrdinators_total')
        others_male = data.get('others_male')
        others_female = data.get('others_female')
        others_total = data.get('others_total')
        total_male = data.get('total_male')
        total_female = data.get('total_female')
        total = data.get('total')
        task = Task.objects.get(id=task_id)

        stakeholders_obj = Stakeholder.objects.create(user_name=request.user,
        master_trainers_male=master_trainers_male, master_trainers_female=master_trainers_female, master_trainers_total=master_trainers_total,
        nodal_teachers_male=nodal_teachers_male, nodal_teachers_female=nodal_teachers_female, nodal_teachers_total=nodal_teachers_total,
        principals_male=principals_male, principals_female=principals_female, principals_total=principals_total, 
        district_level_officials_male=district_level_officials_male, district_level_officials_female=district_level_officials_female, district_level_officials_total=district_level_officials_total,
        peer_educator_male=peer_educator_male, peer_educator_female=peer_educator_female, peer_educator_total=peer_educator_total,
        state_level_officials_male=state_level_officials_male, state_level_officials_female=state_level_officials_female, state_level_officials_total=state_level_officials_total,
        icds_awws_male=icds_awws_male, icds_awws_female=icds_awws_female, icds_awws_total=icds_awws_total,
        icds_supervisors_male=icds_supervisors_male, icds_supervisors_female=icds_supervisors_female, icds_supervisors_total=icds_supervisors_total,
        icds_peer_educator_male=icds_peer_educator_male, icds_peer_educator_female=icds_peer_educator_female, icds_peer_educator_total=icds_peer_educator_total,
        icds_child_developement_project_officers_male=icds_child_developement_project_officers_male, icds_child_developement_project_officers_female=icds_child_developement_project_officers_female, icds_child_developement_project_officers_total=icds_child_developement_project_officers_total,
        icds_district_level_officials_male=icds_district_level_officials_male, icds_district_level_officials_female=icds_district_level_officials_female, icds_district_level_officials_total=icds_district_level_officials_total,
        icds_state_level_officials_male=icds_state_level_officials_male, icds_state_level_officials_female=icds_state_level_officials_female, icds_state_level_officials_total=icds_state_level_officials_total,
        health_ashas_male=health_ashas_male, health_ashas_female=health_ashas_female, health_ashas_total=health_ashas_total,
        health_anms_male=health_anms_male, health_anms_female=health_anms_female, health_anms_total=health_anms_total,
        health_bpm_bhm_pheos_male=health_bpm_bhm_pheos_male, health_bpm_bhm_pheos_female=health_bpm_bhm_pheos_female, health_bpm_bhm_pheos_total=health_bpm_bhm_pheos_total,
        health_medical_officers_male=health_medical_officers_male, health_medical_officers_female=health_medical_officers_female, health_medical_officers_total=health_medical_officers_total,
        health_district_level_officials_male=health_district_level_officials_male, health_district_level_officials_female=health_district_level_officials_female, health_district_level_officials_total=health_district_level_officials_total,
        health_state_level_officials_male=health_state_level_officials_male, health_state_level_officials_female=health_state_level_officials_female, health_state_level_officials_total=health_state_level_officials_total,
        health_rsk_male=health_rsk_male, health_rsk_female=health_rsk_female, health_rsk_total=health_rsk_total,
        health_peer_educator_male=health_peer_educator_male, health_peer_educator_female=health_peer_educator_female, health_peer_educator_total=health_peer_educator_total,
        panchayat_ward_members_male=panchayat_ward_members_male, panchayat_ward_members_female=panchayat_ward_members_female, panchayat_ward_members_total=panchayat_ward_members_total,
        panchayat_up_mukhiya_up_Pramukh_male=panchayat_up_mukhiya_up_Pramukh_male, panchayat_up_mukhiya_up_Pramukh_female=panchayat_up_mukhiya_up_Pramukh_female, panchayat_up_mukhiya_up_Pramukh_total=panchayat_up_mukhiya_up_Pramukh_total,
        panchayat_mukhiya_Pramukh_male=panchayat_mukhiya_Pramukh_male, panchayat_mukhiya_Pramukh_female=panchayat_mukhiya_Pramukh_female, panchayat_mukhiya_Pramukh_total=panchayat_mukhiya_Pramukh_total,
        panchayat_samiti_member_male=panchayat_samiti_member_male, panchayat_samiti_member_female=panchayat_samiti_member_female, panchayat_samiti_member_total=panchayat_samiti_member_total,
        panchayat_zila_parishad_member_male=panchayat_zila_parishad_member_male, panchayat_zila_parishad_member_female=panchayat_zila_parishad_member_female, panchayat_zila_parishad_member_total=panchayat_zila_parishad_member_total,
        panchayat_vc_zila_parishad_male=panchayat_vc_zila_parishad_male, panchayat_vc_zila_parishad_female=panchayat_vc_zila_parishad_female, panchayat_vc_zila_parishad_total=panchayat_vc_zila_parishad_total,
        panchayat_chairman_zila_parishad_male=panchayat_chairman_zila_parishad_male, panchayat_chairman_zila_parishad_female=panchayat_chairman_zila_parishad_female, panchayat_chairman_zila_parishad_total=panchayat_chairman_zila_parishad_total,
        panchayat_block_level_officials_male=panchayat_block_level_officials_male, panchayat_block_level_officials_female=panchayat_block_level_officials_female, panchayat_block_level_officials_total=panchayat_block_level_officials_total,
        panchayat_district_level_officials_male=panchayat_district_level_officials_male, panchayat_district_level_officials_female=panchayat_district_level_officials_female, panchayat_district_level_officials_total=panchayat_district_level_officials_total,
        panchayat_state_level_officials_male=panchayat_state_level_officials_male, panchayat_state_level_officials_female=panchayat_state_level_officials_female, panchayat_state_level_officials_total=panchayat_state_level_officials_total,
        media_interns_male=media_interns_male, media_interns_female=media_interns_female, media_interns_total=media_interns_total,
        media_journalists_male=media_journalists_male, media_journalists_female=media_journalists_female, media_journalists_total=media_journalists_total,
        media_editors_male=media_editors_male, media_editors_female=media_editors_female, media_editors_total=media_editors_total,
        others_block_cluster_field_corrdinators_male=others_block_cluster_field_corrdinators_male, others_block_cluster_field_corrdinators_female=others_block_cluster_field_corrdinators_female, others_block_cluster_field_corrdinators_total=others_block_cluster_field_corrdinators_total,
        others_ngo_staff_corrdinators_male=others_ngo_staff_corrdinators_male, others_ngo_staff_corrdinators_female=others_ngo_staff_corrdinators_female, others_ngo_staff_corrdinators_total=others_ngo_staff_corrdinators_total,
        others_male=others_male, others_female=others_female, others_total=others_total,
        total_male=total_male, total_female=total_female, total=total, task=task, site_id = current_site,)
        stakeholders_obj.save()
        return redirect('/po-report/untrust/stakeholders-listing/'+str(task_id))
    return render(request, 'po_report/untrust/stakeholders/add_stakeholders.html', locals())

@ login_required(login_url='/login/')
def edit_stakeholders_untrust_po_report(request, stakeholders_id, task_id):
    heading = "Section 13: Edit of capacity building of different stakeholders"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    stakeholders_obj = Stakeholder.objects.get(id=stakeholders_id)
    if request.method == 'POST':
        data = request.POST
        user_name_id = data.get('user_name')
        master_trainers_male = data.get('master_trainers_male')
        master_trainers_female = data.get('master_trainers_female')
        master_trainers_total = data.get('master_trainers_total')
        nodal_teachers_male = data.get('nodal_teachers_male')
        nodal_teachers_female = data.get('nodal_teachers_female')
        nodal_teachers_total = data.get('nodal_teachers_total')
        principals_male = data.get('principals_male')
        principals_female = data.get('principals_female')
        principals_total = data.get('principals_total')
        district_level_officials_male = data.get('district_level_officials_male')
        district_level_officials_female = data.get('district_level_officials_female')
        district_level_officials_total = data.get('district_level_officials_total')
        peer_educator_male = data.get('peer_educator_male')
        peer_educator_female = data.get('peer_educator_female')
        peer_educator_total = data.get('peer_educator_total')
        state_level_officials_male = data.get('state_level_officials_male')
        state_level_officials_female = data.get('state_level_officials_female')
        state_level_officials_total = data.get('state_level_officials_total')
        icds_awws_male = data.get('icds_awws_male')
        icds_awws_female = data.get('icds_awws_female')
        icds_awws_total = data.get('icds_awws_total')
        icds_supervisors_male = data.get('icds_supervisors_male')
        icds_supervisors_female = data.get('icds_supervisors_female')
        icds_supervisors_total = data.get('icds_supervisors_total')
        icds_peer_educator_male = data.get('icds_peer_educator_male')
        icds_peer_educator_female = data.get('icds_peer_educator_female')
        icds_peer_educator_total = data.get('icds_peer_educator_total')
        icds_child_developement_project_officers_male = data.get('icds_child_developement_project_officers_male')
        icds_child_developement_project_officers_female = data.get('icds_child_developement_project_officers_female')
        icds_child_developement_project_officers_total = data.get('icds_child_developement_project_officers_total')
        icds_district_level_officials_male = data.get('icds_district_level_officials_male')
        icds_district_level_officials_female = data.get('icds_district_level_officials_female')
        icds_district_level_officials_total = data.get('icds_district_level_officials_total')
        icds_state_level_officials_male = data.get('icds_state_level_officials_male')
        icds_state_level_officials_female = data.get('icds_state_level_officials_female')
        icds_state_level_officials_total = data.get('icds_state_level_officials_total')
        health_ashas_male = data.get('health_ashas_male')
        health_ashas_female = data.get('health_ashas_female')
        health_ashas_total = data.get('health_ashas_total')
        health_anms_male = data.get('health_anms_male')
        health_anms_female = data.get('health_anms_female')
        health_anms_total = data.get('health_anms_total')
        health_bpm_bhm_pheos_male = data.get('health_bpm_bhm_pheos_male')
        health_bpm_bhm_pheos_female = data.get('health_bpm_bhm_pheos_female')
        health_bpm_bhm_pheos_total = data.get('health_bpm_bhm_pheos_total')
        health_medical_officers_male = data.get('health_medical_officers_male')
        health_medical_officers_female = data.get('health_medical_officers_female')
        health_medical_officers_total = data.get('health_medical_officers_total')
        health_district_level_officials_male = data.get('health_district_level_officials_male')
        health_district_level_officials_female = data.get('health_district_level_officials_female')
        health_district_level_officials_total = data.get('health_district_level_officials_total')
        health_state_level_officials_male = data.get('health_state_level_officials_male')
        health_state_level_officials_female = data.get('health_state_level_officials_female')
        health_state_level_officials_total = data.get('health_state_level_officials_total')
        health_rsk_male = data.get('health_rsk_male')
        health_rsk_female = data.get('health_rsk_female')
        health_rsk_total = data.get('health_rsk_total')
        health_peer_educator_male = data.get('health_peer_educator_male')
        health_peer_educator_female = data.get('health_peer_educator_female')
        health_peer_educator_total = data.get('health_peer_educator_total')
        panchayat_ward_members_male = data.get('panchayat_ward_members_male')
        panchayat_ward_members_female = data.get('panchayat_ward_members_female')
        panchayat_ward_members_total = data.get('panchayat_ward_members_total')
        panchayat_up_mukhiya_up_Pramukh_male = data.get('panchayat_up_mukhiya_up_Pramukh_male')
        panchayat_up_mukhiya_up_Pramukh_female = data.get('panchayat_up_mukhiya_up_Pramukh_female')
        panchayat_up_mukhiya_up_Pramukh_total = data.get('panchayat_up_mukhiya_up_Pramukh_total')
        panchayat_mukhiya_Pramukh_male = data.get('panchayat_mukhiya_Pramukh_male')
        panchayat_mukhiya_Pramukh_female = data.get('panchayat_mukhiya_Pramukh_female')
        panchayat_mukhiya_Pramukh_total = data.get('panchayat_mukhiya_Pramukh_total')
        panchayat_samiti_member_male = data.get('panchayat_samiti_member_male')
        panchayat_samiti_member_female = data.get('panchayat_samiti_member_female')
        panchayat_samiti_member_total = data.get('panchayat_samiti_member_total')
        panchayat_zila_parishad_member_male = data.get('panchayat_zila_parishad_member_male')
        panchayat_zila_parishad_member_female = data.get('panchayat_zila_parishad_member_female')
        panchayat_zila_parishad_member_total = data.get('panchayat_zila_parishad_member_total')
        panchayat_vc_zila_parishad_male = data.get('panchayat_vc_zila_parishad_male')
        panchayat_vc_zila_parishad_female = data.get('panchayat_vc_zila_parishad_female')
        panchayat_vc_zila_parishad_total = data.get('panchayat_vc_zila_parishad_total')
        panchayat_chairman_zila_parishad_male = data.get('panchayat_chairman_zila_parishad_male')
        panchayat_chairman_zila_parishad_female = data.get('panchayat_chairman_zila_parishad_female')
        panchayat_chairman_zila_parishad_total = data.get('panchayat_chairman_zila_parishad_total')
        panchayat_block_level_officials_male = data.get('panchayat_block_level_officials_male')
        panchayat_block_level_officials_female = data.get('panchayat_block_level_officials_female')
        panchayat_block_level_officials_total = data.get('panchayat_block_level_officials_total')
        panchayat_district_level_officials_male = data.get('panchayat_district_level_officials_male')
        panchayat_district_level_officials_female = data.get('panchayat_district_level_officials_female')
        panchayat_district_level_officials_total = data.get('panchayat_district_level_officials_total')
        panchayat_state_level_officials_male = data.get('panchayat_state_level_officials_male')
        panchayat_state_level_officials_female = data.get('panchayat_state_level_officials_female')
        panchayat_state_level_officials_total = data.get('panchayat_state_level_officials_total')
        media_interns_male = data.get('media_interns_male')
        media_interns_female = data.get('media_interns_female')
        media_interns_total = data.get('media_interns_total')
        media_journalists_male = data.get('media_journalists_male')
        media_journalists_female = data.get('media_journalists_female')
        media_journalists_total = data.get('media_journalists_total')
        media_editors_male = data.get('media_editors_male')
        media_editors_female = data.get('media_editors_female')
        media_editors_total = data.get('media_editors_total')
        others_block_cluster_field_corrdinators_male = data.get('others_block_cluster_field_corrdinators_male')
        others_block_cluster_field_corrdinators_female = data.get('others_block_cluster_field_corrdinators_female')
        others_block_cluster_field_corrdinators_total = data.get('others_block_cluster_field_corrdinators_total')
        others_ngo_staff_corrdinators_male = data.get('others_ngo_staff_corrdinators_male')
        others_ngo_staff_corrdinators_female = data.get('others_ngo_staff_corrdinators_female')
        others_ngo_staff_corrdinators_total = data.get('others_ngo_staff_corrdinators_total')
        others_male = data.get('others_male')
        others_female = data.get('others_female')
        others_total = data.get('others_total')
        total_male = data.get('total_male')
        total_female = data.get('total_female')
        total = data.get('total')
        task = Task.objects.get(id=task_id)

        stakeholders_obj.user_name_id = request.user
        stakeholders_obj.master_trainers_male = master_trainers_male
        stakeholders_obj.master_trainers_female = master_trainers_female
        stakeholders_obj.master_trainers_total = master_trainers_total
        stakeholders_obj.nodal_teachers_male = nodal_teachers_male
        stakeholders_obj.nodal_teachers_female = nodal_teachers_female
        stakeholders_obj.nodal_teachers_total = nodal_teachers_total
        stakeholders_obj.principals_male = principals_male
        stakeholders_obj.principals_female = principals_female
        stakeholders_obj.principals_total = principals_total
        stakeholders_obj.district_level_officials_male = district_level_officials_male
        stakeholders_obj.district_level_officials_female = district_level_officials_female
        stakeholders_obj.district_level_officials_total = district_level_officials_total
        stakeholders_obj.peer_educator_male = peer_educator_male
        stakeholders_obj.peer_educator_female = peer_educator_female
        stakeholders_obj.peer_educator_total = peer_educator_total
        stakeholders_obj.state_level_officials_male = state_level_officials_male
        stakeholders_obj.state_level_officials_female = state_level_officials_female
        stakeholders_obj.state_level_officials_total = state_level_officials_total
        stakeholders_obj.icds_awws_male = icds_awws_male
        stakeholders_obj.icds_awws_female = icds_awws_female
        stakeholders_obj.icds_awws_total = icds_awws_total
        stakeholders_obj.icds_supervisors_male = icds_supervisors_male
        stakeholders_obj.icds_supervisors_female = icds_supervisors_female
        stakeholders_obj.icds_supervisors_total = icds_supervisors_total
        stakeholders_obj.icds_peer_educator_male = icds_peer_educator_male
        stakeholders_obj.icds_peer_educator_female = icds_peer_educator_female
        stakeholders_obj.icds_peer_educator_total = icds_peer_educator_total
        stakeholders_obj.icds_child_developement_project_officers_male = icds_child_developement_project_officers_male
        stakeholders_obj.icds_child_developement_project_officers_female = icds_child_developement_project_officers_female
        stakeholders_obj.icds_child_developement_project_officers_total = icds_child_developement_project_officers_total
        stakeholders_obj.icds_district_level_officials_male = icds_district_level_officials_male
        stakeholders_obj.icds_district_level_officials_female = icds_district_level_officials_female
        stakeholders_obj.icds_district_level_officials_total = icds_district_level_officials_total
        stakeholders_obj.icds_state_level_officials_male = icds_state_level_officials_male
        stakeholders_obj.icds_state_level_officials_female = icds_state_level_officials_female
        stakeholders_obj.icds_state_level_officials_total = icds_state_level_officials_total
        stakeholders_obj.health_ashas_male = health_ashas_male
        stakeholders_obj.health_ashas_female = health_ashas_female
        stakeholders_obj.health_ashas_total = health_ashas_total
        stakeholders_obj.health_anms_male = health_anms_male
        stakeholders_obj.health_anms_female = health_anms_female
        stakeholders_obj.health_anms_total = health_anms_total
        stakeholders_obj.health_bpm_bhm_pheos_male = health_bpm_bhm_pheos_male
        stakeholders_obj.health_bpm_bhm_pheos_female = health_bpm_bhm_pheos_female
        stakeholders_obj.health_bpm_bhm_pheos_total = health_bpm_bhm_pheos_total
        stakeholders_obj.health_medical_officers_male = health_medical_officers_male
        stakeholders_obj.health_medical_officers_female = health_medical_officers_female
        stakeholders_obj.health_medical_officers_total = health_medical_officers_total
        stakeholders_obj.health_district_level_officials_male = health_district_level_officials_male
        stakeholders_obj.health_district_level_officials_female = health_district_level_officials_female
        stakeholders_obj.health_district_level_officials_total = health_district_level_officials_total
        stakeholders_obj.health_state_level_officials_male = health_state_level_officials_male
        stakeholders_obj.health_state_level_officials_female = health_state_level_officials_female
        stakeholders_obj.health_state_level_officials_total = health_state_level_officials_total
        stakeholders_obj.health_rsk_male = health_rsk_male
        stakeholders_obj.health_rsk_female = health_rsk_female
        stakeholders_obj.health_rsk_total = health_rsk_total
        stakeholders_obj.health_peer_educator_male = health_peer_educator_male
        stakeholders_obj.health_peer_educator_female = health_peer_educator_female
        stakeholders_obj.health_peer_educator_total = health_peer_educator_total
        stakeholders_obj.panchayat_ward_members_male = panchayat_ward_members_male
        stakeholders_obj.panchayat_ward_members_female = panchayat_ward_members_female
        stakeholders_obj.panchayat_ward_members_total = panchayat_ward_members_total
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_male = panchayat_up_mukhiya_up_Pramukh_male
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_female = panchayat_up_mukhiya_up_Pramukh_female
        stakeholders_obj.panchayat_up_mukhiya_up_Pramukh_total = panchayat_up_mukhiya_up_Pramukh_total
        stakeholders_obj.panchayat_mukhiya_Pramukh_male = panchayat_mukhiya_Pramukh_male
        stakeholders_obj.panchayat_mukhiya_Pramukh_female = panchayat_mukhiya_Pramukh_female
        stakeholders_obj.panchayat_mukhiya_Pramukh_total = panchayat_mukhiya_Pramukh_total
        stakeholders_obj.panchayat_samiti_member_male = panchayat_samiti_member_male
        stakeholders_obj.panchayat_samiti_member_female = panchayat_samiti_member_female
        stakeholders_obj.panchayat_samiti_member_male = panchayat_samiti_member_total
        stakeholders_obj.panchayat_zila_parishad_member_male = panchayat_zila_parishad_member_male
        stakeholders_obj.panchayat_zila_parishad_member_female = panchayat_zila_parishad_member_female
        stakeholders_obj.panchayat_zila_parishad_member_total = panchayat_zila_parishad_member_total
        stakeholders_obj.panchayat_vc_zila_parishad_male = panchayat_vc_zila_parishad_male
        stakeholders_obj.panchayat_vc_zila_parishad_female = panchayat_vc_zila_parishad_female
        stakeholders_obj.panchayat_vc_zila_parishad_total = panchayat_vc_zila_parishad_total
        stakeholders_obj.panchayat_chairman_zila_parishad_male = panchayat_chairman_zila_parishad_male
        stakeholders_obj.panchayat_chairman_zila_parishad_female = panchayat_chairman_zila_parishad_female
        stakeholders_obj.panchayat_chairman_zila_parishad_total = panchayat_chairman_zila_parishad_total
        stakeholders_obj.panchayat_block_level_officials_male = panchayat_block_level_officials_male
        stakeholders_obj.panchayat_block_level_officials_female = panchayat_block_level_officials_female
        stakeholders_obj.panchayat_block_level_officials_total = panchayat_block_level_officials_total
        stakeholders_obj.panchayat_district_level_officials_male = panchayat_district_level_officials_male
        stakeholders_obj.panchayat_district_level_officials_female = panchayat_district_level_officials_female
        stakeholders_obj.panchayat_district_level_officials_total = panchayat_district_level_officials_total
        stakeholders_obj.panchayat_state_level_officials_male = panchayat_state_level_officials_male
        stakeholders_obj.panchayat_state_level_officials_female = panchayat_state_level_officials_female
        stakeholders_obj.panchayat_state_level_officials_total = panchayat_state_level_officials_total
        stakeholders_obj.media_interns_male = media_interns_male
        stakeholders_obj.media_interns_female = media_interns_female
        stakeholders_obj.media_interns_total = media_interns_total
        stakeholders_obj.media_journalists_male = media_journalists_male
        stakeholders_obj.media_journalists_female = media_journalists_female
        stakeholders_obj.media_journalists_total = media_journalists_total
        stakeholders_obj.media_editors_male = media_editors_male
        stakeholders_obj.media_editors_female = media_editors_female
        stakeholders_obj.media_editors_total = media_editors_total
        stakeholders_obj.others_block_cluster_field_corrdinators_male = others_block_cluster_field_corrdinators_male
        stakeholders_obj.others_block_cluster_field_corrdinators_female = others_block_cluster_field_corrdinators_female
        stakeholders_obj.others_block_cluster_field_corrdinators_total = others_block_cluster_field_corrdinators_total
        stakeholders_obj.others_ngo_staff_corrdinators_male = others_ngo_staff_corrdinators_male
        stakeholders_obj.others_ngo_staff_corrdinators_female = others_ngo_staff_corrdinators_female
        stakeholders_obj.others_ngo_staff_corrdinators_total = others_ngo_staff_corrdinators_total
        stakeholders_obj.others_male = others_male
        stakeholders_obj.others_female = others_female
        stakeholders_obj.others_total = others_total
        stakeholders_obj.total_male = total_male
        stakeholders_obj.total_female = total_female
        stakeholders_obj.total = total
        stakeholders_obj.task_id = task
        stakeholders_obj.site_id =  current_site
        stakeholders_obj.save()
        return redirect('/po-report/untrust/stakeholders-listing/'+str(task_id))
    return render(request, 'po_report/untrust/stakeholders/edit_stakeholders.html', locals())


@ login_required(login_url='/login/')
def sessions_monitoring_listing_untrust_po_report(request, task_id):
    heading = "Section 14: Details of sessions monitoring and handholding support at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    village_id =CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, sessions_monitoring)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/sessions_monitoring/sessions_monitoring_listing.html', locals())


@ login_required(login_url='/login/')
def add_sessions_monitoring_untrust_po_report(request, task_id):
    heading = "Section 14: Add of sessions monitoring and handholding support at block level"
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        
        
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        

        date = data.get('date')
        sessions = data.getlist('session_attended')
        session_attended = ", ".join(sessions)
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)


        sessions_monitoring = SessionMonitoring.objects.create(name_of_visited=name_of_visited, session_attended=session_attended,
          date=date,
        observation=observation, recommendation=recommendation, task=task, site_id = current_site)
        
        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            sessions_monitoring.content_type=content_type
            sessions_monitoring.object_id=selected_object_id
        
        if name_of_visited in ['4','5']:
            sessions_monitoring.name_of_place_visited = selected_field_other

        sessions_monitoring.save()

        return redirect('/po-report/untrust/sessions-monitoring-listing/'+str(task_id))
    return render(request, 'po_report/untrust/sessions_monitoring/add_sessions_monitoring.html', locals())


@ login_required(login_url='/login/')
def edit_sessions_monitoring_untrust_po_report(request, sessions_id, task_id):
    heading = "Section 14: Edit of sessions monitoring and handholding support at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    sessions_monitoring = SessionMonitoring.objects.get(id=sessions_id)
    session_choice = sessions_monitoring.session_attended.split(', ')
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        selected_field_other = data.get('selected_field_other')
        name_of_visited = data.get('name_of_visited')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        content_type = ContentType.objects.get(model=content_type_model)
        date = data.get('date')
        sessions = data.getlist('session_attended')
        session_attended = ", ".join(sessions)
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        sessions_monitoring.name_of_visited = name_of_visited

        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            sessions_monitoring.content_type=content_type
            sessions_monitoring.object_id=selected_object_id

        if name_of_visited in ['4','5']:
            sessions_monitoring.name_of_place_visited = selected_field_other

        sessions_monitoring.date = date
        sessions_monitoring.session_attended = session_attended
        sessions_monitoring.observation = observation
        sessions_monitoring.recommendation = recommendation
        sessions_monitoring.task_id = task
        sessions_monitoring.site_id =  current_site
        sessions_monitoring.save()
        return redirect('/po-report/untrust/sessions-monitoring-listing/'+str(task_id))
    return render(request, 'po_report/untrust/sessions_monitoring/edit_sessions_monitoring.html', locals())



@ login_required(login_url='/login/')
def facility_visits_listing_untrust_po_report(request, task_id):
    heading = "Section 15: Details of events & facility visits at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    village_id =CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(status=1, user=request.user).values_list('awc__id')
    school_id = CC_School.objects.filter(status=1, user=request.user).values_list('school__id')
    facility_visits = Events.objects.filter(status=1, task__id = task_id)
    data = pagination_function(request, facility_visits)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/facility_visits/facility_visits_listing.html', locals())


@ login_required(login_url='/login/')
def add_facility_visits_untrust_po_report(request, task_id):
    heading = "Section 15: Add of events & facility visits at block level"
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    facility_visits = Events.objects.filter()
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
        purpose_visited = data.get('purpose_visited')
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        
        facility_visits = Events.objects.create(name_of_visited=name_of_visited, purpose_visited=purpose_visited,
        date=date,
        observation=observation, recommendation=recommendation, task=task, site_id = current_site)
        
        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            facility_visits.content_type=content_type
            facility_visits.object_id=selected_object_id

        if name_of_visited in ['4','5','6','7','8','9','10','11']:
            facility_visits.name_of_place_visited = selected_field_other

        facility_visits.save()
        return redirect('/po-report/untrust/facility-visits-listing/'+str(task_id))
    return render(request, 'po_report/untrust/facility_visits/add_facility_visits.html', locals())


@ login_required(login_url='/login/')
def edit_facility_visits_untrust_po_report(request, facility_id, task_id):
    heading = "Section 15: Edit of events & facility visits at block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    user_report_po = MisReport.objects.filter(report_to = request.user).values_list('report_person__id', flat=True)
    user_report_spo = MisReport.objects.filter(report_to__id__in = user_report_po).values_list('report_person__id', flat=True)
    village_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__village__id')
    awc_id = CC_AWC_AH.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('awc__id')
    school_id = CC_School.objects.filter(Q(user__id__in=user_report_po) | Q(user__id__in=user_report_spo), status=1).values_list('school__id')
    facility_visits = Events.objects.get(id=facility_id)
    awc_obj = AWC.objects.filter(status=1, id__in=awc_id).order_by('name')
    village_obj = Village.objects.filter(status=1, id__in=village_id).order_by('name')
    school_obj = School.objects.filter(status=1, id__in=school_id).order_by('name')
    if request.method == 'POST':
        data = request.POST
        name_of_visited = data.get('name_of_visited')
        selected_field_other = data.get('selected_field_other')
        if name_of_visited == '1':
            content_type_model='village'
            selected_object_id=data.get('selected_field_village')
        elif name_of_visited == '2':
            content_type_model='awc'
            selected_object_id=data.get('selected_field_awc')
        else:
            content_type_model='school'
            selected_object_id=data.get('selected_field_school')

        date = data.get('date')
        purpose_visited = data.get('purpose_visited')
        observation = data.get('observation')
        recommendation = data.get('recommendation')
        task = Task.objects.get(id=task_id)

        facility_visits.name_of_visited = name_of_visited

        if selected_object_id:
            content_type = ContentType.objects.get(model=content_type_model)
            facility_visits.content_type = content_type
            facility_visits.object_id = selected_object_id
        
        if name_of_visited in ['4','5','6','7','8','9','10','11']:
            facility_visits.name_of_place_visited = selected_field_other

        facility_visits.date = date
        facility_visits.purpose_visited = purpose_visited
        facility_visits.observation = observation
        facility_visits.recommendation = recommendation
        facility_visits.task_id = task
        facility_visits.site_id =  current_site
        facility_visits.save()
        return redirect('/po-report/untrust/facility-visits-listing/'+str(task_id))
    return render(request, 'po_report/untrust/facility_visits/edit_facility_visits.html', locals())



@ login_required(login_url='/login/')
def followup_liaision_listing_untrust_po_report(request, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    heading = "Section 17: Details of one to one (Follow up/ Liaison) meetings at district & Block Level"
    followup_liaision = FollowUP_LiaisionMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, followup_liaision)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/followup_liaision/followup_liaision_listing.html', locals())


@ login_required(login_url='/login/')
def add_followup_liaision_untrust_po_report(request, task_id):
    heading = "Section 17: Add of one to one (Follow up/ Liaison) meetings at district & Block Level"
    current_site = request.session.get('site_id')
    followup_liaision = FollowUP_LiaisionMeeting.objects.filter()
    meeting_obj = MasterLookUp.objects.filter(parent__slug = 'meeting-with-designation')
    if request.method == 'POST':
        data = request.POST
        date = data.get('date')
        district_block_level = data.get('district_block_level')
        meeting_id = data.get('meeting')
        meeting = MasterLookUp.objects.get(id = meeting_id)
        departments = data.get('departments')
        point_of_discussion = data.get('point_of_discussion')
        outcome = data.get('outcome')
        decision_taken = data.get('decision_taken')
        remarks = data.get('remarks')
        task = Task.objects.get(id=task_id)

        followup_liaision = FollowUP_LiaisionMeeting.objects.create(user_name=request.user, date=date,
        district_block_level=district_block_level, meeting_name=meeting, departments=departments, point_of_discussion=point_of_discussion,
        outcome=outcome, decision_taken=decision_taken, remarks=remarks, site_id = current_site, task=task)
        followup_liaision.save()
        return redirect('/po-report/untrust/followup-liaision-listing/'+str(task_id))
    return render(request, 'po_report/untrust/followup_liaision/add_followup_liaision.html', locals())


@ login_required(login_url='/login/')
def edit_followup_liaision_untrust_po_report(request, followup_liaision_id, task_id):
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    heading = "Section 17: Edit of one to one (Follow up/ Liaison) meetings at district & Block Level"
    current_site = request.session.get('site_id')
    followup_liaision = FollowUP_LiaisionMeeting.objects.get(id=followup_liaision_id)
    meeting_obj = MasterLookUp.objects.filter(parent__slug = 'meeting-with-designation')
    if request.method == 'POST':
        data = request.POST
        date = data.get('date')
        district_block_level = data.get('district_block_level')
        meeting_id = data.get('meeting')
        meeting = MasterLookUp.objects.get(id = meeting_id)
        departments = data.get('departments')
        point_of_discussion = data.get('point_of_discussion')
        outcome = data.get('outcome')
        decision_taken = data.get('decision_taken')
        remarks = data.get('remarks')
        task = Task.objects.get(id=task_id)


        followup_liaision.user_name = request.user
        followup_liaision.date = date
        followup_liaision.district_block_level = district_block_level
        followup_liaision.meeting_name = meeting
        followup_liaision.departments = departments
        followup_liaision.point_of_discussion = point_of_discussion
        followup_liaision.outcome = outcome
        followup_liaision.decision_taken = decision_taken
        followup_liaision.remarks = remarks
        followup_liaision.task_id = task
        followup_liaision.site_id =  current_site
        followup_liaision.save()
        return redirect('/po-report/untrust/followup-liaision-listing/'+str(task_id))
    return render(request, 'po_report/untrust/followup_liaision/edit_followup_liaision.html', locals())


@ login_required(login_url='/login/')
def participating_meeting_listing_untrust_po_report(request, task_id):
    heading = "Section 16: Details of participating in meetings at district and block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    participating_meeting = ParticipatingMeeting.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, participating_meeting)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/participating_meeting/participating_meeting_listing.html', locals())

@ login_required(login_url='/login/')
def add_participating_meeting_untrust_po_report(request, task_id):
    heading = "Section 16: Add of participating in meetings at district and block level"
    current_site = request.session.get('site_id')
    participating_meeting = ParticipatingMeeting.objects.filter()
    if request.method == 'POST':
        data = request.POST
        type_of_meeting = data.get('type_of_meeting')
        department = data.get('department')
        point_of_discussion = data.get('point_of_discussion')
        district_block_level = data.get('district_block_level')
        districit_level_officials = data.get('districit_level_officials')
        block_level = data.get('block_level')
        cluster_level = data.get('cluster_level')
        no_of_pri = data.get('no_of_pri')
        no_of_others = data.get('no_of_others')
        date = data.get('date')
        task = Task.objects.get(id=task_id)
        participating_meeting = ParticipatingMeeting.objects.create(user_name=request.user, type_of_meeting=type_of_meeting,
        department=department, point_of_discussion=point_of_discussion, districit_level_officials=districit_level_officials,
        block_level=block_level, cluster_level=cluster_level, no_of_pri=no_of_pri, no_of_others=no_of_others, 
        district_block_level=district_block_level, date=date, task=task, site_id = current_site,)
        participating_meeting.save()
        return redirect('/po-report/untrust/participating-meeting-listing/'+str(task_id))
    return render(request, 'po_report/untrust/participating_meeting/add_participating_meeting.html', locals())

@ login_required(login_url='/login/')
def edit_participating_meeting_untrust_po_report(request, participating_id, task_id):
    heading = "Section 16: Edit of participating in meetings at district and block level"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    participating_meeting = ParticipatingMeeting.objects.get(id=participating_id)
    if request.method == 'POST':
        data = request.POST
        type_of_meeting = data.get('type_of_meeting')
        department = data.get('department')
        district_block_level = data.get('district_block_level')
        point_of_discussion = data.get('point_of_discussion')
        districit_level_officials = data.get('districit_level_officials')
        block_level = data.get('block_level')
        cluster_level = data.get('cluster_level')
        no_of_pri = data.get('no_of_pri')
        no_of_others = data.get('no_of_others')
        date = data.get('date')
        task = Task.objects.get(id=task_id)

        participating_meeting.user_name = request.user
        participating_meeting.type_of_meeting = type_of_meeting
        participating_meeting.district_block_level = district_block_level
        participating_meeting.department = department
        participating_meeting.point_of_discussion = point_of_discussion
        participating_meeting.districit_level_officials = districit_level_officials
        participating_meeting.block_level = block_level
        participating_meeting.cluster_level = cluster_level
        participating_meeting.no_of_pri = no_of_pri
        participating_meeting.no_of_others = no_of_others
        participating_meeting.date = date
        participating_meeting.task_id = task
        participating_meeting.site_id =  current_site
        participating_meeting.save()
        return redirect('/po-report/untrust/participating-meeting-listing/'+str(task_id))
    return render(request, 'po_report/untrust/participating_meeting/edit_participating_meeting.html', locals())


@ login_required(login_url='/login/')
def faced_related_listing_untrust_po_report(request, task_id):
    heading = "Section 18: Details of faced related"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    faced_related = FacedRelatedOperation.objects.filter(user_name=request.user.id, task__id = task_id)
    data = pagination_function(request, faced_related)

    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'po_report/untrust/faced_related/faced_related_listing.html', locals())

@ login_required(login_url='/login/')
def add_faced_related_untrust_po_report(request, task_id):
    heading = "Section 18: Add of faced related"
    current_site = request.session.get('site_id')
    faced_related = FacedRelatedOperation.objects.filter()
    if request.method == 'POST':
        data = request.POST
        challenges = data.get('challenges')
        proposed_solution = data.get('proposed_solution')
        task = Task.objects.get(id=task_id)

        if FacedRelatedOperation.objects.filter(Q(challenges__isnull=challenges) & Q(proposed_solution__isnull=proposed_solution)).exists():
            return redirect('/po-report/untrust/faced-related-listing/'+str(task_id))
        else:
            faced_related = FacedRelatedOperation.objects.create(user_name=request.user, challenges=challenges,
            proposed_solution=proposed_solution, task=task, site_id = current_site)
            faced_related.save()
        return redirect('/po-report/untrust/faced-related-listing/'+str(task_id))
    return render(request, 'po_report/untrust/faced_related/add_faced_related.html', locals())


@ login_required(login_url='/login/')
def edit_faced_related_untrust_po_report(request, faced_related_id, task_id):
    heading = "Section 18: Edit of faced related"
    task_obj = Task.objects.get(status=1, id=task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    current_site = request.session.get('site_id')
    faced_related = FacedRelatedOperation.objects.get(id=faced_related_id)
    if request.method == 'POST':
        data = request.POST
        challenges = data.get('challenges')
        proposed_solution = data.get('proposed_solution')
        task = Task.objects.get(id=task_id)
       
        if FacedRelatedOperation.objects.filter(Q(challenges__isnull=challenges) & Q(proposed_solution__isnull=proposed_solution)).exists():
            return redirect('/po-report/fossil/faced-related-listing/'+str(task_id))
        else:
            faced_related.user_name = request.user
            faced_related.challenges = challenges
            faced_related.proposed_solution = proposed_solution
            faced_related.task_id = task
            faced_related.site_id =  current_site
            faced_related.save()
        return redirect('/po-report/untrust/faced-related-listing/'+str(task_id))
    return render(request, 'po_report/untrust/faced_related/edit_faced_related.html', locals())