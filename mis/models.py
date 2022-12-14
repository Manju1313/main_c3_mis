from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.postgres.fields import ArrayField
from django.contrib.sites.models import Site
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from application_masters.models import *


# Create your models here.
DESIGNATION_CHOICES = (
        (1, 'ANM'),
        (2, 'Sahiya'),
        (3, 'Sevika'),
        (4, 'Peer Educator'),
        (5, 'Cluster Coordinator'),
        (6, 'Project Officer'),
        (7, 'SPO'),
        (8, 'Others')
    )
class Task(BaseContent):
    STATUS_CHOICE = ((1, 'Pending'), (2, 'Submitted for approval'),
    (3, 'Approved'), (4, 'Rejected'), (5, 'Cancelled'),)
    name = models.CharField(max_length=150)
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING
        )
    start_date = models.DateField()
    end_date = models.DateField()
    task_status = models.IntegerField(choices=STATUS_CHOICE)
    awc = ArrayField(models.CharField(max_length=512, blank=True), null=True)
    extension_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name 

class MonthlyReportingConfig(BaseContent):
    user = models.OneToOneField(
        User, on_delete=models.DO_NOTHING, related_name='user')
    reporting_user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name='reporting_user')
   

    def __str__(self):
        return self.user.username

class UserSiteMapping(BaseContent):
    user = models.OneToOneField(
        User, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)
    #reporing_persons = models.fk(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.user.username

class AHSession(BaseContent):
    DAY_CHOICES = (
        (1, 'Day-1'),
        (2, 'Day-2'),
        (3, 'Day-3')
    )
    GENDER_CHOICE = (
        (1, 'Male'),
        (2, 'Female')
        )
    adolescent_name = models.ForeignKey(
        Adolescent, on_delete=models.DO_NOTHING)
    fossil_ah_session = models.ForeignKey(
        FossilAHSession, on_delete=models.DO_NOTHING)
    gender = models.IntegerField(choices=GENDER_CHOICE, blank=True, null=True)
    date_of_session = models.DateField()
    session_days = models.IntegerField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    session_day = models.IntegerField(choices=DAY_CHOICES, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)
    designation_data = models.IntegerField(choices = DESIGNATION_CHOICES, null=True, blank=True)
    facilitator_name = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        verbose_name_plural = "AH Session"

    def __str__(self):
        return self.adolescent_name.name

class DLSession(BaseContent):
    DAY_CHOICES = (
        (1, 'Day-1'),
        (2, 'Day-2'),
        (3, 'Day-3'),
        (4, 'Day-4'),
        (5, 'Day-5'),
        (6, 'Day-6'),
        (7, 'Day-7'),
        (8, 'Day-8'),
        (9, 'Day-9')
    )
    GENDER_CHOICE = (
        (1, 'Male'),
        (2, 'Female')
        )
    SESSION_CHOICES = (
        (1, 'Theroy'), 
        (2, 'Practical'),
        )
    adolescent_name = models.ForeignKey(
        Adolescent, on_delete=models.DO_NOTHING)
    fossil_dl_session_config = models.ForeignKey(
        FossilDLSessionConfig, on_delete=models.DO_NOTHING)
    session_name = models.IntegerField(choices=SESSION_CHOICES, null=True, blank=True)
    gender = models.IntegerField(choices=GENDER_CHOICE, blank=True, null=True)
    date_of_session = models.DateField()
    age = models.IntegerField(blank=True, null=True)
    session_days = models.IntegerField(blank=True, null=True)
    session_day = models.IntegerField(choices=DAY_CHOICES, null=True, blank=True)
    designation_data = models.IntegerField(choices = DESIGNATION_CHOICES, null=True, blank=True)
    facilitator_name = models.CharField(max_length=150, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "DL Session"


    def __str__(self):
        return self.adolescent_name.name

# Section 3(a): 
# Details of adolescent girls linked with vocational training & placement 




class AdolescentVocationalTraining(BaseContent):
    TRAIN_CHOICES = (
    (1, 'JSLPS'),
    (2, 'SGRS Pvt. Ltd.'),
    (3, 'Vikas Bharti'),
    (4, 'Others')
    )
    adolescent_name = models.ForeignKey(
        Adolescent, on_delete=models.DO_NOTHING)
    date_of_registration = models.DateField()
    age = models.PositiveIntegerField(blank=True, null=True)
    parent_guardian_name = models.CharField(max_length=150)
    training_subject = models.ForeignKey(TrainingSubject, on_delete=models.DO_NOTHING, null=True, blank=True)
    training_providing_by = models.IntegerField(choices = TRAIN_CHOICES, null=True, blank=True)
    duration_days = models.IntegerField(blank=True, null=True)
    training_complated = models.IntegerField(choices=((1, 'Yes'), (2, 'No'),), null=True, blank=True)
    placement_offered = models.IntegerField(choices=((1, 'Yes'), (2, 'No'),), null=True, blank=True)
    placement_accepted = models.PositiveIntegerField(choices=((1, 'Accepted'),
     (2, 'Not accepted'),), null=True, blank=True)
    type_of_employment = models.PositiveIntegerField(choices=((1, 'Full time'),
     (2, 'Part time'), (3, 'Apprentice'),), null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    
    def __str__(self):
        return self.adolescent_name.name


class ParentVocationalTraining(BaseContent):
    TRAIN_CHOICES = (
    (1, 'JSLPS'),
    (2, 'SGRS Pvt. Ltd.'),
    (3, 'Vikas Bharti'),
    (4, 'Others')
    )
    adolescent_name = models.ForeignKey(
        Adolescent, on_delete=models.DO_NOTHING)
    date_of_registration = models.DateField()
    age = models.PositiveIntegerField(blank=True, null=True)
    parent_name = models.CharField(max_length=150)
    training_subject = models.ForeignKey(TrainingSubject, on_delete=models.DO_NOTHING, null=True, blank=True)
    training_providing_by = models.IntegerField(choices = TRAIN_CHOICES, null=True, blank=True)
    duration_days = models.IntegerField(blank=True, null=True)
    training_complated = models.IntegerField(choices=((1, 'Yes'), (2, 'No'),), null=True, blank=True)
    placement_offered = models.IntegerField(choices=((1, 'Yes'), (2, 'No'),), null=True, blank=True)
    placement_accepted = models.PositiveIntegerField(choices=((1, 'Accepted'),
     (2, 'Not accepted'),), null=True, blank=True)
    type_of_employment = models.PositiveIntegerField(choices=((1, 'Full time'),
     (2, 'Part time'), (3, 'Apprentice'),), null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    
    def __str__(self):
        return self.adolescent_name.name

# Section 4(a): 
# Details of participation of adolescent girls in Adolescent Health Wellness Day (AHWD)

class GirlsAHWD(BaseContent):
    AHWD_CHOICES = ((1, 'AWC'), (2, 'School'), (3, 'HWC'))

    place_of_ahwd = models.IntegerField(choices=AHWD_CHOICES, null=True, blank=True)
    date_of_ahwd = models.DateField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    hwc_name = models.CharField(max_length=150, blank=True, null=True)
    participated_10_14_years = models.IntegerField(blank=True, null=True)
    participated_15_19_years = models.IntegerField(blank=True, null=True)
    bmi_10_14_years = models.IntegerField(blank=True, null=True)
    bmi_15_19_years = models.IntegerField(blank=True, null=True)
    hb_10_14_years = models.IntegerField(blank=True, null=True)
    hb_15_19_years = models.IntegerField(blank=True, null=True)
    tt_10_14_years = models.IntegerField(blank=True, null=True)
    tt_15_19_years = models.IntegerField(blank=True, null=True)
    counselling_10_14_years = models.IntegerField(blank=True, null=True)
    counselling_15_19_years = models.IntegerField(null=True, blank=True)
    referral_10_14_years = models.IntegerField(null=True, blank=True)
    referral_15_19_years = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Girls AHWD"


    # def __str__(self):
    #     return self.place_of_ahwd

class BoysAHWD(BaseContent):
    AHWD_CHOICES = ((1, 'AWC'), (2, 'School'), (3, 'HWC'))

    date_of_ahwd = models.DateField(null=True, blank=True)
    place_of_ahwd = models.IntegerField(choices=AHWD_CHOICES, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    hwc_name = models.CharField(max_length=150, blank=True, null=True)
    participated_10_14_years = models.IntegerField(null=True, blank=True)
    participated_15_19_years = models.IntegerField(null=True, blank=True)
    bmi_10_14_years = models.IntegerField(blank=True, null=True)
    bmi_15_19_years = models.IntegerField(blank=True, null=True)
    hb_10_14_years = models.IntegerField(blank=True, null=True)
    hb_15_19_years = models.IntegerField(blank=True, null=True)
    counselling_10_14_years = models.IntegerField(null=True, blank=True)
    counselling_15_19_years = models.IntegerField(null=True, blank=True)
    referral_10_14_years = models.IntegerField(null=True, blank=True)
    referral_15_19_years = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Boys AHWD"

    # def __str__(self):
    #     return self.place_of_ahwd

# Section 5: 
# Details of adolescents referred 

class AdolescentsReferred(BaseContent):
    awc_name = models.ForeignKey(
        AWC, on_delete=models.DO_NOTHING)
    girls_referred_10_14_year = models.IntegerField(null=True, blank=True)
    girls_referred_15_19_year = models.IntegerField(null=True, blank=True)
    boys_referred_10_14_year = models.IntegerField(null=True, blank=True)
    boys_referred_15_19_year = models.IntegerField(null=True, blank=True)
    girls_hwc_referred = models.IntegerField(null=True, blank=True)
    girls_hwc_visited = models.IntegerField(null=True, blank=True)
    girls_afhc_referred = models.IntegerField(null=True, blank=True)
    girls_afhc_visited = models.IntegerField(null=True, blank=True)
    girls_dh_referred = models.IntegerField(null=True, blank=True)
    girls_dh_visited = models.IntegerField(null=True, blank=True)
    boys_hwc_referred = models.IntegerField(null=True, blank=True)
    boys_hwc_visited = models.IntegerField(null=True, blank=True)
    boys_afhc_referred = models.IntegerField(null=True, blank=True)
    boys_afhc_visited = models.IntegerField(null=True, blank=True)
    boys_dh_referred = models.IntegerField(null=True, blank=True)
    boys_dh_visited = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Adolecents Referred"

    

    def __str__(self):
        return self.awc_name.name

# Section 6: 
# Details of Adolescent Friendly Club (AFC) 

class AdolescentFriendlyClub(BaseContent):
    panchayat_name = models.ForeignKey(
        GramaPanchayat, on_delete=models.DO_NOTHING)
    hsc_name = models.CharField(max_length=150)
    start_date = models.DateField(null=True, blank=True)
    subject = models.TextField(null=True, blank=True)
    facilitator = models.CharField(max_length=150)
    designation = models.IntegerField(choices = DESIGNATION_CHOICES, null=True, blank=True)
    no_of_sahiya = models.IntegerField(null=True, blank=True)
    no_of_aww = models.IntegerField(null=True, blank=True)
    pe_girls_10_14_year = models.IntegerField(null=True, blank=True)
    pe_girls_15_19_year = models.IntegerField(null=True, blank=True)
    pe_boys_10_14_year = models.IntegerField(null=True, blank=True)
    pe_boys_15_19_year = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Adolescent Friendly Club"

    def __str__(self):
        return self.hsc_name


# Section 7: 
# Details of Bal Sansad meetings conducted 

class BalSansadMeeting(BaseContent):
    school_name = models.ForeignKey(
        School, on_delete=models.DO_NOTHING)
    no_of_participants = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    # issues_discussed = models.TextField(null=True, blank=True)
    decision_taken = models.CharField(max_length=250, null=True, blank=True)
    issues_discussion = models.ForeignKey(MasterLookUp, on_delete=models.DO_NOTHING, related_name='issues_discussion', null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "BalSansad Meeting"


    def __str__(self):
        return self.school_name.name
# Section 8: 
# Details of community engagement activities 

class CommunityEngagementActivities(BaseContent):
    ORGANIZED_CHOICES = ((1, 'C3'), (2, 'Govt.'),)
    EVENT_ACTIVITY_CHOICES = ((1, 'Event'), (2, 'Activity'),)
    # THEME_TOPIC_CHOICES = ((1, 'Theme'), (2, 'Topic'))
    village_name = models.ForeignKey(
        Village, on_delete=models.DO_NOTHING, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    name_of_event_activity = models.IntegerField(choices=EVENT_ACTIVITY_CHOICES, null=True, blank=True)
    organized_by = models.IntegerField(choices=ORGANIZED_CHOICES, null=True, blank=True)

    # theme_topic = models.IntegerField(choices=THEME_TOPIC_CHOICES, null=True, blank=True)
    event_name = models.ForeignKey(MasterLookUp, on_delete=models.DO_NOTHING, related_name='event_name', null=True, blank=True)
    activity_name = models.ForeignKey(MasterLookUp, on_delete=models.DO_NOTHING, related_name='activity_name', null=True, blank=True)

    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    champions_15_19_year = models.IntegerField(null=True, blank=True)
    adult_male = models.IntegerField(null=True, blank=True)
    adult_female = models.IntegerField(null=True, blank=True)
    teachers = models.IntegerField(null=True, blank=True) 
    pri_members = models.IntegerField(null=True, blank=True)
    services_providers = models.IntegerField(null=True, blank=True)
    sms_members = models.IntegerField(null=True, blank=True)
    other = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)
    


    def __str__(self):
        return self.village_name.name
    

# Section 9: 
# Details of exposure visits of adolescent champions 

class Champions(BaseContent):
    VISITED_CHOICES = (
        (1, 'CHC'),
        (2, 'AFHC'),
        (3, 'HSC'),
        (4, 'HWC'),
        (5, 'Police Station'),
        (6, 'Post Office'),
        (7, 'Bank'),
        (8, 'Pragya Kendra'),
        (9, 'Panchayat Bhawan'),
        (10, 'Employment exchange'),
        (11, 'Zoo'),
        (12, 'Science Park'),
        (13, 'Others'),
    )

    awc_name = models.ForeignKey(
        AWC, on_delete=models.DO_NOTHING)
    date_of_visit = models.DateField(null=True, blank=True)
    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    first_inst_visited = models.PositiveIntegerField(choices=VISITED_CHOICES, null=True, blank=True)
    second_inst_visited = models.PositiveIntegerField(choices=VISITED_CHOICES, null=True, blank=True)
    third_inst_visited = models.PositiveIntegerField(choices=VISITED_CHOICES, null=True, blank=True)
    fourth_inst_visited = models.PositiveIntegerField(choices=VISITED_CHOICES, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.awc_name.name

# Section 10: 
# Details of adolescent re-enrolled in schools

class AdolescentRe_enrolled(BaseContent):
    GENDER_CHOICE = ((1, 'Male'), (2, 'Female'))
    CLASS_CHOICE = ((1, 'Class V'), (2, 'Class VI'), (3, 'Class VII'), (4, 'Class VIII'), (5, 'Class IX'), (6, 'Class X'),  (7, 'Class XI'), (8, 'Class XII'),)
    adolescent_name = models.ForeignKey(
        Adolescent, on_delete=models.DO_NOTHING)
    gender = models.IntegerField(choices=GENDER_CHOICE, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    parent_guardian_name = models.CharField(max_length=150)
    school_name = models.CharField(max_length=150, null=True, blank=True)
    which_class_enrolled = models.IntegerField(choices=CLASS_CHOICE, null=True, blank=True) 
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Adolescent Re_enrolled"

    def __str__(self):
        return self.adolescent_name.name

class VLCPCMetting(BaseContent):
    awc_name = models.ForeignKey(
        AWC, on_delete=models.DO_NOTHING)
    date_of_meeting = models.DateField()
    issues_discussed = models.CharField(max_length=150, blank=True, null=True)
    decision_taken = models.CharField(max_length=150, blank=True, null=True)
    no_of_participants_planned = models.IntegerField(null=True, blank=True)
    no_of_participants_attended = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "VLCPC metting"

    def __str__(self):
        return self.awc_name.name

class DCPU_BCPU(BaseContent):
    block_name = models.ForeignKey(
        Block, on_delete=models.DO_NOTHING, null=True, blank=True)
    name_of_institution = models.CharField(max_length=150)
    date_of_visit = models.DateField()
    name_of_lead = models.CharField(max_length=150)
    designation = models.CharField(max_length=150)
    issues_discussed = models.TextField(null=True, blank=True)
    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    champions_15_19_year = models.IntegerField(null=True, blank=True)
    adult_male = models.IntegerField(null=True, blank=True )
    adult_female = models.IntegerField(null=True, blank=True)
    teachers = models.IntegerField(null=True, blank=True) 
    pri_members = models.IntegerField(null=True, blank=True)
    services_providers = models.IntegerField(null=True, blank=True)
    sms_members = models.IntegerField(null=True, blank=True)
    other = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "DCPU/BCPU"

    def __str__(self):
        return self.block_name.name

class EducatinalEnrichmentSupportProvided(BaseContent):
    STANDARD_CHOICES = ((1, 'VIII'), (2, 'IX'), (3, 'X'))
    
    adolescent_name = models.ForeignKey(
        Adolescent, on_delete=models.DO_NOTHING, null=True, blank=True)
    parent_guardian_name = models.CharField(max_length=150)
    enrolment_date = models.DateField()
    standard = models.PositiveIntegerField('Class', choices=STANDARD_CHOICES)
    duration_of_coaching_support = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)


    def __str__(self):
        return self.adolescent_name.name


    


# Section 11: 
# Details of capacity building of different stakeholders

class Stakeholder(BaseContent):
    user_name = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, blank=True, null=True)
    # Education department 1 to 6
    master_trainers_male = models.IntegerField(null=True, blank=True)
    master_trainers_female = models.IntegerField(null=True, blank=True)
    master_trainers_total = models.IntegerField(null=True, blank=True)
    nodal_teachers_male = models.IntegerField(null=True, blank=True)
    nodal_teachers_female = models.IntegerField(null=True, blank=True)
    nodal_teachers_total = models.IntegerField(null=True, blank=True)
    principals_male = models.IntegerField(null=True, blank=True)
    principals_female = models.IntegerField(null=True, blank=True)
    principals_total = models.IntegerField(null=True, blank=True)
    district_level_officials_male = models.IntegerField(null=True, blank=True)
    district_level_officials_female = models.IntegerField(null=True, blank=True)
    district_level_officials_total = models.IntegerField(null=True, blank=True)
    peer_educator_male = models.IntegerField(null=True, blank=True)
    peer_educator_female = models.IntegerField(null=True, blank=True)
    peer_educator_total = models.IntegerField(null=True, blank=True)
    state_level_officials_male = models.IntegerField(null=True, blank=True)
    state_level_officials_female = models.IntegerField(null=True, blank=True)
    state_level_officials_total = models.IntegerField(null=True, blank=True)
    #  ICDS department 7 to 12
    icds_awws_male = models.IntegerField(null=True, blank=True)
    icds_awws_female = models.IntegerField(null=True, blank=True)
    icds_awws_total = models.IntegerField(null=True, blank=True)
    icds_supervisors_male = models.IntegerField(null=True, blank=True)
    icds_supervisors_female = models.IntegerField(null=True, blank=True)
    icds_supervisors_total = models.IntegerField(null=True, blank=True)
    icds_peer_educator_male = models.IntegerField(null=True, blank=True)
    icds_peer_educator_female = models.IntegerField(null=True, blank=True)
    icds_peer_educator_total = models.IntegerField(null=True, blank=True)
    icds_child_developement_project_officers_male = models.IntegerField(null=True, blank=True)
    icds_child_developement_project_officers_female = models.IntegerField(null=True, blank=True)
    icds_child_developement_project_officers_total = models.IntegerField(null=True, blank=True)
    icds_district_level_officials_male = models.IntegerField(null=True, blank=True)
    icds_district_level_officials_female = models.IntegerField(null=True, blank=True)
    icds_district_level_officials_total = models.IntegerField(null=True, blank=True)
    icds_state_level_officials_male = models.IntegerField(null=True, blank=True)
    icds_state_level_officials_female = models.IntegerField(null=True, blank=True)
    icds_state_level_officials_total = models.IntegerField(null=True, blank=True)
    # Health department 13 to 20
    health_ashas_male = models.IntegerField(null=True, blank=True)
    health_ashas_female = models.IntegerField(null=True, blank=True)
    health_ashas_total = models.IntegerField(null=True, blank=True)
    health_anms_male = models.IntegerField(null=True, blank=True)
    health_anms_female = models.IntegerField(null=True, blank=True)
    health_anms_total = models.IntegerField(null=True, blank=True)
    health_bpm_bhm_pheos_male = models.IntegerField(null=True, blank=True)
    health_bpm_bhm_pheos_female = models.IntegerField(null=True, blank=True)
    health_bpm_bhm_pheos_total = models.IntegerField(null=True, blank=True)
    health_medical_officers_male = models.IntegerField(null=True, blank=True)
    health_medical_officers_female = models.IntegerField(null=True, blank=True)
    health_medical_officers_total = models.IntegerField(null=True, blank=True)
    health_district_level_officials_male = models.IntegerField(null=True, blank=True)
    health_district_level_officials_female = models.IntegerField(null=True, blank=True)
    health_district_level_officials_total = models.IntegerField(null=True, blank=True)
    health_state_level_officials_male = models.IntegerField(null=True, blank=True)
    health_state_level_officials_female = models.IntegerField(null=True, blank=True)
    health_state_level_officials_total = models.IntegerField(null=True, blank=True)
    health_rsk_male = models.IntegerField(null=True, blank=True)
    health_rsk_female = models.IntegerField(null=True, blank=True)
    health_rsk_total = models.IntegerField(null=True, blank=True)
    health_peer_educator_male = models.IntegerField(null=True, blank=True)
    health_peer_educator_female = models.IntegerField(null=True, blank=True)
    health_peer_educator_total = models.IntegerField(null=True, blank=True)
    # Panchayat Raj Department 21 to 30
    panchayat_ward_members_male = models.IntegerField(null=True, blank=True)
    panchayat_ward_members_female = models.IntegerField(null=True, blank=True)
    panchayat_ward_members_total = models.IntegerField(null=True, blank=True)
    panchayat_up_mukhiya_up_Pramukh_male = models.IntegerField(null=True, blank=True)
    panchayat_up_mukhiya_up_Pramukh_female = models.IntegerField(null=True, blank=True)
    panchayat_up_mukhiya_up_Pramukh_total = models.IntegerField(null=True, blank=True)
    panchayat_mukhiya_Pramukh_male = models.IntegerField(null=True, blank=True)
    panchayat_mukhiya_Pramukh_female = models.IntegerField(null=True, blank=True)
    panchayat_mukhiya_Pramukh_total = models.IntegerField(null=True, blank=True)
    panchayat_samiti_member_male = models.IntegerField(null=True, blank=True)
    panchayat_samiti_member_female = models.IntegerField(null=True, blank=True)
    panchayat_samiti_member_total = models.IntegerField(null=True, blank=True)
    panchayat_zila_parishad_member_male = models.IntegerField(null=True, blank=True)
    panchayat_zila_parishad_member_female = models.IntegerField(null=True, blank=True)
    panchayat_zila_parishad_member_total = models.IntegerField(null=True, blank=True)
    panchayat_vc_zila_parishad_male = models.IntegerField(null=True, blank=True)
    panchayat_vc_zila_parishad_female = models.IntegerField(null=True, blank=True)
    panchayat_vc_zila_parishad_total = models.IntegerField(null=True, blank=True)
    panchayat_chairman_zila_parishad_male = models.IntegerField(null=True, blank=True)
    panchayat_chairman_zila_parishad_female = models.IntegerField(null=True, blank=True)
    panchayat_chairman_zila_parishad_total = models.IntegerField(null=True, blank=True)
    panchayat_block_level_officials_male = models.IntegerField(null=True, blank=True)
    panchayat_block_level_officials_female = models.IntegerField(null=True, blank=True)
    panchayat_block_level_officials_total = models.IntegerField(null=True, blank=True)
    panchayat_district_level_officials_male = models.IntegerField(null=True, blank=True)
    panchayat_district_level_officials_female = models.IntegerField(null=True, blank=True)
    panchayat_district_level_officials_total = models.IntegerField(null=True, blank=True)
    panchayat_state_level_officials_male = models.IntegerField(null=True, blank=True)
    panchayat_state_level_officials_female = models.IntegerField(null=True, blank=True)
    panchayat_state_level_officials_total = models.IntegerField(null=True, blank=True)
    # Media 31 to 33
    media_interns_male = models.IntegerField(null=True, blank=True)
    media_interns_female = models.IntegerField(null=True, blank=True)
    media_interns_total = models.IntegerField(null=True, blank=True)
    media_journalists_male = models.IntegerField(null=True, blank=True)
    media_journalists_female = models.IntegerField(null=True, blank=True)
    media_journalists_total = models.IntegerField(null=True, blank=True)
    media_editors_male = models.IntegerField(null=True, blank=True)
    media_editors_female = models.IntegerField(null=True, blank=True)
    media_editors_total = models.IntegerField(null=True, blank=True)
   
    # Others 34 to 36
    others_block_cluster_field_corrdinators_male = models.IntegerField(null=True, blank=True)
    others_block_cluster_field_corrdinators_female = models.IntegerField(null=True, blank=True)
    others_block_cluster_field_corrdinators_total = models.IntegerField(null=True, blank=True)
    others_ngo_staff_corrdinators_male = models.IntegerField(null=True, blank=True)
    others_ngo_staff_corrdinators_female = models.IntegerField(null=True, blank=True)
    others_ngo_staff_corrdinators_total = models.IntegerField(null=True, blank=True)
    others_male = models.IntegerField(null=True, blank=True)
    others_female = models.IntegerField(null=True, blank=True)
    others_total = models.IntegerField(null=True, blank=True)
    total_male = models.IntegerField(null=True, blank=True)
    total_female = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)


    



# Section 12: 
# Details of sessions monitoring and handholding support at block level
 
class SessionMonitoring(BaseContent):
    VISITED_CHOICE = ((1, 'Village'), (2, 'AWC'),  (3, 'School'),(4, 'Vocational Training Institute'),(5, 'Others'))

    name_of_visited = models.IntegerField(choices=VISITED_CHOICE, blank=True, null=True)
    name_of_place_visited = models.CharField(max_length=250, blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING,blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    # These is check box fields in html page, session_attended
    session_attended = models.CharField(max_length=150, blank=True, null=True)
    observation = models.TextField()
    recommendation = models.CharField(max_length=150)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)


    

# Section 13: Details of events & facility visits at block level 

class Events(BaseContent):
    VISITED_CHOICE = (
        (1, 'Village'), 
        (2, 'AWC'),  
        (3, 'School'),
        (4, 'HSC'),
        (5, 'HWC'),
        (6, 'AFHC'),
        (7, 'CHC'),
        (8, 'PHC'),
        (9, 'Vocational Training Institute'),
        (10, 'Other Public Service Institutions'),
        (11, 'Others')
    )

    name_of_visited = models.IntegerField(choices=VISITED_CHOICE, blank=True, null=True)
    name_of_place_visited = models.CharField(max_length=250, blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    purpose_visited = models.CharField(max_length=150)
    observation = models.TextField()
    recommendation = models.CharField(max_length=150)
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Events"    

    def __str__(self):
        return self.purpose_visited

# Section 14:
#  Details of participating in meetings at district and block level 

class ParticipatingMeeting(BaseContent):
    DISTRICT_BLOCK_CHOICE = ((1, 'District Level'), (2, 'Block Level'),)
    MEETING_CHOICE = (
        (1, 'Monthly Review meeting'),
        (2, 'Quarterly review meeting'),
        (3, 'Event planning meeting'),
        (4, 'Issue based meeting'),
        (5, 'SMC meeting'),
        (6, 'Convergence meeting'),
        (7, 'Others')
	)

    DEPARTMENT = (
        (1, 'Health'),
        (2, 'WCD'),
        (3, 'PRI'),
        (4, 'District administration'),
        (5, 'Block administration'),
        (6, 'Child protection'),
        (7, 'Education'),
        (8, "Partner organization’s meeting"),
        (9, 'Others')
    )
    date = models.DateField()
    user_name = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)
    district_block_level = models.IntegerField(choices=DISTRICT_BLOCK_CHOICE, blank=True, null=True)
    # type_of_meeting = models.CharField(max_length=150)
    type_of_meeting = models.IntegerField(choices = MEETING_CHOICE, blank=True, null=True)
    # department = models.CharField(max_length=150)
    department = models.IntegerField(choices = DEPARTMENT, blank=True, null=True)

    point_of_discussion = models.CharField(max_length=150)
    districit_level_officials = models.IntegerField(blank=True, null=True)
    block_level = models.IntegerField(blank=True, null=True)
    cluster_level = models.IntegerField(blank=True, null=True)
    no_of_pri = models.IntegerField(blank=True, null=True)
    no_of_others = models.IntegerField(blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.user_name.username

# Section 15: 
# Details of one to one (Follow up/ Liaison) meetings at district & Block Level

class FollowUP_LiaisionMeeting(BaseContent):
    DISTRICT_BLOCK_CHOICE = ((1, 'District Level'), (2, 'Block Level'),)

    DEPARTMENT = (
        (1, 'Health'),
        (2, 'WCD'),
        (3, 'PRI'),
        (4, 'District administration'),
        (5, 'Block administration'),
        (6, 'Child protection'),
        (7, 'Education'),
        (8, "Partner organization’s meeting"),
        (9, 'Others')
    )

    user_name = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    district_block_level = models.IntegerField(choices=DISTRICT_BLOCK_CHOICE, blank=True, null=True)
    meeting = models.CharField(max_length=150)
    meeting_name = models.ForeignKey(MasterLookUp, on_delete=models.DO_NOTHING, related_name='meeting_name', null=True, blank=True)
    # department = models.CharField(max_length=150, blank=True, null=True)
    departments = models.IntegerField(choices=DEPARTMENT, blank=True, null=True)
    point_of_discussion = models.CharField(max_length=150)
    outcome = models.CharField(max_length=150)
    decision_taken = models.CharField(max_length=150)
    remarks = models.CharField(max_length=150)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Follow up/Liaision meeting"


    def __str__(self):
        return self.user_name.username

# Section 16: 
# If any challenge faced related to the operation of the program, then mention it and mention the proposed solution 


class FacedRelatedOperation(BaseContent):
    user_name = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, blank=True, null=True)
    challenges = models.TextField(blank=True, null=True)
    proposed_solution = models.TextField(blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)


    def __str__(self):
        return self.user_name.username



class CCReportNotes(BaseContent):
    successes = models.TextField(blank=True, null=True)
    challenges_faced = models.TextField(blank=True, null=True)
    feasible_solution_to_scale_up = models.TextField(blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)


    class Meta:
        verbose_name_plural = "CC Report Notes"

    def __str__(self):
        return self.successes

class POReportSection17(BaseContent):
    suggestions = models.TextField(blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "PO Report Section 17"

    def __str__(self):
        return self.suggestions
    
class DataEntryRemark(BaseContent):
    task = models.ForeignKey(Task, on_delete = models.DO_NOTHING, blank=True, null=True)
    user_name = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Data Entry Remark"

    def __str__(self):
        return str(self.task)

class ReportSection1(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_cc = models.CharField(max_length=250,blank=True, null=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    session_name = models.CharField(max_length=250,blank=True, null=True)
    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section1"

    def __str__(self):
        return str(self.task)

class ReportSection2(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_cc = models.CharField(max_length=250,blank=True, null=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    session_name = models.CharField(max_length=250,blank=True, null=True)
    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section2"

    def __str__(self):
        return str(self.task)

class ReportSection3(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    number_adolescent_girls_linked = models.CharField(max_length=250,blank=True, null=True)
    number_girls_completed_training = models.CharField(max_length=250,blank=True, null=True)
    number_girls_accepted_placement = models.CharField(max_length=250,blank=True, null=True)
    number_of_girls_offered_placement = models.CharField(max_length=250,blank=True, null=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section3"

    def __str__(self):
        return str(self.task)

class ReportSection4a(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    
    participated_10_14_years = models.IntegerField(null=True, blank=True)
    participated_15_19_years = models.IntegerField(null=True, blank=True)

    bmi_10_14_year = models.IntegerField(null=True, blank=True)
    bmi_15_19_year = models.IntegerField(null=True, blank=True)

    hb_test_10_14_year = models.IntegerField(null=True, blank=True)
    hb_test_15_19_year = models.IntegerField(null=True, blank=True)

    tt_shot_10_14_year = models.IntegerField(null=True, blank=True)
    tt_shot_15_19_year = models.IntegerField(null=True, blank=True)

    counselling_10_14_year = models.IntegerField(null=True, blank=True)
    counselling_15_19_year = models.IntegerField(null=True, blank=True)

    referral_10_14_year = models.IntegerField(null=True, blank=True)
    referral_15_19_year = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section4a"

    def __str__(self):
        return str(self.task)

class ReportSection4b(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    
    participated_10_14_years = models.IntegerField(null=True, blank=True)
    participated_15_19_years = models.IntegerField(null=True, blank=True)

    bmi_10_14_year = models.IntegerField(null=True, blank=True)
    bmi_15_19_year = models.IntegerField(null=True, blank=True)

    hb_test_10_14_year = models.IntegerField(null=True, blank=True)
    hb_test_15_19_year = models.IntegerField(null=True, blank=True)

    counselling_10_14_year = models.IntegerField(null=True, blank=True)
    counselling_15_19_year = models.IntegerField(null=True, blank=True)

    referral_10_14_year = models.IntegerField(null=True, blank=True)
    referral_15_19_year = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section4b"

    def __str__(self):
        return str(self.task)

class ReportSection5(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)

    girls_referred_10_14_year = models.IntegerField(null=True, blank=True)
    girls_referred_15_19_year = models.IntegerField(null=True, blank=True)

    boys_referred_10_14_year = models.IntegerField(null=True, blank=True)
    boys_referred_15_19_year = models.IntegerField(null=True, blank=True)

    girls_hwc_referred = models.IntegerField(null=True, blank=True)
    girls_hwc_visited = models.IntegerField(null=True, blank=True)

    girls_afhc_referred = models.IntegerField(null=True, blank=True)
    girls_afhc_visited = models.IntegerField(null=True, blank=True)

    girls_dh_referred = models.IntegerField(null=True, blank=True)
    girls_dh_visited = models.IntegerField(null=True, blank=True)

    boys_hwc_referred = models.IntegerField(null=True, blank=True)
    boys_hwc_visited = models.IntegerField(null=True, blank=True)

    boys_afhc_referred = models.IntegerField(null=True, blank=True)
    boys_afhc_visited = models.IntegerField(null=True, blank=True)

    boys_dh_referred = models.IntegerField(null=True, blank=True)
    boys_dh_visited = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section5"

    def __str__(self):
        return str(self.task)

class ReportSection6(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_hsc = models.CharField(max_length=250,blank=True, null=True)
    name_of_sahiya_participated = models.CharField(max_length=250,blank=True, null=True)
    no_of_aww = models.CharField(max_length=250,blank=True, null=True)
    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section6"

    def __str__(self):
        return str(self.task)

class ReportSection7(BaseContent):
    school_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    school_name = models.CharField(max_length=250,blank=True, null=True)
    no_of_participants = models.CharField(max_length=250,blank=True, null=True)
    number_issues_discussed = models.CharField(max_length=250,blank=True, null=True)
    number_decision_taken = models.CharField(max_length=250,blank=True, null=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section7"
    
    def __str__(self):
        return str(self.task)


class ReportSection8(BaseContent):
    village_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    event_name = models.CharField(max_length=250,blank=True, null=True)
    activity_name = models.CharField(max_length=250,blank=True, null=True)
    organized_by = models.CharField(max_length=250,blank=True, null=True)

    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    champions_15_19_year = models.IntegerField(null=True, blank=True)
    adult_male = models.IntegerField(null=True, blank=True)
    adult_female = models.IntegerField(null=True, blank=True)
    teachers = models.IntegerField(null=True, blank=True) 
    pri_members = models.IntegerField(null=True, blank=True)
    services_providers = models.IntegerField(null=True, blank=True)
    sms_members = models.IntegerField(null=True, blank=True)
    other = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section8"

    def __str__(self):
        return str(self.task)

class ReportSection9(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    first_inst_visited = models.CharField(max_length=250, blank=True, null=True)
    second_inst_visited = models.CharField(max_length=250, blank=True, null=True)
    third_inst_visited = models.CharField(max_length=250, blank=True, null=True)
    fourth_inst_visited = models.CharField(max_length=250, blank=True, null=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section9"

    def __str__(self):
        return str(self.task)
    
class ReportSection10(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    name_of_adolescent = models.CharField(max_length=250,blank=True, null=True)
    gender = models.CharField(max_length=250,blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    parent_guardian_name = models.CharField(max_length=250,blank=True, null=True)
    name_of_school  = models.CharField(max_length=250,blank=True, null=True)
    class_enrolled = models.CharField(max_length=250,blank=True, null=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Report Section10"

    def __str__(self):
        return str(self.task)

class UntrustParentVocationalTraining(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    parent_name = models.CharField(max_length=250,blank=True, null=True)
    training_complated = models.CharField(max_length=250,blank=True, null=True)
    placement_accepted = models.CharField(max_length=250,blank=True, null=True)
    placement_offered = models.CharField(max_length=250,blank=True, null=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Untrust Parent Vocational Training"

    def __str__(self):
        return str(self.task)

class UntrustVLCPCMetting(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    date_of_meeting = models.CharField(max_length=250,blank=True, null=True)
    no_of_participants_planned = models.IntegerField(null=True, blank=True)
    no_of_participants_attended = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Untrust VLCPC Meeting"

    def __str__(self):
        return str(self.task)

class UntrustDCPU_BCPU(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_institution = models.CharField(max_length=150)
    date_of_visit = models.CharField(max_length=150)
    date_of_visit1 = models.DateField(null=True, blank=True)
    name_of_lead = models.CharField(max_length=150)
    designation = models.CharField(max_length=150)
    issues_discussed = models.TextField(null=True, blank=True)
    girls_10_14_year = models.IntegerField(null=True, blank=True)
    girls_15_19_year = models.IntegerField(null=True, blank=True)
    boys_10_14_year = models.IntegerField(null=True, blank=True)
    boys_15_19_year = models.IntegerField(null=True, blank=True)
    champions_15_19_year = models.IntegerField(null=True, blank=True)
    adult_male = models.IntegerField(null=True, blank=True )
    adult_female = models.IntegerField(null=True, blank=True)
    teachers = models.IntegerField(null=True, blank=True) 
    pri_members = models.IntegerField(null=True, blank=True)
    services_providers = models.IntegerField(null=True, blank=True)
    sms_members = models.IntegerField(null=True, blank=True)
    other = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Untrust DCPU_BCPU"

    def __str__(self):
        return str(self.task)

class UntrustEducatinalEnrichmentSupportProvided(BaseContent):
    unique_id = models.IntegerField(null=True, blank=True)
    name_of_block = models.CharField(max_length=250,blank=True, null=True)
    name_of_panchayat = models.CharField(max_length=250,blank=True, null=True)
    name_of_village = models.CharField(max_length=250,blank=True, null=True)
    name_of_awc_code = models.CharField(max_length=250,blank=True, null=True)
    name_of_adolescent = models.CharField(max_length=250,blank=True, null=True)
    parent_guardian_name = models.CharField(max_length=250,blank=True, null=True)
    enrolment_date = models.CharField(max_length=250,blank=True, null=True)
    standard = models.CharField(max_length=250,blank=True, null=True)
    duration_of_coaching_support = models.IntegerField(null=True, blank=True)

    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Untrust Educatinal Enrichment SupportProvided"

    def __str__(self):
        return str(self.task)

class HistoryRecord(BaseContent):
    start_date_time = models.DateTimeField(blank=True, null=True)
    end_date_time = models.DateTimeField(blank=True, null=True)
    execution_time = models.CharField(max_length=250,blank=True, null=True)


class Logged(BaseContent):
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING)
    month = models.CharField(max_length=255)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Logged User"