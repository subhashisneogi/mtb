from django.db import models
from time import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()
from master.models import *
from user_profile.models import *
from user_profile.aggregator_api_models import *
from django.utils.text import slugify
from user_profile.validators import *
from django.core.validators import MaxValueValidator, MinValueValidator

class ChemicalType(BaseAbstractStructure):
    """ Chemical Type Model Trace Tea @vivek"""   
    name=models.CharField(max_length=200,blank=True,null=True)
    def __str__(self):
        return self.name 
        
class ChemicalData(models.Model):
    """ Chemical Type Model Trace Tea @vivek"""   
    chemical_type= models.ForeignKey(ChemicalType, related_name='chemical_type_trusttea',on_delete=models.CASCADE, blank=True, null=True)
    chemical_name = models.CharField(max_length=200, blank=True,null=True)
    manufacturer=models.CharField(max_length=200,blank=True,null=True)
    brand_local_name=models.CharField(max_length=200,blank=True,null=True)
    composition=models.CharField(max_length=200,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='created_by_user_chemical', on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return self.chemical_name     
    
class UseOfChemical(BaseAbstractStructure):
    """ User of chemical i.e fertilizer, herbicides, acarcides and insecticides Model and use for FIARM DIARY  """
    grower= models.ForeignKey(GrowerProfile, related_name='user_of_chemical_aggregator', on_delete=models.CASCADE, blank=True, null=True)
    aggregator= models.ForeignKey(GrowerProfile, related_name='user_of_chemical_blf', on_delete=models.CASCADE, blank=True, null=True)
    blf= models.ForeignKey(GrowerProfile, related_name='user_of_chemical_grower', on_delete=models.CASCADE, blank=True, null=True)
    date=models.DateField(auto_now_add= False, blank=True,null=True)
    chemical= models.ForeignKey(ChemicalData, related_name='chemical_data_id', on_delete=models.CASCADE, blank=True, null=True)
    labour= models.ForeignKey(Labour, related_name='labour_id_chemical',on_delete=models.CASCADE, blank=True, null=True)
    quantity=models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])
    unit=models.CharField(max_length=50,blank=True,null=True)
    plot= models.ForeignKey(Plot, related_name='plot_id_chemical', on_delete=models.CASCADE, blank=True, null=True)
    division = models.ForeignKey(Division, related_name="division_use_of_chemical", on_delete=models.CASCADE, blank=True, null=True)
    dose = models.CharField(max_length=250,blank=True, null=True)
    def __str__(self):
        return str(self.grower)

# MAP AREA MODELS
class MapAreaNameMaster(BaseAbstractStructure):
    name = models.CharField(max_length=200, blank=True,null=True)
    slug = models.SlugField(max_length=200, null=True, blank=True)
    def __str__(self):
        return str(self.name)
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(MapAreaNameMaster, self).save(*args, **kwargs)	

class MapAreaMaster(BaseAbstractStructure):
    blf= models.ForeignKey(BlfProfile, related_name='blf_map_area_master', on_delete=models.DO_NOTHING, blank=True, null=True)
    grower= models.OneToOneField(GrowerProfile, related_name='grower_map_area_master', on_delete=models.DO_NOTHING, blank=True, null=True)
    aggregator= models.ForeignKey(AggregatorProfile, related_name='aggregator_map_area_master', on_delete=models.DO_NOTHING, blank=True, null=True)
    map_image=models.FileField(
        upload_to='map_details/file',null=True,blank=True, help_text='file', validators=[validate_image_file_extension])
    pdf_map_image=models.FileField(
        upload_to='map_details/file',null=True,blank=True, help_text='file', validators=[validate_image_file_extension])
    digital_map_image=models.FileField(
        upload_to='map_details/file/digital-map', null=True,blank=True, help_text='file', validators=[validate_image_file_extension])
    water_source = models.TextField(blank=True, null=True)
    land_near_by = models.TextField(blank=True, null=True)
    is_image_upload = models.BooleanField(default=False, blank=True, null=True)
    is_digital_upload = models.BooleanField(default=False, blank=True, null=True)
    def __str__(self):
        return str(self.grower)
    def save(self, *args, **kwargs):
        """ image file resize @Subhashis"""
        # if self.map_image:
        #     temp_image = Image.open(self.map_image).convert('RGB')
        #     output_io_stream = BytesIO()
        #     temp_resized_image = temp_image.resize((1720, 500))
        #     temp_resized_image.save(
        #         output_io_stream, format='JPEG', quality=90)
        #     output_io_stream.seek(0)
        #     self.map_image = InMemoryUploadedFile(output_io_stream,
        #                                           'ImageField', "%s.jpg" % self.map_image.name.split('.')[0], 'image/jpeg', sys.getsizeof(output_io_stream), None)
        #     # Update pdf_map_image whenever map_image is updated
        #     temp_pdf_output_io_stream = BytesIO()
        #     temp_pdf_resized_image = temp_image.resize((800, 400))
        #     temp_pdf_resized_image.save(
        #         temp_pdf_output_io_stream, format='JPEG', quality=90)
        #     temp_pdf_output_io_stream.seek(0)
        #     self.pdf_map_image = InMemoryUploadedFile(temp_pdf_output_io_stream,
        #                                               'ImageField', "%s.jpg" % self.map_image.name.split('.')[0], 'image/jpeg', sys.getsizeof(temp_pdf_output_io_stream), None)
        super(MapAreaMaster, self).save(*args, **kwargs)

class MapAreaLandDetails(BaseAbstractStructure):
    grower = models.ForeignKey(GrowerProfile, related_name='grower_map_area_land_details', on_delete=models.DO_NOTHING, blank=True, null=True)
    map_area_master = models.ForeignKey(MapAreaMaster, related_name='map_area_land_details', on_delete=models.CASCADE, blank=True, null=True)
    map_area_name = models.ForeignKey(MapAreaNameMaster, related_name="map_area_name_land_details", on_delete=models.CASCADE, blank=True, null=True)
    total_areas = models.FloatField(blank=True, null=True, default=0, validators=[MinValueValidator(0.1)])
    coordinate = models.JSONField(blank=True, null=True)
    def __str__(self):
        return str(self.map_area_name)
    
###########
class MapAreaDetails(BaseAbstractStructure):
    blf= models.ForeignKey(BlfProfile, related_name='blf_map_area_details', on_delete=models.DO_NOTHING, blank=True, null=True)
    grower= models.ForeignKey(GrowerProfile, related_name='grower_map_area_details', on_delete=models.DO_NOTHING, blank=True, null=True)
    aggregator= models.ForeignKey(AggregatorProfile, related_name='aggregator_map_area_details', on_delete=models.DO_NOTHING, blank=True, null=True)
    map_area_name = models.ForeignKey(MapAreaNameMaster, related_name="map_area_name", on_delete=models.CASCADE,  blank=True,null=True)
    total_areas = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0.1)]) 
    map_image=models.FileField(
        upload_to='map_details/file',null=True,blank=True,)
    coordinate = models.JSONField(blank=True, null=True)
    water_source = models.TextField(blank=True, null=True)
    land_near_by = models.TextField(blank=True, null=True)
    is_image_upload = models.BooleanField(default=False, blank=True, null=True)
    is_digital_upload = models.BooleanField(default=False, blank=True, null=True)
    mime_type = models.CharField(max_length=200, null=True, blank=True)
    file_data = models.TextField(null=True, blank=True)


class FarmersAggreementMaster(BaseAbstractStructure):
    name = models.CharField(max_length=200, blank=True,null=True)
    slug = models.SlugField(max_length=200, null=True, blank=True)
    def __str__(self):
        return str(self.name)
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(FarmersAggreementMaster, self).save(*args, **kwargs)	
        
class FarmersAggreementForms(BaseAbstractStructure): 
    blf= models.ForeignKey(BlfProfile, related_name='blf_farmer_aggreements', on_delete=models.DO_NOTHING, blank=True, null=True)
    grower= models.ForeignKey(GrowerProfile, related_name='grower_aggreements', on_delete=models.DO_NOTHING, blank=True, null=True)
    aggregator= models.ForeignKey(AggregatorProfile, related_name='aggregator_aggreements', on_delete=models.DO_NOTHING, blank=True, null=True)
    aggreement_form_title = models.ForeignKey(FarmersAggreementMaster, related_name="farmers_aggreement_title", on_delete=models.CASCADE,  blank=True,null=True)
    farmer_signature_file = models.FileField(
        upload_to='BLF/Farmers/Aggreement',
        null=True,
        blank=True,
        help_text='file',
        validators=[validate_signature_file_extension]
    )
    blf_grade_official_signature_file = models.FileField(
        upload_to='BLF/Farmers/Aggreement',null=True,blank=True,help_text='file',
        validators=[validate_signature_file_extension]
    )
    date = models.DateField(auto_now=False, null=True, blank=True)
    place = models.CharField(max_length=150, null=True, blank=True)
    mime_type = models.CharField(max_length=200, null=True, blank=True)
    file_data = models.TextField(null=True, blank=True)
    def __str__(self):
        return str(self.grower)


