from django.contrib import admin
from django.urls import path
from mis.views import *

app_name = "mis"

urlpatterns = [
    # API for checking user exist or not
    
    path('fossil/cc/monthly/report/<task_id>/', fossil_cc_monthly_report, name="fossil_cc_monthly_report"),
    path('rnp/cc/monthly/report/<task_id>/', rnp_cc_monthly_report, name="rnp_cc_monthly_report"),
    path('untrust/cc/monthly/report/<task_id>/', untrust_cc_monthly_report, name="untrust_cc_monthly_report"),
    path('fossil/po/monthly/report/<task_id>/', fossil_po_monthly_report, name="fossil_po_monthly_report"),
    path('rnp/po/monthly/report/<task_id>/', rnp_po_monthly_report, name="rnp_po_monthly_report"),
    path('untrust/po/monthly/report/<task_id>/', untrust_po_monthly_report, name="untrust_po_monthly_report"),
    path('fossil/spo/monthly/report/<task_id>/', fossil_spo_monthly_report, name="fossil_spo_monthly_report"),
    path('rnp/spo/monthly/report/<task_id>/', rnp_spo_monthly_report, name="rnp_spo_monthly_report"),
    path('untrust/spo/monthly/report/<task_id>/', untrust_spo_monthly_report, name="untrust_spo_monthly_report"),
    path('rnp/tco/monthly/report/<task_id>/', rnp_tco_monthly_report, name="rnp_tco_monthly_report"),
    path('', login_view, name="login"),
    path('login/', login_view, name="login"),
    path('add-file/', add_file, name="add_file"),
    path('monthly/report/', monthly_report, name="monthly_report"),
    path('cc/monthly/report/', cc_monthly_report, name="cc_monthly_report"),
    path('po/monthly/report/', po_monthly_report, name="po_monthly_report"),
    path('spo/monthly/report/', spo_monthly_report, name="spo_monthly_report"),
    path('logout/', logout_view, name="logout"),

    path("ajax-task/<task_id>", task_status_changes, name="submitted_approval"),
    path('ajax/adolescent/<awc_id>/', get_adolescent, name="get_adolescent"),
    path('ajax/session_name/<awc_id>/', get_session_name, name="get_session_name"),
    # path('ajax/fossil_dl_session_name/<awc_id>/', get_fossil_dl_session_name, name="get_fossil_dl_session_name"),


    #-----------cc-report  fossil---------------

    
    path('cc-report/fossil/health-sessions-listing/<task_id>/', health_sessions_listing_fossil_cc_report, name="health_sessions_listing_fossil_cc_report"),
    path('cc-report/fossil/add-health-sessions/<task_id>/', add_health_sessions_fossil_cc_report, name="add_health_sessions_fossil_cc_report"),
    path('cc-report/fossil/edit-health-sessions/<task_id>/<int:ahsession_id>/', edit_health_sessions_fossil_cc_report, name="edit_health_sessions_fossil_cc_report"),

    path('cc-report/fossil/digital-literacy-listing/<task_id>/', digital_literacy_listing_fossil_cc_report, name="digital_literacy_listing_fossil_cc_report"),
    path('cc-report/fossil/add-digital-literacy/<task_id>/', add_digital_literacy_fossil_cc_report, name="add_digital_literacy_fossil_cc_report"),
    path('cc-report/fossil/edit-digital-literacy/<task_id>/<int:dlsession_id>/', edit_digital_literacy_fossil_cc_report, name="edit_digital_literacy_fossil_cc_report"),


    path('cc-report/fossil/girls-ahwd-listing/<task_id>/', girls_ahwd_listing_fossil_cc_report, name="girls_ahwd_listing_fossil_cc_report"),
    path('cc-report/fossil/add-girls-ahwd/<task_id>/', add_girls_ahwd_fossil_cc_report, name="add_girls_ahwd_fossil_cc_report"),
    path('cc-report/fossil/edit-girls-ahwd/<task_id>/<int:girls_ahwd_id>/', edit_girls_ahwd_fossil_cc_report, name="edit_girls_ahwd_fossil_cc_report"),


    path('cc-report/fossil/boys-ahwd-listing/<task_id>/', boys_ahwd_listing_fossil_cc_report, name="boys_ahwd_listing_fossil_cc_report"),
    path('cc-report/fossil/add-boys-ahwd/<task_id>/', add_boys_ahwd_fossil_cc_report, name="add_boys_ahwd_fossil_cc_report"),
    path('cc-report/fossil/edit-boys-ahwd/<task_id>/<int:boys_ahwd_id>/', edit_boys_ahwd_fossil_cc_report, name="edit_boys_ahwd_fossil_cc_report"),     


    path('cc-report/fossil/vocation-listing/<task_id>/', vocation_listing_fossil_cc_report, name="vacation_list"),
    path('cc-report/fossil/add-vocation/<task_id>/', add_vocation_fossil_cc_report, name="add_vocation"),
    path('cc-report/fossil/edit-vocation/<task_id>/<int:vocation_id>/', edit_vocation_fossil_cc_report, name="edit_vocation"),

    path('cc-report/fossil/adolescent-referred-listing/<task_id>/', adolescents_referred_listing_fossil_cc_report, name="adolescent_referred_listing"),
    path('cc-report/fossil/add-adolescen-referred/<task_id>/', add_adolescents_referred_fossil_cc_report, name="add_adolescen_referred"),
    path('cc-report/fossil/edit-adolescen-referred/<task_id>/<int:adolescents_referred_id>/', edit_adolescents_referred_fossil_cc_report, name="edit_adolescen_referred"),


    path('cc-report/fossil/friendly-club-listing/<task_id>/', friendly_club_listing_fossil_cc_report, name="friendly_club_listing_fossil_cc_report"),
    path('cc-report/fossil/add-friendly-club/<task_id>/', add_friendly_club_fossil_cc_report, name="add_friendly_club_fossil_cc_report"),
    path('cc-report/fossil/edit-friendly-club/<task_id>/<int:friendly_club_id>/', edit_friendly_club_fossil_cc_report, name="edit_friendly_club_fossil_cc_report"),


    path('cc-report/fossil/balsansad-listing/<task_id>/', balsansad_meeting_listing_fossil_cc_report, name="balsansad_meeting_listing_fossil_cc_report"),
    path('cc-report/fossil/add-balsansad/<task_id>/', add_balsansad_meeting_fossil_cc_report, name="add_balsansad_meeting_fossil_cc_report"),
    path('cc-report/fossil/edit-balsansad/<task_id>/<int:balsansad_id>/', edit_balsansad_meeting_fossil_cc_report, name="edit_balsansad_meeting_fossil_cc_report"),

    path('cc-report/fossil/community-activities-listing/<task_id>/', community_activities_listing_fossil_cc_report, name="community_activities_listing_fossil_cc_report"),
    path('cc-report/fossil/add-community-activities/<task_id>/', add_community_activities_fossil_cc_report, name="add_community_activities_fossil_cc_report"),
    path('cc-report/fossil/edit-community-activities/<task_id>/<int:activities_id>/', edit_community_activities_fossil_cc_report, name="edit_community_activities_fossil_cc_report"),


    path('cc-report/fossil/champions-listing/<task_id>/', champions_listing_fossil_cc_report, name="champions_listing"),
    path('cc-report/fossil/add-champions/<task_id>/', add_champions_fossil_cc_report, name="add_champion"),
    path('cc-report/fossil/edit-champions/<task_id>/<int:champions_id>/', edit_champions_fossil_cc_report, name="edit_champions"),

    path('cc-report/fossil/reenrolled-listing/<task_id>/', reenrolled_listing_fossil_cc_report, name="reenrolled_listing_untrust_cc_report"),
    path('cc-report/fossil/add-reenrolled/<task_id>/', add_reenrolled_fossil_cc_report, name="add_reenrolled_fossil_cc_report"),
    path('cc-report/fossil/edit-reenrolled/<task_id>/<int:reenrolled_id>/', edit_reenrolled_fossil_cc_report, name="edit_reenrolled_fossil_cc_report"),



    #-----------cc-report  rnp---------------

    path('cc-report/rnp/health-sessions-listing/<task_id>/', health_sessions_listing_rnp_cc_report, name="health_sessions_listing_rnp_cc_report"),
    path('cc-report/rnp/add-health-sessions/<task_id>/', add_health_sessions_rnp_cc_report, name="add_health_sessions_rnp_cc_report"),
    path('cc-report/rnp/edit-health-sessions/<task_id>/<int:ahsession_id>/', edit_health_sessions_rnp_cc_report, name="edit_health_sessions_rnp_cc_report"),


    path('cc-report/rnp/girls-ahwd-listing/<task_id>/', girls_ahwd_listing_rnp_cc_report, name="girls_ahwd_listing_rnp_cc_report"),
    path('cc-report/rnp/add-girls-ahwd/<task_id>/', add_girls_ahwd_rnp_cc_report, name="add_girls_ahwd_rnp_cc_report"),
    path('cc-report/rnp/edit-girls-ahwd/<task_id>/<int:girls_ahwd_id>/', edit_girls_ahwd_rnp_cc_report, name="edit_girls_ahwd_rnp_cc_report"),


    path('cc-report/rnp/boys-ahwd-listing/<task_id>/', boys_ahwd_listing_rnp_cc_report, name="boys_ahwd_listing_rnp_cc_report"),
    path('cc-report/rnp/add-boys-ahwd/<task_id>/', add_boys_ahwd_rnp_cc_report, name="add_boys_ahwd_rnp_cc_report"),
    path('cc-report/rnp/edit-boys-ahwd/<task_id>/<int:boys_ahwd_id>/', edit_boys_ahwd_rnp_cc_report, name="edit_boys_ahwd_rnp_cc_report"),     


    path('cc-report/rnp/vocation-listing/<task_id>/', vocation_listing_rnp_cc_report, name="vocation_listing_rnp_cc_report"),
    path('cc-report/rnp/add-vocation/<task_id>/', add_vocation_rnp_cc_report, name="add_vocation_rnp_cc_report"),
    path('cc-report/rnp/edit-vocation/<task_id>/<int:vocation_id>/', edit_vocation_rnp_cc_report, name="edit_vocation_rnp_cc_report"),

    path('cc-report/rnp/adolescent-referred-listing/<task_id>/', adolescents_referred_listing_rnp_cc_report, name="adolescents_referred_listing_rnp_cc_report"),
    path('cc-report/rnp/add-adolescen-referred/<task_id>/', add_adolescents_referred_rnp_cc_report, name="add_adolescents_referred_rnp_cc_report"),
    path('cc-report/rnp/edit-adolescen-referred/<task_id>/<int:adolescents_referred_id>/', edit_adolescents_referred_rnp_cc_report, name="edit_adolescents_referred_rnp_cc_report"),


    path('cc-report/rnp/friendly-club-listing/<task_id>/', friendly_club_listing_rnp_cc_report, name="friendly_club_listing_rnp_cc_report"),
    path('cc-report/rnp/add-friendly-club/<task_id>/', add_friendly_club_rnp_cc_report, name="add_friendly_club_rnp_cc_report"),
    path('cc-report/rnp/edit-friendly-club/<task_id>/<int:friendly_club_id>/', edit_friendly_club_rnp_cc_report, name="edit_friendly_club_rnp_cc_report"),


    path('cc-report/rnp/community-activities-listing/<task_id>/', community_activities_listing_rnp_cc_report, name="community_activities_listing_rnp_cc_report"),
    path('cc-report/rnp/add-community-activities/<task_id>/', add_community_activities_rnp_cc_report, name="add_community_activities_rnp_cc_report"),
    path('cc-report/rnp/edit-community-activities/<task_id>/<int:activities_id>/', edit_community_activities_rnp_cc_report, name="edit_community_activities_rnp_cc_report"),

    path('cc-report/rnp/champions-listing/<task_id>/', champions_listing_rnp_cc_report, name="champions_listing_rnp_cc_report"),
    path('cc-report/rnp/add-champions/<task_id>/', add_champions_rnp_cc_report, name="add_champions_rnp_cc_report"),
    path('cc-report/rnp/edit-champions/<task_id>/<int:champions_id>/', edit_champions_rnp_cc_report, name="edit_champions_rnp_cc_report"),

    path('cc-report/rnp/reenrolled-listing/<task_id>/', reenrolled_listing_rnp_cc_report, name="reenrolled_listing_rnp_cc_report"),
    path('cc-report/rnp/add-reenrolled/<task_id>/', add_reenrolled_rnp_cc_report, name="add_reenrolled_rnp_cc_report"),
    path('cc-report/rnp/edit-reenrolled/<task_id>/<int:reenrolled_id>/', edit_reenrolled_rnp_cc_report, name="edit_reenrolled_rnp_cc_report"),

    path('cc-report/rnp/balsansad-listing/<task_id>/', balsansad_meeting_listing_rnp_cc_report, name="balsansad_meeting_listing_rnp_cc_report"),
    path('cc-report/rnp/add-balsansad/<task_id>/', add_balsansad_meeting_rnp_cc_report, name="add_balsansad_meeting_rnp_cc_report"),
    path('cc-report/rnp/edit-balsansad/<task_id>/<int:balsansad_id>/', edit_balsansad_meeting_rnp_cc_report, name="edit_balsansad_meeting_rnp_cc_report"),


    #-----------cc-report  untrust---------------

    path('cc-report/untrust/health-sessions-listing/<task_id>/', health_sessions_listing_untrust_cc_report, name="health_sessions_listing_untrust_cc_report"),
    path('cc-report/untrust/add-health-sessions/<task_id>/', add_health_sessions_untrust_cc_report, name="add_health_sessions_untrust_cc_report"),
    path('cc-report/untrust/edit-health-sessions/<task_id>/<int:ahsession_id>/', edit_health_sessions_untrust_cc_report, name="edit_health_sessions_untrust_cc_report"),


    path('cc-report/untrust/girls-ahwd-listing/<task_id>/', girls_ahwd_listing_untrust_cc_report, name="girls_ahwd_listing_untrust_cc_report"),
    path('cc-report/untrust/add-girls-ahwd/<task_id>/', add_girls_ahwd_untrust_cc_report, name="add_girls_ahwd_untrust_cc_report"),
    path('cc-report/untrust/edit-girls-ahwd/<task_id>/<int:girls_ahwd_id>/', edit_girls_ahwd_untrust_cc_report, name="edit_girls_ahwd_untrust_cc_report"),


    path('cc-report/untrust/boys-ahwd-listing/<task_id>/', boys_ahwd_listing_untrust_cc_report, name="boys_ahwd_listing_untrust_cc_report"),
    path('cc-report/untrust/add-boys-ahwd/<task_id>/', add_boys_ahwd_untrust_cc_report, name="add_boys_ahwd_untrust_cc_report"),
    path('cc-report/untrust/edit-boys-ahwd/<task_id>/<int:boys_ahwd_id>/', edit_boys_ahwd_untrust_cc_report, name="edit_boys_ahwd_untrust_cc_report"),     


    path('cc-report/untrust/vocation-listing/<task_id>/', vocation_listing_untrust_cc_report, name="vocation_listing_untrust_cc_report"),
    path('cc-report/untrust/add-vocation/<task_id>/', add_vocation_untrust_cc_report, name="add_vocation_untrust_cc_report"),
    path('cc-report/untrust/edit-vocation/<task_id>/<int:vocation_id>/', edit_vocation_untrust_cc_report, name="edit_vocation_untrust_cc_report"),

    path('cc-report/untrust/parents-vocation-listing/<task_id>/', parents_vocation_listing_untrust_cc_report, name="parents_vocation_listing_untrust_cc_report"),
    path('cc-report/untrust/add-parents-vocation/<task_id>/', add_parents_vocation_untrust_cc_report, name="add_parents_vocation_untrust_cc_report"),
    path('cc-report/untrust/edit-parents-vocation/<task_id>/<int:parent_id>/', edit_parents_vocation_untrust_cc_report, name="edit_parents_vocation_untrust_cc_report"),

    path('cc-report/untrust/adolescent-referred-listing/<task_id>/', adolescents_referred_listing_untrust_cc_report, name="adolescents_referred_listing_untrust_cc_report"),
    path('cc-report/untrust/add-adolescen-referred/<task_id>/', add_adolescents_referred_untrust_cc_report, name="add_adolescents_referred_untrust_po_report"),
    path('cc-report/untrust/edit-adolescen-referred/<task_id>/<int:adolescents_referred_id>/', edit_adolescents_referred_untrust_cc_report, name="edit_adolescents_referred_untrust_cc_report"),


    path('cc-report/untrust/friendly-club-listing/<task_id>/', friendly_club_listing_untrust_cc_report, name="friendly_club_listing_untrust_cc_report"),
    path('cc-report/untrust/add-friendly-club/<task_id>/', add_friendly_club_untrust_cc_report, name="add_friendly_club_untrust_cc_report"),
    path('cc-report/untrust/edit-friendly-club/<task_id>/<int:friendly_club_id>/', edit_friendly_club_untrust_cc_report, name="edit_friendly_club_untrust_cc_report"),


    path('cc-report/untrust/balsansad-listing/<task_id>/', balsansad_meeting_listing_untrust_cc_report, name="balsansad_meeting_listing_untrust_cc_report"),
    path('cc-report/untrust/add-balsansad/<task_id>/', add_balsansad_meeting_untrust_cc_report, name="add_balsansad_meeting_untrust_cc_report"),
    path('cc-report/untrust/edit-balsansad/<task_id>/<int:balsansad_id>/', edit_balsansad_meeting_untrust_cc_report, name="edit_balsansad_meeting_untrust_cc_report"),

    path('cc-report/untrust/community-activities-listing/<task_id>/', community_activities_listing_untrust_cc_report, name="community_activities_listing_untrust_cc_report"),
    path('cc-report/untrust/add-community-activities/<task_id>/', add_community_activities_untrust_cc_report, name="add_community_activities_untrust_cc_report"),
    path('cc-report/untrust/edit-community-activities/<task_id>/<int:activities_id>/', edit_community_activities_untrust_cc_report, name="edit_community_activities_untrust_cc_report"),

    path('cc-report/untrust/champions-listing/<task_id>/', champions_listing_untrust_cc_report, name="champions_listing_untrust_cc_report"),
    path('cc-report/untrust/add-champions/<task_id>/', add_champions_untrust_cc_report, name="add_champions_untrust_cc_report"),
    path('cc-report/untrust/edit-champions/<task_id>/<int:champions_id>/', edit_champions_untrust_cc_report, name="edit_champions_untrust_cc_report"),

    path('cc-report/untrust/reenrolled-listing/<task_id>/', reenrolled_listing_untrust_cc_report, name="reenrolled_listing_untrust_cc_report"),
    path('cc-report/untrust/add-reenrolled/<task_id>/', add_reenrolled_untrust_cc_report, name="add_reenrolled_untrust_cc_report"),
    path('cc-report/untrust/edit-reenrolled/<task_id>/<int:reenrolled_id>/', edit_reenrolled_untrust_cc_report, name="edit_reenrolled_untrust_cc_report"),


    path('cc-report/untrust/vlcpc-meeting-listing/<task_id>/', vlcpc_meeting_listing_untrust_cc_report, name="vlcpc_meeting_listing_untrust_cc_report"),
    path('cc-report/untrust/add-vlcpc-meeting/<task_id>/', add_vlcpc_meeting_untrust_cc_report, name="add_vlcpc_meeting_untrust_cc_report"),
    path('cc-report/untrust/edit-vlcpc-meeting/<task_id>/<int:vlcpc_metting>/', edit_vlcpc_meeting_untrust_cc_report, name="edit_vlcpc_meeting_untrust_cc_report"),

    path('cc-report/untrust/dcpu-bcpu-listing/<task_id>/', dcpu_bcpu_listing_untrust_cc_report, name="dcpu_bcpu_listing_untrust_cc_report"),
    path('cc-report/untrust/add-dcpu-bcpu/<task_id>/', add_dcpu_bcpu_untrust_cc_report, name="add_dcpu_bcpu_untrust_cc_report"),
    path('cc-report/untrust/edit-dcpu-bcpu/<task_id>/<int:dcpu_bcpu_id>/', edit_dcpu_bcpu_untrust_cc_report, name="edit_dcpu_bcpu_untrust_cc_report"),

    path('cc-report/untrust/educational-enrichment-listing/<task_id>/', educational_enrichment_listing_untrust_cc_report, name="educational_enrichment_listing_untrust_cc_report"),
    path('cc-report/untrust/add-educational-enrichment/<task_id>/', add_educational_enrichment_untrust_cc_report, name="add_educational_enrichment_untrust_cc_report"),
    path('cc-report/untrust/edit-educational-enrichment/<task_id>/<int:educational_id>/', edit_educational_enrichment_untrust_cc_report, name="edit_educational_enrichment_untrust_cc_report"),


    #-----------po-report  fossil---------------


    path('po-report/fossil/health-sessions-listing/<task_id>/', health_sessions_listing_fossil_po_report, name="health_sessions_listing_fossil_po_report"),
    path('po-report/fossil/add-health-sessions/<task_id>/', add_health_sessions_fossil_po_report, name="add_health_sessions_fossil_po_report"),
    path('po-report/fossil/edit-health-sessions/<task_id>/<int:ahsession_id>/', edit_health_sessions_fossil_po_report, name="edit_health_sessions_fossil_po_report"),

    path('po-report/fossil/digital-literacy-listing/<task_id>/', digital_literacy_listing_fossil_po_report, name="digital_literacy_listing_fossil_po_report"),
    path('po-report/fossil/add-digital-literacy/<task_id>/', add_digital_literacy_fossil_po_report, name="add_digital_literacy_fossil_po_report"),
    path('po-report/fossil/edit-digital-literacy/<task_id>/<int:dlsession_id>/', edit_digital_literacy_fossil_po_report, name="edit_digital_literacy_fossil_po_report"),

    path('po-report/fossil/girls-ahwd-listing/<task_id>/', girls_ahwd_listing_fossil_po_report, name="girls_ahwd_listing_untrust_po_report"),
    path('po-report/fossil/add-girls-ahwd/<task_id>/', add_girls_ahwd_fossil_po_report, name="add_girls_ahwd_untrust_po_report"),
    path('po-report/fossil/edit-girls-ahwd/<task_id>/<int:girls_ahwd_id>/', edit_girls_ahwd_fossil_po_report, name="edit_girls_ahwd_untrust_po_report"),


    path('po-report/fossil/boys-ahwd-listing/<task_id>/', boys_ahwd_listing_fossil_po_report, name="boys_ahwd_listing_fossil_po_report"),
    path('po-report/fossil/add-boys-ahwd/<task_id>/', add_boys_ahwd_fossil_po_report, name="add_boys_ahwd_fossil_po_report"),
    path('po-report/fossil/edit-boys-ahwd/<task_id>/<int:boys_ahwd_id>/', edit_boys_ahwd_fossil_po_report, name="edit_boys_ahwd_fossil_po_report"),     

    path('po-report/fossil/vocation-listing/<task_id>/', vocation_listing_fossil_po_report, name="vocation_listing_fossil_po_report"),
    path('po-report/fossil/add-vocation/<task_id>/', add_vocation_fossil_po_report, name="add_vocation_fossil_po_report"),
    path('po-report/fossil/edit-vocation/<task_id>/<int:vocation_id>/', edit_vocation_fossil_po_report, name="edit_vocation_fossil_po_report"),

    path('po-report/fossil/adolescent-referred-listing/<task_id>/', adolescents_referred_listing_fossil_po_report, name="adolescent_referred_listing"),
    path('po-report/fossil/add-adolescen-referred/<task_id>/', add_adolescents_referred_fossil_po_report, name="add_adolescen_referred"),
    path('po-report/fossil/edit-adolescen-referred/<task_id>/<int:adolescents_referred_id>/', edit_adolescents_referred_fossil_po_report, name="edit_adolescen_referred"),


    path('po-report/fossil/friendly-club-listing/<task_id>/', friendly_club_listing_fossil_po_report, name="friendly_club_listing_fossil_po_report"),
    path('po-report/fossil/add-friendly-club/<task_id>/', add_friendly_club_fossil_po_report, name="add_friendly_club_fossil_po_report"),
    path('po-report/fossil/edit-friendly-club/<task_id>/<int:friendly_club_id>/', edit_friendly_club_fossil_po_report, name="edit_friendly_club_fossil_po_report"),


    path('po-report/fossil/balsansad-listing/<task_id>/', balsansad_meeting_listing_fossil_po_report, name="balsansad_meeting_listing_fossil_po_report"),
    path('po-report/fossil/add-balsansad/<task_id>/', add_balsansad_meeting_fossil_po_report, name="add_balsansad_meeting_fossil_po_report"),
    path('po-report/fossil/edit-balsansad/<task_id>/<int:balsansad_id>/', edit_balsansad_meeting_fossil_po_report, name="edit_balsansad_meeting_fossil_po_report"),

    path('po-report/fossil/community-activities-listing/<task_id>/', community_activities_listing_fossil_po_report, name="community_activities_listing_fossil_po_report"),
    path('po-report/fossil/add-community-activities/<task_id>/', add_community_activities_fossil_po_report, name="add_community_activities_fossil_po_report"),
    path('po-report/fossil/edit-community-activities/<task_id>/<int:activities_id>/', edit_community_activities_fossil_po_report, name="edit_community_activities_fossil_po_report"),

    path('po-report/fossil/champions-listing/<task_id>/', champions_listing_fossil_po_report, name="champions_listing_fossil_po_report"),
    path('po-report/fossil/add-champions/<task_id>/', add_champions_fossil_po_report, name="add_champions_fossil_po_report"),
    path('po-report/fossil/edit-champions/<task_id>/<int:champions_id>/', edit_champions_fossil_po_report, name="edit_champions_fossil_po_report"),

    path('po-report/fossil/reenrolled-listing/<task_id>/', reenrolled_listing_fossil_po_report, name="reenrolled_listing_untrust_po_report"),
    path('po-report/fossil/add-reenrolled/<task_id>/', add_reenrolled_fossil_po_report, name="add_reenrolled_fossil_po_report"),
    path('po-report/fossil/edit-reenrolled/<task_id>/<int:reenrolled_id>/', edit_reenrolled_fossil_po_report, name="edit_reenrolled_fossil_po_report"),

    path('po-report/fossil/facility-visits-listing/<task_id>/', facility_visits_listing_fossil_po_report, name="facility_visits_listing_fossil_po_report"),
    path('po-report/fossil/add-facility-visits/<task_id>/', add_facility_visits_fossil_po_report, name="add_facility_visits_fossil_po_report"),
    path('po-report/fossil/edit-facility-visits/<task_id>/<int:facility_id>/', edit_facility_visits_fossil_po_report, name="edit_facility_visits_fossil_po_report"),

    path('po-report/fossil/stakeholders-listing/<task_id>/', stakeholders_listing_fossil_po_report, name="stakeholders_listing_fossil_po_report"),
    path('po-report/fossil/add_stakeholders/<task_id>/', add_stakeholders_fossil_po_report, name="add_stakeholders_fossil_po_report"),
    path('po-report/fossil/edit_stakeholders/<task_id>/<int:stakeholders_id>/', edit_stakeholders_fossil_po_report, name="edit_stakeholders_fossil_po_report"),

    path('po-report/fossil/sessions-monitoring-listing/<task_id>/', sessions_monitoring_listing_fossil_po_report, name="sessions_monitoring_listing_fossil_po_report"),
    path('po-report/fossil/add-sessions-monitoring/<task_id>/', add_sessions_monitoring_fossil_po_report, name="add_sessions_monitoring_fossil_po_report"),
    path('po-report/fossil/edit-sessions-monitoring/<task_id>/<int:sessions_id>/', edit_sessions_monitoring_fossil_po_report, name="edit_sessions_monitoring_fossil_po_report"),

    path('po-report/fossil/followup-liaision-listing/<task_id>/', followup_liaision_listing_fossil_po_report, name="participating_meeting_listing_fossil_po_report"),
    path('po-report/fossil/add-followup-liaision/<task_id>/', add_followup_liaision_fossil_po_report, name="add_followup_liaision_fossil_po_report"),
    path('po-report/fossil/edit-followup-liaision/<task_id>/<int:followup_liaision_id>/', edit_followup_liaision_fossil_po_report, name="edit_followup_liaision_fossil_po_report"),


    path('po-report/fossil/participating-meeting-listing/<task_id>/', participating_meeting_listing_fossil_po_report, name="participating_meeting_listing_fossil_po_report"),
    path('po-report/fossil/add-participating-meeting/<task_id>/', add_participating_meeting_fossil_po_report, name="add_participating_meeting_fossil_po_report"),
    path('po-report/fossil/edit-participating-meeting/<task_id>/<int:participating_id>/', edit_participating_meeting_fossil_po_report, name="edit_participating_meeting_fossil_po_report"),


    path('po-report/fossil/faced-related-listing/<task_id>/', faced_related_listing_fossil_po_report, name="faced_related_listing_fossil_po_report"),
    path('po-report/fossil/add-faced-related/<task_id>/', add_faced_related_fossil_po_report, name="add_faced_related_fossil_po_report"),
    path('po-report/fossil/edit-faced-related/<task_id>/<int:faced_related_id>/', edit_faced_related_fossil_po_report, name="edit_faced_related_fossil_po_report"),

    #-----------po-report  rnp---------------


    path('po-report/rnp/health-sessions-listing/<task_id>/', health_sessions_listing_rnp_po_report, name="health_sessions_listing_rnp_po_report"),
    path('po-report/rnp/add-health-sessions/<task_id>/', add_health_sessions_rnp_po_report, name="add_health_sessions_rnp_po_report"),
    path('po-report/rnp/edit-health-sessions/<task_id>/<int:ahsession_id>/', edit_health_sessions_rnp_po_report, name="edit_health_sessions_rnp_po_report"),

    path('po-report/rnp/girls-ahwd-listing/<task_id>/', girls_ahwd_listing_rnp_po_report, name="girls_ahwd_listing_rnp_po_report"),
    path('po-report/rnp/add-girls-ahwd/<task_id>/', add_girls_ahwd_rnp_po_report, name="add_girls_ahwd_rnp_po_report"),
    path('po-report/rnp/edit-girls-ahwd/<task_id>/<int:girls_ahwd_id>/', edit_girls_ahwd_rnp_po_report, name="edit_girls_ahwd_rnp_po_report"),


    path('po-report/rnp/boys-ahwd-listing/<task_id>/', boys_ahwd_listing_rnp_po_report, name="boys_ahwd_listing_rnp_po_report"),
    path('po-report/rnp/add-boys-ahwd/<task_id>/', add_boys_ahwd_rnp_po_report, name="add_boys_ahwd_rnp_po_report"),
    path('po-report/rnp/edit-boys-ahwd/<task_id>/<int:boys_ahwd_id>/', edit_boys_ahwd_rnp_po_report, name="edit_boys_ahwd_rnp_po_report"),  

    path('po-report/rnp/vocation-listing/<task_id>/', vocation_listing_rnp_po_report, name="vocation_listing_rnp_po_report"),
    path('po-report/rnp/add-vocation/<task_id>/', add_vocation_rnp_po_report, name="add_vocation_rnp_po_report"),
    path('po-report/rnp/edit-vocation/<task_id>/<int:vocation_id>/', edit_vocation_rnp_po_report, name="edit_vocation_rnp_po_report"),

    path('po-report/rnp/adolescent-referred-listing/<task_id>/', adolescents_referred_listing_rnp_po_report, name="adolescent_referred_listing"),
    path('po-report/rnp/add-adolescen-referred/<task_id>/', add_adolescents_referred_rnp_po_report, name="add_adolescen_referred"),
    path('po-report/rnp/edit-adolescen-referred/<task_id>/<int:adolescents_referred_id>/', edit_adolescents_referred_rnp_po_report, name="edit_adolescen_referred"),


    path('po-report/rnp/friendly-club-listing/<task_id>/', friendly_club_listing_rnp_po_report, name="friendly_club_listing_rnp_po_report"),
    path('po-report/rnp/add-friendly-club/<task_id>/', add_friendly_club_rnp_po_report, name="add_friendly_club_rnp_po_report"),
    path('po-report/rnp/edit-friendly-club/<task_id>/<int:friendly_club_id>/', edit_friendly_club_rnp_po_report, name="edit_friendly_club_rnp_po_report"),


    path('po-report/rnp/balsansad-listing/<task_id>/', balsansad_meeting_listing_rnp_po_report, name="balsansad_meeting_listing_rnp_po_report"),
    path('po-report/rnp/add-balsansad/<task_id>/', add_balsansad_meeting_rnp_po_report, name="add_balsansad_meeting_rnp_po_report"),
    path('po-report/rnp/edit-balsansad/<task_id>/<int:balsansad_id>/', edit_balsansad_meeting_rnp_po_report, name="edit_balsansad_meeting_rnp_po_report"),

    path('po-report/rnp/community-activities-listing/<task_id>/', community_activities_listing_rnp_po_report, name="community_activities_listing_rnp_po_report"),
    path('po-report/rnp/add-community-activities/<task_id>/', add_community_activities_rnp_po_report, name="add_community_activities_rnp_po_report"),
    path('po-report/rnp/edit-community-activities/<task_id>/<int:activities_id>/', edit_community_activities_rnp_po_report, name="edit_community_activities_rnp_po_report"),

    path('po-report/rnp/champions-listing/<task_id>/', champions_listing_rnp_po_report, name="champions_listing_fossil_po_report"),
    path('po-report/rnp/add-champions/<task_id>/', add_champions_rnp_po_report, name="add_champions_rnp_po_report"),
    path('po-report/rnp/edit-champions/<task_id>/<int:champions_id>/', edit_champions_rnp_po_report, name="edit_champions_rnp_po_report"),

    path('po-report/rnp/reenrolled-listing/<task_id>/', reenrolled_listing_rnp_po_report, name="reenrolled_listing_rnp_po_report"),
    path('po-report/rnp/add-reenrolled/<task_id>/', add_reenrolled_rnp_po_report, name="add_reenrolled_rnp_po_report"),
    path('po-report/rnp/edit-reenrolled/<task_id>/<int:reenrolled_id>/', edit_reenrolled_rnp_po_report, name="edit_reenrolled_rnp_po_report"),

    path('po-report/rnp/facility-visits-listing/<task_id>/', facility_visits_listing_rnp_po_report, name="facility_visits_listing_rnp_po_report"),
    path('po-report/rnp/add-facility-visits/<task_id>/', add_facility_visits_rnp_po_report, name="add_facility_visits_rnp_po_report"),
    path('po-report/rnp/edit-facility-visits/<task_id>/<int:facility_id>/', edit_facility_visits_rnp_po_report, name="edit_facility_visits_rnp_po_report"),

    path('po-report/rnp/stakeholders-listing/<task_id>/', stakeholders_listing_rnp_po_report, name="stakeholders_listing_rnp_po_report"),
    path('po-report/rnp/add_stakeholders/<task_id>/', add_stakeholders_rnp_po_report, name="add_stakeholders_rnp_po_report"),
    path('po-report/rnp/edit_stakeholders/<task_id>/<int:stakeholders_id>/', edit_stakeholders_rnp_po_report, name="edit_stakeholders_rnp_po_report"),

    path('po-report/rnp/sessions-monitoring-listing/<task_id>/', sessions_monitoring_listing_rnp_po_report, name="sessions_monitoring_listing_rnp_po_report"),
    path('po-report/rnp/add-sessions-monitoring/<task_id>/', add_sessions_monitoring_rnp_po_report, name="add_sessions_monitoring_rnp_po_report"),
    path('po-report/rnp/edit-sessions-monitoring/<task_id>/<int:sessions_id>/', edit_sessions_monitoring_rnp_po_report, name="edit_sessions_monitoring_rnp_po_report"),


    path('po-report/rnp/followup-liaision-listing/<task_id>/', followup_liaision_listing_rnp_po_report, name="participating_meeting_listing_rnp_po_report"),
    path('po-report/rnp/add-followup-liaision/<task_id>/', add_followup_liaision_rnp_po_report, name="add_followup_liaision_rnp_po_report"),
    path('po-report/rnp/edit-followup-liaision/<task_id>/<int:followup_liaision_id>/', edit_followup_liaision_rnp_po_report, name="edit_followup_liaision_rnp_po_report"),
    

    path('po-report/rnp/participating-meeting-listing/<task_id>/', participating_meeting_listing_rnp_po_report, name="participating_meeting_listing_rnp_po_report"),
    path('po-report/rnp/add-participating-meeting/<task_id>/', add_participating_meeting_rnp_po_report, name="add_participating_meeting_rnp_po_report"),
    path('po-report/rnp/edit-participating-meeting/<task_id>/<int:participating_id>/', edit_participating_meeting_rnp_po_report, name="edit_participating_meeting_rnp_po_report"),


    path('po-report/rnp/faced-related-listing/<task_id>/', faced_related_listing_rnp_po_report, name="faced_related_listing_rnp_po_report"),
    path('po-report/rnp/add-faced-related/<task_id>/', add_faced_related_rnp_po_report, name="add_faced_related_rnp_po_report"),
    path('po-report/rnp/edit-faced-related/<task_id>/<int:faced_related_id>/', edit_faced_related_rnp_po_report, name="edit_faced_related_rnp_po_report"),

    #--- ---------po-report-un-trust--------------

    path('po-report/untrust/health-sessions-listing/<task_id>/', health_sessions_listing_untrust_po_report, name="health_sessions_listing_untrust_po_report"),
    path('po-report/untrust/add-health-sessions/<task_id>/', add_health_sessions_untrust_po_report, name="add_health_sessions_untrust_po_report"),
    path('po-report/untrust/edit-health-sessions/<task_id>/<int:ahsession_id>/', edit_health_sessions_untrust_po_report, name="edit_health_sessions_untrust_po_report"),

    path('po-report/untrust/girls-ahwd-listing/<task_id>/', girls_ahwd_listing_untrust_po_report, name="girls_ahwd_listing_untrust_po_report"),
    path('po-report/untrust/add-girls-ahwd/<task_id>/', add_girls_ahwd_untrust_po_report, name="add_girls_ahwd_untrust_po_report"),
    path('po-report/untrust/edit-girls-ahwd/<task_id>/<int:girls_ahwd_id>/', edit_girls_ahwd_untrust_po_report, name="edit_girls_ahwd_untrust_po_report"),


    path('po-report/untrust/boys-ahwd-listing/<task_id>/', boys_ahwd_listing_untrust_po_report, name="boys_ahwd_listing_untrust_po_report"),
    path('po-report/untrust/add-boys-ahwd/<task_id>/', add_boys_ahwd_untrust_po_report, name="add_boys_ahwd_untrust_po_report"),
    path('po-report/untrust/edit-boys-ahwd/<task_id>/<int:boys_ahwd_id>/', edit_boys_ahwd_untrust_po_report, name="edit_boys_ahwd_untrust_po_report"),     


    path('po-report/untrust/vocation-listing/<task_id>/', vocation_listing_untrust_po_report, name="vocation_listing_untrust_po_report"),
    path('po-report/untrust/add-vocation/<task_id>/', add_vocation_untrust_po_report, name="add_vocation_untrust_po_report"),
    path('po-report/untrust/edit-vocation/<task_id>/<int:vocation_id>/', edit_vocation_untrust_po_report, name="edit_vocation_untrust_po_report"),

    path('po-report/untrust/parents-vocation-listing/<task_id>/', parents_vocation_listing_untrust_po_report, name="parents_vocation_listing_untrust_po_report"),
    path('po-report/untrust/add-parents-vocation/<task_id>/', add_parents_vocation_untrust_po_report, name="add_parents_vocation_untrust_po_report"),
    path('po-report/untrust/edit-parents-vocation/<task_id>/<int:parent_id>/', edit_parents_vocation_untrust_po_report, name="edit_parents_vocation_untrust_po_report"),

    path('po-report/untrust/adolescent-referred-listing/<task_id>/', adolescents_referred_listing_untrust_po_report, name="adolescents_referred_listing_untrust_po_report"),
    path('po-report/untrust/add-adolescen-referred/<task_id>/', add_adolescents_referred_untrust_po_report, name="add_adolescents_referred_untrust_po_report"),
    path('po-report/untrust/edit-adolescen-referred/<task_id>/<int:adolescents_referred_id>/', edit_adolescents_referred_untrust_po_report, name="edit_adolescents_referred_untrust_po_report"),


    path('po-report/untrust/friendly-club-listing/<task_id>/', friendly_club_listing_untrust_po_report, name="friendly_club_listing_untrust_po_report"),
    path('po-report/untrust/add-friendly-club/<task_id>/', add_friendly_club_untrust_po_report, name="add_friendly_club_untrust_po_report"),
    path('po-report/untrust/edit-friendly-club/<task_id>/<int:friendly_club_id>/', edit_friendly_club_untrust_po_report, name="edit_friendly_club_untrust_po_report"),



    path('po-report/untrust/balsansad-listing/<task_id>/', balsansad_meeting_listing_untrust_po_report, name="balsansad_meeting_listing_untrust_po_report"),
    path('po-report/untrust/add-balsansad/<task_id>/', add_balsansad_meeting_untrust_po_report, name="add_balsansad_meeting_untrust_po_report"),
    path('po-report/untrust/edit-balsansad/<task_id>/<int:balsansad_id>/', edit_balsansad_meeting_untrust_po_report, name="edit_balsansad_meeting_untrust_po_report"),

    path('po-report/untrust/community-activities-listing/<task_id>/', community_activities_listing_untrust_po_report, name="community_activities_listing_untrust_po_report"),
    path('po-report/untrust/add-community-activities/<task_id>/', add_community_activities_untrust_po_report, name="add_community_activities_untrust_po_report"),
    path('po-report/untrust/edit-community-activities/<task_id>/<int:activities_id>/', edit_community_activities_untrust_po_report, name="edit_community_activities_untrust_po_report"),

    path('po-report/untrust/champions-listing/<task_id>/', champions_listing_untrust_po_report, name="champions_listing_untrust_po_report"),
    path('po-report/untrust/add-champions/<task_id>/', add_champions_untrust_po_report, name="add_champions_untrust_po_report"),
    path('po-report/untrust/edit-champions/<task_id>/<int:champions_id>/', edit_champions_untrust_po_report, name="edit_champions_untrust_po_report"),

    path('po-report/untrust/reenrolled-listing/<task_id>/', reenrolled_listing_untrust_po_report, name="reenrolled_listing_untrust_po_report"),
    path('po-report/untrust/add-reenrolled/<task_id>/', add_reenrolled_untrust_po_report, name="add_reenrolled_untrust_po_report"),
    path('po-report/untrust/edit-reenrolled/<task_id>/<int:reenrolled_id>/', edit_reenrolled_untrust_po_report, name="edit_reenrolled_untrust_po_report"),


    path('po-report/untrust/vlcpc-meeting-listing/<task_id>/', vlcpc_meeting_listing_untrust_po_report, name="vlcpc_meeting_listing_untrust_po_report"),
    path('po-report/untrust/add-vlcpc-meeting/<task_id>/', add_vlcpc_meeting_untrust_po_report, name="add_vlcpc_meeting_untrust_po_report"),
    path('po-report/untrust/edit-vlcpc-meeting/<task_id>/<int:vlcpc_metting>/', edit_vlcpc_meeting_untrust_po_report, name="edit_vlcpc_meeting_untrust_po_report"),

    path('po-report/untrust/dcpu-bcpu-listing/<task_id>/', dcpu_bcpu_listing_untrust_po_report, name="dcpu_bcpu_listing_untrust_po_report"),
    path('po-report/untrust/add-dcpu-bcpu/<task_id>/', add_dcpu_bcpu_untrust_po_report, name="add_dcpu_bcpu_untrust_po_report"),
    path('po-report/untrust/edit-dcpu-bcpu/<task_id>/<int:dcpu_bcpu_id>/', edit_dcpu_bcpu_untrust_po_report, name="edit_dcpu_bcpu_untrust_po_report"),

    path('po-report/untrust/educational-enrichment-listing/<task_id>/', educational_enrichment_listing_untrust_po_report, name="educational_enrichment_listing_untrust_po_report"),
    path('po-report/untrust/add-educational-enrichment/<task_id>/', add_educational_enrichment_untrust_po_report, name="add_educational_enrichment_untrust_po_report"),
    path('po-report/untrust/edit-educational-enrichment/<task_id>/<int:educational_id>/', edit_educational_enrichment_untrust_po_report, name="edit_educational_enrichment_untrust_po_report"),


    path('po-report/untrust/facility-visits-listing/<task_id>/', facility_visits_listing_untrust_po_report, name="facility_visits_listing_untrust_po_report"),
    path('po-report/untrust/add-facility-visits/<task_id>/', add_facility_visits_untrust_po_report, name="add_facility_visits_untrust_po_report"),
    path('po-report/untrust/edit-facility-visits/<task_id>/<int:facility_id>/', edit_facility_visits_untrust_po_report, name="edit_facility_visits_untrust_po_report"),

    path('po-report/untrust/stakeholders-listing/<task_id>/', stakeholders_listing_untrust_po_report, name="stakeholders_listing_untrust_po_report"),
    path('po-report/untrust/add_stakeholders/<task_id>/', add_stakeholders_untrust_po_report, name="add_stakeholders_untrust_po_report"),
    path('po-report/untrust/edit_stakeholders/<task_id>/<int:stakeholders_id>/', edit_stakeholders_untrust_po_report, name="edit_stakeholders_untrust_po_report"),

    path('po-report/untrust/sessions-monitoring-listing/<task_id>/', sessions_monitoring_listing_untrust_po_report, name="sessions_monitoring_listing_untrust_po_report"),
    path('po-report/untrust/add-sessions-monitoring/<task_id>/', add_sessions_monitoring_untrust_po_report, name="add_sessions_monitoring_untrust_po_report"),
    path('po-report/untrust/edit-sessions-monitoring/<task_id>/<int:sessions_id>/', edit_sessions_monitoring_untrust_po_report, name="edit_sessions_monitoring_untrust_po_report"),

    path('po-report/untrust/followup-liaision-listing/<task_id>/', followup_liaision_listing_untrust_po_report, name="participating_meeting_listing_untrust_po_report"),
    path('po-report/untrust/add-followup-liaision/<task_id>/', add_followup_liaision_untrust_po_report, name="add_followup_liaision_untrust_po_report"),
    path('po-report/untrust/edit-followup-liaision/<task_id>/<int:followup_liaision_id>/', edit_followup_liaision_untrust_po_report, name="edit_followup_liaision_untrust_po_report"),

    path('po-report/untrust/participating-meeting-listing/<task_id>/', participating_meeting_listing_untrust_po_report, name="participating_meeting_listing_untrust_po_report"),
    path('po-report/untrust/add-participating-meeting/<task_id>/', add_participating_meeting_untrust_po_report, name="add_participating_meeting_untrust_po_report"),
    path('po-report/untrust/edit-participating-meeting/<task_id>/<int:participating_id>/', edit_participating_meeting_untrust_po_report, name="edit_participating_meeting_untrust_po_report"),


    path('po-report/untrust/faced-related-listing/<task_id>/', faced_related_listing_untrust_po_report, name="faced_related_listing_untrust_po_report"),
    path('po-report/untrust/add-faced-related/<task_id>/', add_faced_related_untrust_po_report, name="add_faced_related_untrust_po_report"),
    path('po-report/untrust/edit-faced-related/<task_id>/<int:faced_related_id>/', edit_faced_related_untrust_po_report, name="edit_faced_related_untrust_po_report"),


]