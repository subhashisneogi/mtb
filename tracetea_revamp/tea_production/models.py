from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()



# Create your models here.
class CustomManager(models.Manager):
    def get_queryset(self):
        return super(__class__, self).get_queryset().filter(is_deleted=False)
    

class BaseAbstractStructure(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    cmobjects = CustomManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super(__class__, self).save(*args, **kwargs)


class TeaType(models.Model):
    """ Tea Type Model Trace Tea @vivek"""   
    name=models.CharField(max_length=200,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
    
    
class TeaGradeDetails(models.Model) :
    """ Tea Grade Details Model Trace Tea @vivek"""

    tea_type=models.ForeignKey(TeaType, related_name='tea_grade',on_delete=models.CASCADE, blank=True, null=True)
    grade= models.CharField(max_length=200,blank=True,null=True)  
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.grade)  


class Marks(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return str(self.name)
