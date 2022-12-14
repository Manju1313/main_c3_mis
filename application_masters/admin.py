from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin, ImportExportMixin
from import_export.formats import base_formats
from import_export import resources, fields
from import_export.fields import Field

# Register your models here.

class ImportExportFormat(ImportExportMixin):
    def get_export_formats(self):
        formats = (base_formats.CSV, base_formats.XLSX, base_formats.XLS,)
        return [f for f in formats if f().can_export()]

    def get_import_formats(self):
        formats = (base_formats.CSV, base_formats.XLSX, base_formats.XLS,)
        return [f for f in formats if f().can_import()]

@admin.register(State)
class StateAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'status' ]
    fields = ['name', 'status']
    search_fields = ['name',  ]
    ordering = ['name']
    list_per_page = 15
    
@admin.register(TrainingSubject)
class TrainingSubjectAdmin(admin.ModelAdmin):
    list_display = ['training_subject', ]
    fields = ['training_subject',]

@admin.register(MasterLookUp)
class MasterLookUpAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'order']
    fields = ['name', 'parent', 'slug', 'order']

@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'state', 'status']
    fields = ['name', 'state', 'status']
    search_fields = ['name', 'state__name']
    ordering = ['name']
    list_per_page = 15

@admin.register(Block)
class BlockAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'district', 'status']
    fields = ['name', 'district', 'status']
    search_fields = ['name', 'district__name']
    ordering = ['name']
    list_per_page = 15

@admin.register(GramaPanchayat)
class GramaPanchayatAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'block', 'status']
    fields = ['name', 'block', 'status']
    search_fields = ['name', 'block__name']
    ordering = ['name']
    list_per_page = 15

@admin.register(Village)
class VillageAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'grama_panchayat', 'status']
    fields = ['name', 'grama_panchayat', 'status']
    search_fields = ['name', 'grama_panchayat__name', ]
    ordering = ['name']
    list_per_page = 15

@admin.register(School)
class SchoolAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'village', 'code', 'status']
    fields = ['name', 'village', 'code', 'status']
    search_fields = ['name', 'code', 'village__name']
    ordering = ['village__name']
    ordering = ['name']
    list_per_page = 15

@admin.register(AWC)
class AWCAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['id', 'name', 'village', 'code', 'status']
    fields = ['name', 'code', 'village', 'status']
    search_fields = ['id', 'name', 'code', 'village__name']
    ordering = ['name']
    list_per_page = 15

@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'awc', 'status']
    fields = ['name', 'awc', 'status']
    search_fields = ['name', 'awc__name']
    ordering = ['name']
    list_per_page = 15

@admin.register(Adolescent)
class AdolescentAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['name', 'awc', 'code', 'group', 'gender', 'age_in_completed_years', 'site', 'status']
    fields = ['name', 'awc', 'code', 'group', 'gender', 'age_in_completed_years', 'site',  'status']
    search_fields = ['name', 'awc__name', 'group__name']
    ordering = ['name']
    list_per_page = 15

@admin.register(FossilDLSessionCategory)
class FossilDLSessionCategoryAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['session_category', 'status']
    fields = ['session_category', 'status']
    search_fields = ['session_category', ]
    ordering = ['session_category']
    list_per_page = 15

@admin.register(FossilDLSessionConfig)
class FossilDLSessionConfigAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['session_category', 'session_type', 'scheduled_days', 'status']
    fields = ['session_category', 'session_type', 'scheduled_days', 'status']
    search_fields = ['session_category__session_category', ]
    ordering = ['session_category']
    list_per_page = 15
    
@admin.register(FossilAHSessionCategory)
class FossilAHSessionCategoryAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['session_category', 'status']
    fields = ['session_category', 'status']
    search_fields = ['session_category', ]
    ordering = ['session_category']
    list_per_page = 15

@admin.register(FossilAHSession)
class FossilAHSessionAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['session_name', 'fossil_ah_session_category', 'no_of_days', 'status']
    fields = ['session_name', 'fossil_ah_session_category',  'no_of_days', 'status']
    search_fields = ['session_name', 'fossil_ah_session_category__session_category', ]
    ordering = ['session_name']
    list_per_page = 15



@admin.register(CC_AWC_AH)
class CC_AWC_AHAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user', 'awc', 'deactivated_date', 'status' ]
    fields = ['user', 'awc', 'deactivated_date', 'status']
    search_fields = ['user__username', 'awc__name', ]
    # ordering = ['user__username']
    list_per_page = 15

@admin.register(CC_AWC_DL)
class CC_AWC_DLAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user', 'awc', 'deactivated_date', 'status' ]
    fields = ['user', 'awc', 'deactivated_date', 'status']
    search_fields = ['user__username', 'awc__name', ]
    list_per_page = 15

@admin.register(CC_School)
class CC_SchoolAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user', 'school', 'deactivated_date', 'status' ]
    fields = ['user', 'school', 'deactivated_date', 'status']
    search_fields = ['user__username', 'school__name', ]
    list_per_page = 15


@admin.register(MisReport)
class MisReportAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['report_person', 'report_to', 'status']
    fields = ['report_person', 'report_to', 'status']
    search_fields = ['report_person__username', 'report_to__username', ]
    list_per_page = 15


