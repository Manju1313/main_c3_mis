from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin, ImportExportMixin
from import_export.formats import base_formats
from import_export import resources, fields
from import_export.fields import Field
from application_masters.admin import ImportExportFormat


# Register your models here.
admin.site.site_url = "/monthly/report/"
admin.site.site_header = 'C3 WEB MIS administration'
admin.site.site_title = 'C3 WEB MIS  adminsitration'
admin.site.index_title = 'C3 WEB MIS administration'

@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'user', 'start_date', 'end_date', 'task_status',
     'awc', 'extension_date', 'status' ]
    fields = ['name', 'user', 'start_date', 'end_date',
     'task_status', 'awc', 'extension_date', 'status']
    search_fields = ['name', 'user__username', ]
    list_per_page = 15

@admin.register(MonthlyReportingConfig)
class MonthlyReportingConfigAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user', 'reporting_user', 'status' ]
    fields = ['user', 'reporting_user', 'status']
    search_fields = ['user__username', ]
    list_per_page = 15

@admin.register(UserSiteMapping)
class UserSiteMappingAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user', 'site', 'status' ]
    fields = ['user', 'site', 'status']
    search_fields = ['user__username', ]
    list_per_page = 15

@admin.register(AHSession)
class AHSessionAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['adolescent_name', 'fossil_ah_session', 'age', 'gender',
     'facilitator_name', 'date_of_session', 'designation_data',
     'session_day', 'task', 'site', 'status' ]
    fields = ['adolescent_name', 'fossil_ah_session', 'age', 'gender',
     'facilitator_name', 'date_of_session', 'designation_data',
     'session_day', 'task', 'site', 'status' ]
    search_fields = ['adolescent_name__name', 'fossil_ah_session__session_name', 'task__name']
    list_per_page = 15

@admin.register(DLSession)
class DLSessionAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['adolescent_name', 'fossil_dl_session_config', 'session_name', 'date_of_session',
     'session_day', 'age', 'gender', 'designation_data', 'facilitator_name',
      'task', 'site', 'status' ]
    fields = ['adolescent_name', 'fossil_dl_session_config', 'session_name', 'date_of_session',
     'session_day', 'age', 'gender', 'designation_data', 'facilitator_name',
      'task', 'site', 'status' ]
    search_fields = ['adolescent_name__name', 'task__name']
    list_per_page = 15
    # 'fossil_dl_session_config__session_category__session_category',

@admin.register(AdolescentVocationalTraining)
class AdolescentVocationalTrainingAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['adolescent_name', 'date_of_registration', 'age',
     'parent_guardian_name', 'training_subject', 'training_providing_by',
     'duration_days', 'training_complated', 'placement_offered',
     'placement_accepted', 'type_of_employment', 'task', 'site', 'status' ]
    fields = ['adolescent_name', 'date_of_registration', 'age',
     'parent_guardian_name', 'training_subject', 'training_providing_by',
     'duration_days', 'training_complated', 'placement_offered',
     'placement_accepted', 'type_of_employment', 'task', 'site', 'status']
    search_fields = ['adolescent_name__name', 'task__name']
    list_per_page = 15

@admin.register(ParentVocationalTraining)
class ParentVocationalTrainingAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['adolescent_name',  'date_of_registration', 'age',
     'parent_name', 'training_subject', 'training_providing_by',
     'duration_days', 'training_complated', 'placement_offered',
     'placement_accepted', 'type_of_employment', 'task', 'site', 'status' ]
    fields = ['adolescent_name', 'date_of_registration', 'age',
     'parent_name', 'training_subject', 'training_providing_by',
     'duration_days', 'training_complated', 'placement_offered',
     'placement_accepted', 'type_of_employment', 'task', 'site', 'status']
    search_fields = ['adolescent_name__name', 'parent_name', 'task__name']
    list_per_page = 15

@admin.register(GirlsAHWD)
class GirlsAHWDAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['place_of_ahwd', 'date_of_ahwd', 'content_object', 'hwc_name', 'participated_10_14_years',
     'participated_15_19_years', 'bmi_10_14_years', 'bmi_15_19_years',
     'hb_10_14_years', 'hb_15_19_years', 'tt_10_14_years', 'tt_15_19_years',
     'counselling_10_14_years', 'counselling_15_19_years', 'referral_10_14_years', 
     'referral_15_19_years', 'task', 'site', 'status' ]
    fields = ['place_of_ahwd', 'date_of_ahwd', 'content_type', 'hwc_name', 'object_id','participated_10_14_years',
     'participated_15_19_years', 'bmi_10_14_years', 'bmi_15_19_years',
     'hb_10_14_years', 'hb_15_19_years', 'tt_10_14_years', 'tt_15_19_years',
     'counselling_10_14_years', 'counselling_15_19_years', 'referral_10_14_years', 
     'referral_15_19_years', 'task', 'site', 'status']
    list_filter = ['place_of_ahwd', ]
    search_fields = ['task__name']
    list_per_page = 15

@admin.register(BoysAHWD)
class BoysAHWDAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['place_of_ahwd', 'date_of_ahwd', 'content_object', 'hwc_name', 'participated_10_14_years',
     'participated_15_19_years', 'bmi_10_14_years', 'bmi_15_19_years',
     'hb_10_14_years', 'hb_15_19_years',
     'counselling_10_14_years', 'counselling_15_19_years', 'referral_10_14_years', 
     'referral_15_19_years', 'task', 'site', 'status' ]
    fields = ['place_of_ahwd', 'content_type', 'object_id', 'hwc_name', 'participated_10_14_years',
     'participated_15_19_years', 'bmi_10_14_years', 'bmi_15_19_years',
     'hb_10_14_years', 'hb_15_19_years',
     'counselling_10_14_years', 'counselling_15_19_years', 'referral_10_14_years', 
     'referral_15_19_years', 'task', 'site', 'status']
    search_fields = ['task__name']
    list_filter = ['place_of_ahwd']
    list_per_page = 15


@admin.register(AdolescentsReferred)
class AdolescentsReferredAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['awc_name', 'girls_referred_10_14_year', 'girls_referred_15_19_year',
     'boys_referred_10_14_year', 'boys_referred_15_19_year', 'girls_hwc_referred',
     'girls_hwc_visited', 'girls_afhc_referred', 'girls_afhc_visited',
     'girls_dh_referred', 'girls_dh_visited','boys_hwc_referred',
     'boys_hwc_visited', 'boys_afhc_referred', 'boys_afhc_visited',
     'boys_dh_referred', 'boys_dh_visited', 'task', 'site', 'status' ]
    fields = ['awc_name', 'girls_referred_10_14_year', 'girls_referred_15_19_year',
     'boys_referred_10_14_year', 'boys_referred_15_19_year', 'girls_hwc_referred',
     'girls_hwc_visited', 'girls_afhc_referred', 'girls_afhc_visited',
     'girls_dh_referred', 'girls_dh_visited','boys_hwc_referred',
     'boys_hwc_visited', 'boys_afhc_referred', 'boys_afhc_visited',
     'boys_dh_referred', 'boys_dh_visited', 'task', 'site', 'status']
    search_fields = ['awc_name__name', 'task__name']
    list_per_page = 15

@admin.register(AdolescentFriendlyClub)
class AdolescentFriendlyClubAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['panchayat_name', 'start_date', 'hsc_name', 'subject',
     'facilitator', 'designation', 'no_of_sahiya', 'no_of_aww', 
     'pe_girls_10_14_year', 'pe_girls_15_19_year', 'pe_boys_10_14_year', 
     'pe_boys_15_19_year', 'task', 'site', 'status' ]
    fields = ['panchayat_name', 'start_date', 'hsc_name', 'subject',
     'facilitator', 'designation', 'no_of_sahiya', 'no_of_aww', 
     'pe_girls_10_14_year', 'pe_girls_15_19_year', 'pe_boys_10_14_year', 
     'pe_boys_15_19_year', 'task', 'site', 'status' ]
    search_fields = ['panchayat_name__name', 'hsc_name', 'task__name']
    list_per_page = 15

@admin.register(BalSansadMeeting)
class BalSansadMeetingAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['school_name', 'start_date','no_of_participants', 'issues_discussion',
     'decision_taken', 'task', 'site', 'status' ]
    fields = ['school_name','start_date', 'no_of_participants', 'issues_discussion',
     'decision_taken', 'task', 'site', 'status' ]
    search_fields = ['school_name__name', 'task__name']
    list_per_page = 15

@admin.register(CommunityEngagementActivities)
class CommunityEngagementActivitiesAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['village_name','event_name','activity_name', 'name_of_event_activity', 'organized_by',
     'girls_10_14_year', 'girls_15_19_year', 'boys_10_14_year', 'boys_15_19_year',
     'champions_15_19_year', 'adult_male', 'adult_female', 'teachers', 'pri_members',
     'services_providers', 'sms_members', 'other', 'task', 'site', 'status' ]
    fields = ['village_name','event_name','activity_name', 'name_of_event_activity', 'organized_by',
     'girls_10_14_year', 'girls_15_19_year', 'boys_10_14_year', 'boys_15_19_year',
     'champions_15_19_year', 'adult_male', 'adult_female', 'teachers', 'pri_members',
     'services_providers', 'sms_members', 'other', 'task', 'site', 'status' ]
    search_fields = ['school_name__name', 'task__name']
    list_per_page = 15

@admin.register(Champions)
class ChampionsAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['awc_name', 'date_of_visit', 'girls_10_14_year', 'girls_15_19_year',
     'boys_10_14_year', 'boys_15_19_year', 'first_inst_visited', 'second_inst_visited',
     'third_inst_visited', 'task', 'site', 'status' ]
    fields = ['awc_name', 'date_of_visit',
     'girls_10_14_year', 'girls_15_19_year',
     'boys_10_14_year', 'boys_15_19_year', 'first_inst_visited', 'second_inst_visited',
     'third_inst_visited', 'task', 'site', 'status' ]
    search_fields = ['awc_name__name', 'task__name']
    list_per_page = 15

@admin.register(AdolescentRe_enrolled)
class AdolescentRe_enrolledAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['adolescent_name', 'gender', 'age', 'parent_guardian_name',
     'school_name', 'which_class_enrolled', 'task', 'site', 'status' ]
    fields = ['adolescent_name', 'gender', 'age', 'parent_guardian_name',
     'school_name', 'which_class_enrolled', 'task', 'site', 'status' ]
    search_fields = ['adolescent_name__name', 'task__name']
    list_per_page = 15


@admin.register(VLCPCMetting)
class VLCPCMettingAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['awc_name', 'date_of_meeting', 'decision_taken',
     'no_of_participants_planned', 'no_of_participants_attended',
     'issues_discussed', 'task', 'site', 'status' ]
    fields = ['awc_name', 'date_of_meeting', 'decision_taken',
     'no_of_participants_planned', 'no_of_participants_attended',
     'issues_discussed', 'task', 'site', 'status' ]
    search_fields = ['awc_name__name', 'task__name']
    list_per_page = 15

@admin.register(DCPU_BCPU)
class DCPU_BCPUAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['block_name', 'name_of_institution', 'date_of_visit', 'name_of_lead',
     'designation', 'issues_discussed', 'girls_10_14_year', 'girls_15_19_year',
     'boys_10_14_year', 'boys_15_19_year', 'champions_15_19_year', 'adult_male',
     'adult_female', 'teachers', 'pri_members', 'services_providers',
     'sms_members', 'other', 'task', 'site', 'status' ]
    fields = ['block_name', 'name_of_institution', 'date_of_visit', 'name_of_lead',
     'designation', 'issues_discussed', 'girls_10_14_year', 'girls_15_19_year',
     'boys_10_14_year', 'boys_15_19_year', 'champions_15_19_year', 'adult_male',
     'adult_female', 'teachers', 'pri_members', 'services_providers',
     'sms_members', 'other', 'task', 'site', 'status'  ]
    search_fields = ['block_name__name', 'task__name']
    list_per_page = 15

@admin.register(EducatinalEnrichmentSupportProvided)
class EducatinalEnrichmentSupportProvidedAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['adolescent_name', 'parent_guardian_name',
     'enrolment_date', 'standard', 'duration_of_coaching_support', 
     'task', 'site', 'status' ]
    fields = ['adolescent_name', 'parent_guardian_name',
     'enrolment_date', 'standard', 'duration_of_coaching_support', 
     'task', 'site', 'status' ]
    search_fields = ['adolescent_name__name', 'parent_guardian_name', 'task__name']
    list_per_page = 15

@admin.register(Stakeholder)
class StakeholderAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user_name', 'master_trainers_male', 'master_trainers_female', 'master_trainers_total',
     'nodal_teachers_male', 'nodal_teachers_female', 'nodal_teachers_total',
     'principals_male', 'principals_female', 'principals_total', 
     'district_level_officials_male', 'district_level_officials_female', 'district_level_officials_total',
     'peer_educator_male', 'peer_educator_female', 'peer_educator_total',
     'state_level_officials_male', 'state_level_officials_female', 'state_level_officials_total',
     'icds_awws_male', 'icds_awws_female', 'icds_awws_total', 'icds_supervisors_male',
     'icds_supervisors_female', 'icds_supervisors_total', 'icds_peer_educator_male',
     'icds_peer_educator_female', 'icds_peer_educator_total', 'icds_child_developement_project_officers_male',
     'icds_child_developement_project_officers_female', 'icds_child_developement_project_officers_total',
     'icds_district_level_officials_male', 'icds_district_level_officials_female',
     'icds_district_level_officials_total', 'icds_state_level_officials_male',
     'icds_state_level_officials_female', 'icds_state_level_officials_total',
     'health_ashas_male', 'health_ashas_female', 'health_ashas_total', 'health_bpm_bhm_pheos_male',
     'health_bpm_bhm_pheos_female', 'health_bpm_bhm_pheos_total', 'health_medical_officers_male',
     'health_medical_officers_female', 'health_medical_officers_total', 'health_district_level_officials_male',
     'health_district_level_officials_female', 'health_district_level_officials_total',
     'health_state_level_officials_male', 'health_state_level_officials_female',
     'health_state_level_officials_total', 'health_rsk_male', 'health_rsk_female',
     'health_rsk_total', 'health_peer_educator_male', 'health_peer_educator_female',
     'health_peer_educator_total', 'panchayat_ward_members_male', 'panchayat_ward_members_female',
     'panchayat_ward_members_total', 'panchayat_up_mukhiya_up_Pramukh_male',
     'panchayat_up_mukhiya_up_Pramukh_female', 'panchayat_up_mukhiya_up_Pramukh_total',
     'panchayat_mukhiya_Pramukh_male', 'panchayat_mukhiya_Pramukh_female', 'panchayat_mukhiya_Pramukh_total',
     'panchayat_samiti_member_male', 'panchayat_samiti_member_female', 'panchayat_samiti_member_total',
     'panchayat_zila_parishad_member_male', 'panchayat_zila_parishad_member_female',
     'panchayat_zila_parishad_member_total', 'panchayat_vc_zila_parishad_male',
     'panchayat_vc_zila_parishad_female', 'panchayat_vc_zila_parishad_total', 'panchayat_chairman_zila_parishad_male',
     'panchayat_chairman_zila_parishad_female', 'panchayat_chairman_zila_parishad_total',
     'panchayat_block_level_officials_male', 'panchayat_block_level_officials_female', 'panchayat_block_level_officials_total',
     'panchayat_district_level_officials_male', 'panchayat_district_level_officials_female',
     'panchayat_district_level_officials_total', 'panchayat_state_level_officials_male',
     'panchayat_state_level_officials_female', 'panchayat_state_level_officials_total',
     'media_interns_male', 'media_interns_female', 'media_interns_total', 'media_journalists_male',
     'media_journalists_female', 'media_journalists_total', 'media_editors_male',
     'media_editors_female', 'media_editors_total', 'others_block_cluster_field_corrdinators_male',
     'others_block_cluster_field_corrdinators_female', 'others_block_cluster_field_corrdinators_total',
     'others_ngo_staff_corrdinators_male', 'others_ngo_staff_corrdinators_female',
     'others_ngo_staff_corrdinators_total', 'others_male', 'others_female', 'others_total',
     'total_male', 'total_female', 'total', 'task', 'site', 'status' ]
    fields = ['user_name', 'master_trainers_male', 'master_trainers_female', 'master_trainers_total',
     'nodal_teachers_male', 'nodal_teachers_female', 'nodal_teachers_total',
     'principals_male', 'principals_female', 'principals_total', 
     'district_level_officials_male', 'district_level_officials_female', 'district_level_officials_total',
     'peer_educator_male', 'peer_educator_female', 'peer_educator_total',
     'state_level_officials_male', 'state_level_officials_female', 'state_level_officials_total',
     'icds_awws_male', 'icds_awws_female', 'icds_awws_total', 'icds_supervisors_male',
     'icds_supervisors_female', 'icds_supervisors_total', 'icds_peer_educator_male',
     'icds_peer_educator_female', 'icds_peer_educator_total', 'icds_child_developement_project_officers_male',
     'icds_child_developement_project_officers_female', 'icds_child_developement_project_officers_total',
     'icds_district_level_officials_male', 'icds_district_level_officials_female',
     'icds_district_level_officials_total', 'icds_state_level_officials_male',
     'icds_state_level_officials_female', 'icds_state_level_officials_total',
     'health_ashas_male', 'health_ashas_female', 'health_ashas_total','health_anms_male',
     'health_anms_female', 'health_anms_total', 'health_bpm_bhm_pheos_male',
     'health_bpm_bhm_pheos_female', 'health_bpm_bhm_pheos_total', 'health_medical_officers_male',
     'health_medical_officers_female', 'health_medical_officers_total', 'health_district_level_officials_male',
     'health_district_level_officials_female', 'health_district_level_officials_total',
     'health_state_level_officials_male', 'health_state_level_officials_female',
     'health_state_level_officials_total', 'health_rsk_male', 'health_rsk_female',
     'health_rsk_total', 'health_peer_educator_male', 'health_peer_educator_female',
     'health_peer_educator_total', 'panchayat_ward_members_male', 'panchayat_ward_members_female',
     'panchayat_ward_members_total', 'panchayat_up_mukhiya_up_Pramukh_male',
     'panchayat_up_mukhiya_up_Pramukh_female', 'panchayat_up_mukhiya_up_Pramukh_total',
     'panchayat_mukhiya_Pramukh_male', 'panchayat_mukhiya_Pramukh_female', 'panchayat_mukhiya_Pramukh_total',
     'panchayat_samiti_member_male', 'panchayat_samiti_member_female', 'panchayat_samiti_member_total',
     'panchayat_zila_parishad_member_male', 'panchayat_zila_parishad_member_female',
     'panchayat_zila_parishad_member_total', 'panchayat_vc_zila_parishad_male',
     'panchayat_vc_zila_parishad_female', 'panchayat_vc_zila_parishad_total', 'panchayat_chairman_zila_parishad_male',
     'panchayat_chairman_zila_parishad_female', 'panchayat_chairman_zila_parishad_total',
     'panchayat_block_level_officials_male', 'panchayat_block_level_officials_female', 'panchayat_block_level_officials_total',
     'panchayat_district_level_officials_male', 'panchayat_district_level_officials_female',
     'panchayat_district_level_officials_total', 'panchayat_state_level_officials_male',
     'panchayat_state_level_officials_female', 'panchayat_state_level_officials_total',
     'media_interns_male', 'media_interns_female', 'media_interns_total', 'media_journalists_male',
     'media_journalists_female', 'media_journalists_total', 'media_editors_male',
     'media_editors_female', 'media_editors_total', 'others_block_cluster_field_corrdinators_male',
     'others_block_cluster_field_corrdinators_female', 'others_block_cluster_field_corrdinators_total',
     'others_ngo_staff_corrdinators_male', 'others_ngo_staff_corrdinators_female',
     'others_ngo_staff_corrdinators_total', 'others_male', 'others_female', 'others_total',
     'total_male', 'total_female', 'total', 'task', 'site', 'status']
    search_fields = ['user_name__username', 'task__name']
    list_per_page = 15

@admin.register(SessionMonitoring)
class SessionMonitoringAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name_of_visited', 'name_of_place_visited', 'date', 'content_object',
     'session_attended', 'observation', 'recommendation',
     'task', 'site', 'status' ]
    fields = ['name_of_visited', 'name_of_place_visited', 'date', 'content_type', 'object_id',
     'session_attended', 'observation', 'recommendation',
     'task', 'site', 'status'  ]
    list_filter = ['name_of_visited', 'task__name']
    list_per_page = 15

@admin.register(Events)
class EventsAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name_of_visited', 'name_of_place_visited', 'date', 'content_object',
     'purpose_visited', 'observation', 'recommendation', 
     'task', 'site', 'status' ]
    fields = ['name_of_visited', 'name_of_place_visited', 'date', 'content_type', 'object_id',
     'purpose_visited', 'observation', 'recommendation', 
     'task', 'site', 'status'  ]
    list_filter = ['name_of_visited']
    search_fields = ['task__name']
    list_per_page = 15

@admin.register(ParticipatingMeeting)
class ParticipatingMeetingAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user_name',  
     'type_of_meeting', 'department', 'point_of_discussion', 'districit_level_officials', 
     'block_level', 'cluster_level', 'no_of_pri', 'no_of_others', 'date',
     'task', 'site', 'status' ]
    fields = ['user_name', 
     'type_of_meeting', 'department', 'point_of_discussion', 'districit_level_officials', 
     'block_level', 'cluster_level', 'no_of_pri', 'no_of_others', 'date',
     'task', 'site', 'status' ]
    search_fields = ['user_name__username', 'task__name']
    list_per_page = 15


@admin.register(FollowUP_LiaisionMeeting)
class FollowUP_LiaisionMeetingAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user_name', 'date', 'district_block_level', 'meeting_name', 'departments', 'outcome', 'point_of_discussion',
     'decision_taken', 'remarks', 'task', 'site', 'status' ]
    fields = ['user_name', 'date', 'district_block_level', 'meeting_name', 'departments', 'outcome', 'point_of_discussion',
     'decision_taken', 'remarks', 'task', 'site', 'status' ]
    search_fields = ['user_name__username',  'task__name']
    list_per_page = 15

@admin.register(FacedRelatedOperation)
class FacedRelatedOperationAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user_name', 'challenges', 'proposed_solution',
     'task', 'site', 'status' ]
    fields = ['user_name', 'challenges', 'proposed_solution',
     'task', 'site', 'status'  ]
    search_fields = ['user_name__username',  'task__name']
    list_per_page = 15


@admin.register(CCReportNotes)
class CCReportNotesAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['successes', 'challenges_faced', 'feasible_solution_to_scale_up',
     'task', 'site', 'status' ]
    fields = ['successes', 'challenges_faced', 'feasible_solution_to_scale_up',
     'task', 'site', 'status' ]
    search_fields = ['successes', 'task__name']
    list_per_page = 15

@admin.register(POReportSection17)
class POReportSection17Admin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['suggestions', 'task', 'site', 'status' ]
    fields = ['suggestions', 'task', 'site', 'status' ]
    search_fields = ['suggestions', 'task__name']
    list_per_page = 15


@admin.register(DataEntryRemark)
class DataEntryRemarkAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['task', 'remark' ]
    fields = ['task', 'remark' ]
    search_fields = ['task__name']

@admin.register(Logged)
class LoggedAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user', 'month', 'error_message' ]
    fields = ['user', 'month', 'error_message']

# @admin.register(ReportSection3)
# class ReportSection3Admin(admin.ModelAdmin):
#     list_display = ['name_of_block', 'name_of_panchayat', 'name_of_village','name_of_awc_code','number_adolescent_girls_linked','number_girls_completed_training','number_girls_accepted_placement','number_of_girls_offered_placement','task','site']
#     fields = ['name_of_block', 'name_of_panchayat', 'name_of_village','name_of_awc_code','number_adolescent_girls_linked','number_girls_completed_training','number_girls_accepted_placement','number_of_girls_offered_placement','task','site']


# @admin.register(ReportSection7)
# class ReportSection7Admin(admin.ModelAdmin):
#     list_display = ['name_of_block','name_of_panchayat','school_name','no_of_participants','number_issues_discussed','number_decision_taken'
# ,'task','site']
#     fields = ['name_of_block','name_of_panchayat','school_name','no_of_participants','number_issues_discussed','number_decision_taken'
# ,'task','site']


# @admin.register(ReportSection4a)
# class ReportSection4aAdmin(admin.ModelAdmin):
#     list_display = ['name_of_block','name_of_panchayat','name_of_village','name_of_awc_code','participated_10_14_years','bmi_10_14_year','bmi_15_19_year','hb_test_10_14_year','hb_test_15_19_year','tt_shot_10_14_year','tt_shot_15_19_year','counselling_10_14_year','counselling_15_19_year','referral_10_14_year','referral_15_19_year','task','site']
#     fields = ['name_of_block','name_of_panchayat','name_of_village','name_of_awc_code','participated_10_14_years','bmi_10_14_year','bmi_15_19_year','hb_test_10_14_year','hb_test_15_19_year','tt_shot_10_14_year','tt_shot_15_19_year','counselling_10_14_year','counselling_15_19_year','referral_10_14_year','referral_15_19_year','task','site']

# @admin.register(ReportSection4b)
# class ReportSection4bAdmin(admin.ModelAdmin):
#     list_display = ['name_of_block','name_of_panchayat','name_of_village','name_of_awc_code','participated_10_14_years','bmi_10_14_year','bmi_15_19_year','hb_test_10_14_year','hb_test_15_19_year','tt_shot_10_14_year','tt_shot_15_19_year','counselling_10_14_year','counselling_15_19_year','referral_10_14_year','referral_15_19_year','task','site']
#     fields = ['name_of_block','name_of_panchayat','name_of_village','name_of_awc_code','participated_10_14_years','bmi_10_14_year','bmi_15_19_year','hb_test_10_14_year','hb_test_15_19_year','tt_shot_10_14_year','tt_shot_15_19_year','counselling_10_14_year','counselling_15_19_year','referral_10_14_year','referral_15_19_year','task','site']

@admin.register(ReportSection1)
class AdminReportSection1(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection2)
class AdminReportSection2(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection3)
class AdminReportSection3(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection4a)
class AdminReportSection4a(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection4b)
class AdminReportSection4b(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection5)
class AdminReportSection5(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection6)
class AdminReportSection6(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection7)
class AdminReportSection7(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection8)
class AdminReportSection8(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection9)
class AdminReportSection9(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ReportSection10)
class AdminReportSection10(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(HistoryRecord)
class AdminHistoryRecord(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UntrustVLCPCMetting)
class AdminUntrustVLCPCMetting(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UntrustDCPU_BCPU)
class AdminUntrustDCPU_BCPU(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UntrustEducatinalEnrichmentSupportProvided)
class AdminUntrustEducatinalEnrichmentSupportProvided(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UntrustParentVocationalTraining)
class AdminUntrustParentVocationalTraining(ImportExportModelAdmin, ImportExportFormat):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]