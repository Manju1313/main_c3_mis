from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class BaseContent(models.Model):
    STATUS_CHOICES = ((1, 'Active'), (2, 'Inactive'),)
    
    status = models.PositiveIntegerField(
        choices=STATUS_CHOICES, default=1, db_index=True)
    server_created_on = models.DateTimeField(auto_now_add=True)
    server_modified_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name='created%(app_label)s_%(class)s_related', null=True, blank=True,)
    modified_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name='modified%(app_label)s_%(class)s_related', null=True, blank=True,)

    class Meta:
        abstract = True


class TrainingSubject(BaseContent):
    training_subject = models.CharField(max_length=350, null=True, blank=True)

    def __str__(self):
        return self.training_subject

class MasterLookUp(BaseContent):
    name = models.CharField(max_length=400)
    parent = models.ForeignKey('self',on_delete=models.DO_NOTHING, null=True, blank=True)
    slug = models.SlugField(_("Slug"), blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return str(self.name)


# class CommunityEngagement(BaseContent):
#     EVENT_ACTIVITY_CHOICES = ((1, 'Event'), (2, 'Activity'),)
#     event_theme_name = models.CharField(max_length=350, null=True, blank=True)
#     name_of_event_activity = models.IntegerField(choices=EVENT_ACTIVITY_CHOICES, null=True, blank=True)

#     def __str__(self):
#         return self.event_theme_name


class State(BaseContent):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name

class District(BaseContent):
    name = models.CharField(max_length=150)
    state = models.ForeignKey(
        State, on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.name

class Block(BaseContent):
    name = models.CharField(max_length=150)
    district = models.ForeignKey(
        District, on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.name

class GramaPanchayat(BaseContent):
    name = models.CharField(max_length=150)
    block = models.ForeignKey(
        Block, on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.name

class Village(BaseContent):
    name = models.CharField(max_length=150)
    grama_panchayat = models.ForeignKey(
        GramaPanchayat, on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ["grama_panchayat"]

class School(BaseContent):
    name = models.CharField(max_length=150)
    village = models.ForeignKey(
        Village, on_delete=models.DO_NOTHING)
    code = models.PositiveBigIntegerField(unique=True)

    def __str__(self):
        return self.name
    class Meta:
        ordering = ["village"]


class AWC(BaseContent):
    name = models.CharField(max_length=150)
    village = models.ForeignKey(
        Village, on_delete=models.DO_NOTHING)
    code = models.PositiveBigIntegerField(unique=True)

    class Meta:
        verbose_name_plural = "AWC"
        ordering = ["village"]

    def __str__(self):
        return self.name

class Group(BaseContent):
    name = models.CharField(max_length=150)
    awc = models.ForeignKey(
        AWC, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["awc"]

class Adolescent(BaseContent):
    GENDER_CHOICE = ((1, 'Male'), (2, 'Female'))
    name = models.CharField(max_length=150)
    awc = models.ForeignKey(
        AWC, on_delete=models.DO_NOTHING)
    group = models.ForeignKey(
        Group, on_delete=models.DO_NOTHING, blank=True, null=True)
    gender = models.IntegerField(choices=GENDER_CHOICE,)
    code = models.CharField(max_length=150, blank=True, null=True)
    age_in_completed_years = models.IntegerField()
    site = models.IntegerField(default=0, blank=True, null=True)


    def __str__(self):
        return self.name 

class FossilDLSessionCategory(BaseContent):
    session_category = models.CharField(max_length=150)

    class Meta:
        verbose_name_plural = "Fossil DL session category"

    def __str__(self):
        return self.session_category

class FossilDLSessionConfig(BaseContent):
    SESSION_CHOICES = ((1, 'Theroy'), (2, 'Practical'),)

    session_category = models.ForeignKey(FossilDLSessionCategory, on_delete=models.DO_NOTHING)
    session_type = models.IntegerField(choices=SESSION_CHOICES)
    scheduled_days = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "Fossil DL config"

    def __str__(self):
        return self.session_category.session_category

class FossilAHSessionCategory(BaseContent):
    session_category = models.CharField(max_length=150)

    class Meta:
        verbose_name_plural = "Fossil AH session category"

    def __str__(self):
        return self.session_category

class FossilAHSession(BaseContent):
    session_name = models.CharField(max_length=150)
    fossil_ah_session_category = models.ForeignKey(
        FossilAHSessionCategory, on_delete=models.DO_NOTHING)
    no_of_days = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "Fossil AH session"

    def __str__(self):
        return self.session_name 

class CC_AWC_AH(BaseContent):
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING)
    awc = models.ForeignKey(
        AWC, on_delete=models.DO_NOTHING)
    deactivated_date = models.DateField()

    class Meta:
        verbose_name_plural = "CC AWC AH"

    def __str__(self):
        return self.user.username



class CC_AWC_DL(BaseContent):
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING)
    awc = models.ForeignKey(
        AWC, on_delete=models.DO_NOTHING)
    deactivated_date = models.DateField()

    class Meta:
        verbose_name_plural = "CC AWC DL"

    def __str__(self):
        return self.user.username

class CC_School(BaseContent):
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING)
    school = models.ForeignKey(
        School, on_delete=models.DO_NOTHING)
    deactivated_date = models.DateField()

    class Meta:
        verbose_name_plural = "CC School"

    def __str__(self):
        return self.user.username


class MisReport(BaseContent):
    report_person = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='report_person')
    report_to = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='report_to')
    
    def __str__(self):
        return self.report_person.username




    






    

