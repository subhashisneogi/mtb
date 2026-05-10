
class FarmersAggreementForms(BaseAbstractStructure): 
    blf= models.ForeignKey(BlfProfile, related_name='blf_farmer_aggreements', on_delete=models.DO_NOTHING, blank=True, null=True)
    grower= models.ForeignKey(GrowerProfile, related_name='grower_aggreements', on_delete=models.DO_NOTHING, blank=True, null=True)
    aggreement_form_title = models.ForeignKey(FarmersAggreementMaster, related_name="farmers_aggreement_title", on_delete=models.CASCADE,  blank=True,null=True)
    farmer_signature_file = models.FileField(
        upload_to='BLF/Farmers/Aggreement',null=True,blank=True, help_text='file')
    def __str__(self):
        return str(self.aggreement_form_title)

<form method="POST" action="{% url 'chemical_data:uplaod_farmers_signature' %}" enctype="multipart/form-data">
    {% csrf_token %}
    <input type="" name="grower_pk" value="{{ grower_pk }}">
    <input type="" name="form_master_pk" value="{{ item.pk }}">

    <div class="form-group">
        <label for="signature_file">Signature File</label>
        <input type="file" name="farmer_signature_file" class="form-control-file" id="farmer_signature_file">
    </div>
    <button type="submit" class="btn btn-primary">Upload</button>
</form>

@login_required
def edit_farmers_signature(request):
    if request.method == 'POST':
        grower_pk = request.POST.get('grower_pk')
        signature_file = request.FILES.get('farmer_signature_file')
        form_master_pk = request.POST.get('form_master_pk')
        blf_details = BlfProfile.objects.filter(user=request.user).first()
        grower_details = GrowerProfile.objects.filter(user=grower_pk).first()
        form_master_details = FarmersAggreementMaster.objects.filter(pk=form_master_pk).first()

        messages.success(request, 'Signature Updated successfully.')
        return redirect(reverse('chemical_data:farmers_aggreements_forms_list', kwargs={"grower_pk": grower_pk }))


please write the proper complete  code here to update file into FarmersAggreementForms model