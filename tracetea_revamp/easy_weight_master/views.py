import collections
# import dateutil
import datetime
from datetime import datetime, date
import csv
from datetime import date, timedelta
from rest_framework.response import Response

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from django.db.models import Sum, Value, Count, Avg, Case, When, F
from django.db.models.functions import Coalesce

from master.common import CommonMixin


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from rest_framework.decorators  import api_view, permission_classes, authentication_classes
from .models import *
from .utils import *
import pandas as pd
from django.db import transaction
import numpy as np
from easy_weight_master.forms import *
import decimal
import datetime

from master.decorators import *

# Create your views here.
def ExportEasyWeightTemplate(request):
    """Export or download template for bulk upload @vivek"""
    
    if request.method == 'GET':
        # Get selected option from form
        # row=EasyWeightMaster.objects.get(id=1)
        # print(row)
        # combined_resource = CombinedResource()
        # # user_resource=user_resource.UserDetails()
        # dataset = combined_resource.export()

        # response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
        # response['Content-Disposition'] = 'attachment; filename="easy_weight.xls"'
        # return response   
           
        data_table1=EasyWeightMaster.objects.all().values('tracetea_id','member_no',\
                                                          'member_name','mobile_number','month_year',\
                                                            'total_weight','rate_gl','total_value',\
                                                                'rate_tf','tft','ss','rate_fa',\
                                                                    'fa','manure','kadhi','gl_adv',\
                                                                        'hort','mbf','misc1','misc2','misc3',\
                                                                        'roud_off_net','total_ded','net_payable',\
                                                                        'cb','ob','payment_rcpt_no','payment_date',
                                                                        )
        data_table2=EasyWeightWt.objects.all().values('wt')
        data_table3=EasyWeightAdv.objects.all().values('adv')
        data_table4=EasyWeightGwt.objects.all().values('gwt')
        df_table1=pd.DataFrame.from_records(data_table1)
        df_table2=pd.DataFrame.from_records(data_table2)
        df_table3=pd.DataFrame.from_records(data_table3)
        df_table4=pd.DataFrame.from_records(data_table4)
        # df_table1['created_at'] =  pd.to_datetime(df_table1.created_at, format='%Y-%m-%d %H:%M:%S')
        # df_table2['created_at'] =  pd.to_datetime(df_table2.created_at, format='%Y-%m-%d %H:%M:%S')
        # df_table1['updated_at'] =  pd.to_datetime(df_table1.updated_at, format='%Y-%m-%d %H:%M:%S')
        # df_table2['updated_at'] =  pd.to_datetime(df_table2.updated_at, format='%Y-%m-%d %H:%M:%S')
        # df_table1['payment_date'] =  pd.to_datetime(df_table1.payment_date, format='%Y-%m-%d %H:%M:%S')
        output_file='media/easy_weight/easy_weight.xlsx'
        writer=pd.ExcelWriter(output_file,engine='xlsxwriter')
        df_table1.to_excel(writer,sheet_name='Sheet1',index=False)
        df_table2.to_excel(writer,sheet_name='Sheet1',startcol=len(df_table1) ,index=False)
        df_table3.to_excel(writer,sheet_name='Sheet1',startcol=len(df_table1) + len(df_table1),index=False)
        df_table4.to_excel(writer,sheet_name='Sheet1',startcol=len(df_table1) + len(df_table1) + len(df_table1) ,index=False)
       
        
        writer.close()
        # iden= request.GET["id"]
        # output = BytesIO()
        # queryset = EasyWeightWt.objects.all().values()
        # df = pd.DataFrame(queryset)
        # writer = pd.ExcelWriter(output,engine='xlsxwriter')
        # df.to_excel(writer,sheet_name='Sheet1')
        # writer.save()
        # output_name = 'example'
        # output.seek(0)
        # response = HttpResponse(output_file,content_type='application/vnd.ms-excel')
        # response['Content-Disposition'] = 'attachment;filename="easy.xlsx"'
        # response = HttpResponse(content_type='application/vnd.ms-excel')
        # # tell the browser what the file is named
        # response['Content-Disposition'] = 'attachment;filename="file_name.xlsx"' 
        # return response

def DownloadEasyWeightTemplate(request):
    """ download template for bulk upload @vivek"""
    file_path='easy_weight.xlsx'
    file_name=os.path.basename(file_path)
    if request.method == 'GET':
       with open(file_path,'rb') as file:
           response =HttpResponse(file.read(),content_type='application/vnd.ms-excel')
           response['Content-Disposition'] = f'attachment;filename="{file_name}"'
           return response





# @permission_required_admin
@login_required
def BulkImportEasyWeight(request):
    "Bulk import easy weight"
    if request.method == 'POST':
        form = EasyWeightForm(request.POST)
        if form.is_valid():
            collection_center = form.cleaned_data.get('collection_center')
            month_year = form.cleaned_data.get('month_year')
            file=request.FILES['file']
            path = 'media/excel/' + file.name
            if not os.path.exists('media/excel'):
                os.makedirs('media/excel')
            with open(path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            df = pd.read_excel(path)
            df=df.replace({np.nan: None})
            print("check",df)
            if df.empty == True:
                messages.error(request,'Empty excel file') 
            successful_upload=0
            successful_update=0
            try:
                for index, row in df.iterrows(): 
                    # print("month year",type(row['Month_Year'] ) ,row['Month_Year'])
                    # print(collection_center.id)
                    # print("row and index",row,index)
                    with transaction.atomic(): 
                        # try:                   
                            if row['tracetea ID'] is None:
                                messages.error(request,'Tracetea ID is not be blank ,Please enter Tracetea ID in excel')


                            # elif EasyWeightMaster.objects.filter(tracetea_id__username=row['tracetea ID'],) .exists():
                            #     messages.error( request, 'TraceTea ID'+ " : " + str(row['tracetea ID']) + ' already exists in Easy Weight List',\
                            #                      )
                            elif row['Member_No'] is None:
                                 messages.error(request,'Member is not be blank,Please enter no. of member  in excel')

                            elif row['Member_Name'] is None:
                                messages.error(request,'Please Enter Member Name in  excel')   
                            elif row['Phone No'] is None:
                                messages.error(request,'Please enter phone number in excel')
                            elif row['Month_Year'] is None:
                                messages.error(request,'Please Enter Month and Year in excel')  
                            elif row['Total_Weight'] is None:
                                messages.error(request,'Please Enter Total Weight in excel')  
                            # elif row['RateGL'] is None:
                            #     messages.error(request,'Please enter Rate GL in excel')   
                            # elif row['Total_Value'] is None:
                            #     messages.error(request,'Please enter Total_Value in excel')      
                            # elif row['RateTF'] is None :
                            #      messages.error(request,"Please enter Rate TF in excel")
                            # elif row['Tft'] is None :
                            #      messages.error(request,"Please enter Tft in excel")
                            # elif row['SS'] is None :
                            #      messages.error(request,"Please enter SS in excel")
                            # elif row['RateFA'] is None :
                            #      messages.error(request,"Please Rate FA in excel")
                            # elif row['FA'] is None :
                            #      messages.error(request,"Please enter FA in excel")
                            # elif row['Manure'] is None :
                            #      messages.error(request,"Please enter Manure in excel")
                            # elif row['Kadhi'] is None :
                            #      messages.error(request,"Please enter Kadhi in excel")
                            # elif row['GL_Adv'] is None :
                            #      messages.error(request,"Please enter GL_Adv in excel")
                            # elif row['Hort'] is None :
                            #      messages.error(request,"Please enter Hort in excel")                                                     
                            # elif row['MBF'] is None :
                            #      messages.error(request,"Please enter MBF in excel")
                            # elif row['RoudOff_net']  is None:  
                            #     messages.error(request,"Please enter Roud Off net in Excel")
                            # elif row['Total_Ded']  is None:  
                            #     messages.error(request,"Please enter Total Deduction")    
                            # elif row['Net_Payable'] is None :  
                            #     messages.error(request,"Please enter Net Payable")             
                            # elif row['CB'] is None :  
                            #     messages.error(request,"Please enter CB")
                            # elif row['OB'] is None :  
                            #     messages.error(request,"Please enter OB")
                            # elif row['Payment_Rcpt_No'] is None :  
                            #     messages.error(request,"Please enter Payment Rcpt Number")
                            # elif row['Payment_Date'] is None :  
                            #     messages.error(request,"Please enter payment date in yyyy-mm-dd format ") 
                            # elif type(row['Member_Name']) != str:
                            #     messages.error(request,'Please Enter Member Name in  String only')         
                            # elif type(row['Phone No']) != int :  
                            #     messages.error(request,"Please enter Mobile Number  in number only")     
                            # elif type(row['Member_No'] ) != int :  
                            #     messages.error(request,"Please enter Member Number  in integer only")
                            # elif type( row['Month_Year'] ) != pd._libs.tslibs.timestamps.Timestamp :  
                            #     messages.error(request,"Please enter month year in  in mm-yyyy format only")  

                            # elif type(row['Total_Weight']) == str:  
                            #     messages.error(request,"Please enter Total Weight  in Decimal or Number only")
                            # elif type(row['RateGL']) == str :  
                            #     messages.error(request,"Please enter Rate GL worker in number only")
                            # elif type(row['Total_Value']) == str :  
                            #     messages.error(request,"Please enter Total Value in number only") 
                            # elif type(row['RateTF']) == str :  
                            #     messages.error(request,"Please enter Rate TF in number only")    
                            # elif type(row['Tft'])  == str :  
                            #     messages.error(request,"Please enter TFT in number only")
                            # elif type(row['SS']) == str :  
                            #     messages.error(request,"Please enter SS in number only")        
                            # elif type(row['RateFA']) == str :  
                            #     messages.error(request,"Please enter RateFA in number only") 
                            # elif type(row['FA']) == str :  
                            #     messages.error(request,"Please enter FA in number only") 
                            # elif type(row['Manure']) == str :  
                            #     messages.error(request,"Please enter Manure in number only") 
                            # elif type(row['Kadhi']) == str :  
                            #     messages.error(request,"Please enter Kadhi in number only") 
                            # elif type(row['GL_Adv'])  == str :  
                            #     messages.error(request,"Please enter GL_Adv in number only") 
                            # elif type(row['Hort']) == str :  
                            #     messages.error(request,"Please enter Hort in number only") 
                            # elif type(row['MBF']) == str :  
                            #     messages.error(request,"Please enter MBF in number only") 
                            # elif type(row['RoudOff_net']) == str :  
                            #     messages.error(request,"Please enter RoudOff_net in number only") 
                            # elif type(row['Total_Ded']) == str :  
                            #     messages.error(request,"Please enter Total_Ded in number only") 
                            # elif type(row['Net_Payable']) == str :  
                            #     messages.error(request,"Please enter Net_Payable in number only") 
                            # elif type(row['CB']) == str :  
                            #     messages.error(request,"Please enter CB in number only")    
                            # elif type(row['OB']) == str :  
                            #     messages.error(request,"Please enter OB in number only")  
                            # elif type(row['Payment_Date']) != pd._libs.tslibs.timestamps.Timestamp:  
                            #     messages.error(request,"Please enter payment date in dd/mm/yyyy format only")        
                            # # elif type(row['Payment_Rcpt_No']) is decimal.Decimal :  
                            # #     messages.error(request,"Please enter payment receipt number in number only")                                            
                            # elif (len(str(row['Phone No']))) != 10:
                            #      messages.error(request,"Please enter Phone number in 10 digit only")            
                            # elif type(row['Wt1'] ) == str:
                            #     messages.error(request,"Please enter Wt1 in number only")          
                            # elif type(row['Wt2'] ) == str:
                            #     messages.error(request,"Please enter Wt2 in number only")
                            # elif type(row['Wt3'] ) == str:
                            #     messages.error(request,"Please enter Wt3 in number only")
                            # # elif row['Wt4'] is not None:
                            # elif type(row['Wt4'] ) == str:
                            #     messages.error(request,"Please enter Wt4 in number only")
                            # elif type(row['Wt5'] ) == str:
                            #     messages.error(request,"Please enter Wt5 in number only")
                            # elif type(row['Wt6'] ) == str:
                            #     messages.error(request,"Please enter Wt6 in number only")
                            # elif type(row['Wt7'] ) == str:
                            #     messages.error(request,"Please enter Wt7 in number only")
                            # elif type(row['Wt8'] ) == str:
                            #     messages.error(request,"Please enter Wt8 in number only")
                            # elif type(row['Wt9'] ) == str:
                            #     messages.error(request,"Please enter Wt9 in number only")
                            # elif type(row['Wt10'] ) == str:
                            #     messages.error(request,"Please enter Wt10 in number only")
                            # elif type(row['Wt11'] ) == str:
                            #     messages.error(request,"Please enter Wt11 in number only")
                            # elif type(row['Wt12'] ) == str:
                            #     messages.error(request,"Please enter Wt12 in number only")
                            # elif type(row['Wt13'] ) == str:
                            #     messages.error(request,"Please enter Wt13 in number only")
                            # elif type(row['Wt14'] ) == str:
                            #     messages.error(request,"Please enter Wt14 in number only")
                            # elif type(row['Wt15'] ) == str:
                            #     messages.error(request,"Please enter Wt15 in number only")
                            # elif type(row['Wt16'] ) == str:
                            #     messages.error(request,"Please enter Wt16 in number only")        
                            # elif type(row['Wt17'] ) == str:
                            #     messages.error(request,"Please enter Wt17 in number only")
                            # elif type(row['Wt18'] ) == str:
                            #     messages.error(request,"Please enter Wt18 in number only")
                            # elif type(row['Wt19'] ) == str:
                            #     messages.error(request,"Please enter Wt19 in number only")                
                            # elif type(row['Wt20'] ) == str:
                            #     messages.error(request,"Please enter Wt20 in number only")        
                            # elif type(row['Wt21'] ) == str:
                            #     messages.error(request,"Please enter Wt21 in number only")        
                            # elif type(row['Wt22'] ) == str:
                            #     messages.error(request,"Please enter Wt22 in number only")
                            # elif type(row['Wt23'] ) == str:
                            #     messages.error(request,"Please enter Wt23 in number only")
                            # elif type(row['Wt24'] ) == str:
                            #     messages.error(request,"Please enter Wt24 in number only")
                            # elif type(row['Wt25'] ) == str:
                            #     messages.error(request,"Please enter Wt25 in number only")
                            # elif type(row['Wt26'] ) == str:
                            #     messages.error(request,"Please enter Wt26 in number only")
                            # elif type(row['Wt27'] ) == str:
                            #     messages.error(request,"Please enter Wt27 in number only")
                            # elif type(row['Wt28'] ) == str:
                            #     messages.error(request,"Please enter Wt28 in number only")
                            # elif type(row['Wt29'] ) == str:
                            #     messages.error(request,"Please enter Wt29 in number only")
                            # elif type(row['Wt30'] ) == str:
                            #     messages.error(request,"Please enter Wt30 in number only")
                            # elif type(row['Wt31'] ) == str:
                            #     messages.error(request,"Please enter Wt31 in number only")
                            # elif type(row['Adv1'] ) == str:
                            #     messages.error(request,"Please enter Adv1 in number only")          
                            # elif type(row['Adv2'] ) == str:
                            #     messages.error(request,"Please enter Adv2 in number only")
                            # elif type(row['Adv3'] ) == str:
                            #     messages.error(request,"Please enter Adv3 in number only")
                            # elif type(row['Adv4'] ) == str:
                            #     messages.error(request,"Please enter Adv4 in number only")
                            # elif type(row['Adv5'] ) == str:
                            #     messages.error(request,"Please enter Wt5 in number only")
                            # elif type(row['Adv6'] ) == str:
                            #     messages.error(request,"Please enter Adv6 in number only")
                            # elif type(row['Adv7'] ) == str:
                            #     messages.error(request,"Please enter Adv7 in number only")
                            # elif type(row['Adv8'] ) == str:
                            #     messages.error(request,"Please enter Adv8 in number only")
                            # elif type(row['Adv9'] ) == str:
                            #     messages.error(request,"Please enter Adv9 in number only")
                            # elif type(row['Adv10'] ) == str:
                            #     messages.error(request,"Please enter Adv10 in number only")
                            # elif type(row['Adv11'] ) == str:
                            #     messages.error(request,"Please enter Adv11 in number only")
                            # elif type(row['Adv12'] ) == str:
                            #     messages.error(request,"Please enter Adv12 in number only")
                            # elif type(row['Adv13'] ) == str:
                            #     messages.error(request,"Please enter Adv13 in number only")
                            # elif type(row['Adv14'] ) == str:
                            #     messages.error(request,"Please enter Adv14 in number only")
                            # elif type(row['Adv15'] ) == str:
                            #     messages.error(request,"Please enter Adv15 in number only")
                            # elif type(row['Adv16'] ) == str:
                            #     messages.error(request,"Please enter Adv16 in number only")        
                            # elif type(row['Adv17'] ) == str:
                            #     messages.error(request,"Please enter Adv17 in number only")
                            # elif type(row['Adv18'] ) == str:
                            #     messages.error(request,"Please enter Adv18 in number only")
                            # elif type(row['Adv19'] ) == str:
                            #     messages.error(request,"Please enter Adv19 in number only")                
                            # elif type(row['Adv20'] ) == str:
                            #     messages.error(request,"Please enter Adv20 in number only")        
                            # elif type(row['Adv21'] ) == str:
                            #     messages.error(request,"Please enter Adv21 in number only")        
                            # elif type(row['Adv22'] ) == str:
                            #     messages.error(request,"Please enter Adv22 in number only")
                            # elif type(row['Adv23'] ) == str:
                            #     messages.error(request,"Please enter Adv23 in number only")
                            # elif type(row['Adv24'] ) == str:
                            #     messages.error(request,"Please enter Adv24 in number only")
                            # elif type(row['Adv25'] ) == str:
                            #     messages.error(request,"Please enter Adv25 in number only")
                            # elif type(row['Adv26'] ) == str:
                            #     messages.error(request,"Please enter Adv26 in number only")
                            # elif type(row['Adv27'] ) == str:
                            #     messages.error(request,"Please enter Adv27 in number only")
                            # elif type(row['Adv28'] ) == str:
                            #     messages.error(request,"Please enter Adv28 in number only")
                            # elif type(row['Adv29'] ) == str:
                            #     messages.error(request,"Please enter Adv29 in number only")
                            # elif type(row['Adv30'] ) == str:
                            #     messages.error(request,"Please enter Adv30 in number only")
                            # elif type(row['Adv31'] ) == str:
                            #     messages.error(request,"Please enter Adv31 in number only")
                            # elif type(row['GWt1'] ) == str:
                            #     messages.error(request,"Please enter GWt1 in number only")          
                            # elif type(row['GWt2'] ) == str:
                            #     messages.error(request,"Please enter GWt2 in number only")
                            # elif type(row['GWt3'] ) == str:
                            #     messages.error(request,"Please enter GWt3 in number only")
                            # elif type(row['GWt4'] ) == str:
                            #     messages.error(request,"Please enter GWt4 in number only")
                            # elif type(row['GWt5'] ) == str:
                            #     messages.error(request,"Please enter GWt5 in number only")
                            # elif type(row['GWt6'] ) == str:
                            #     messages.error(request,"Please enter GWt6 in number only")
                            # elif type(row['GWt7'] ) == str:
                            #     messages.error(request,"Please enter GWt7 in number only")
                            # elif type(row['GWt8'] ) == str:
                            #     messages.error(request,"Please enter GWt8 in number only")
                            # elif type(row['GWt9'] ) == str:
                            #     messages.error(request,"Please enter GWt9 in number only")
                            # elif type(row['GWt10'] ) == str:
                            #     messages.error(request,"Please enter GWt10 in number only")
                            # elif type(row['GWt11'] ) == str:
                            #     messages.error(request,"Please enter GWt11 in number only")
                            # elif type(row['GWt12'] ) == str:
                            #     messages.error(request,"Please enter GWt12 in number only")
                            # elif type(row['GWt13'] ) == str:
                            #     messages.error(request,"Please enter GWt13 in number only")
                            # elif type(row['GWt14'] ) == str:
                            #     messages.error(request,"Please enter GWt14 in number only")
                            # elif type(row['GWt15'] ) == str:
                            #     messages.error(request,"Please enter GWt15 in number only")
                            # elif type(row['GWt16'] ) == str:
                            #     messages.error(request,"Please enter GWt16 in number only")        
                            # elif type(row['GWt17'] ) == str:
                            #     messages.error(request,"Please enter GWt17 in number only")
                            # elif type(row['GWt18'] ) == str:
                            #     messages.error(request,"Please enter GWt18 in number only")
                            # elif type(row['GWt19'] ) == str:
                            #     messages.error(request,"Please enter GWt19 in number only")                
                            # elif type(row['GWt20'] ) == str:
                            #     messages.error(request,"Please enter GWt20 in number only")        
                            # elif type(row['GWt21'] ) == str:
                            #     messages.error(request,"Please enter GWt21 in number only")        
                            # elif type(row['GWt22'] ) == str:
                            #     messages.error(request,"Please enter GWt22 in number only")
                            # elif type(row['GWt23'] ) == str:
                            #     messages.error(request,"Please enter GWt23 in number only")
                            # elif type(row['GWt24'] ) == str:
                            #     messages.error(request,"Please enter GWt24 in number only")
                            # elif type(row['GWt25'] ) == str:
                            #     messages.error(request,"Please enter GWt25 in number only")
                            # elif type(row['GWt26'] ) == str:
                            #     messages.error(request,"Please enter GWt26 in number only")
                            # elif type(row['GWt27'] ) == str:
                            #     messages.error(request,"Please enter GWt27 in number only")
                            # elif type(row['GWt28'] ) == str:
                            #     messages.error(request,"Please enter GWt28 in number only")
                            # elif type(row['GWt29'] ) == str:
                            #     messages.error(request,"Please enter GWt29 in number only")
                            # elif type(row['GWt30'] ) == str:
                            #     messages.error(request,"Please enter GWt30 in number only")
                            # elif type(row['GWt31'] ) == str:
                            #     messages.error(request,"Please enter GWt31 in number only")       
                            # elif type(row['Misc1'] ) == str:
                            #     messages.error(request,"Please enter Misc1 in number only")
                            # elif type(row['Misc2'] ) == str:
                            #     messages.error(request,"Please enter Misc2 in number only")                                                                                                
                            # elif type(row['Misc3'] ) == str:
                            #     messages.error(request,"Please enter Misc3 in number only")

                            elif EasyWeightMaster.objects.filter(collection_center_id=collection_center.id,tracetea_id__username=row['tracetea ID'].strip(),\
                                                                 month_year__iexact= month_year).exists():
                                try:
                                    tracetead_id=row['tracetea ID'].strip()
                                    obj = EasyWeightMaster.cmobjects.get(collection_center_id=collection_center.id,\
                                                                         tracetea_id__username=tracetead_id,\
                                                                            month_year__iexact=month_year)
                                    obj.member_no=row['Member_No']
                                    obj.member_name=row['Member_Name']
                                    obj.mobile_number=row['Phone No']
                                    obj.month_year=  month_year #row['Month_Year']
                                    obj.total_weight=row['Total_Weight']
                                    obj.rate_gl=row['RateGL']
                                    obj.total_value=row['Total_Value']
                                    obj.rate_tf=row['RateTF']
                                    obj.tft=row['Tft']
                                    obj.ss=row['SS']
                                    obj.rate_fa=row['RateFA']
                                    obj.fa=row['FA']
                                    obj.manure=row['Manure']
                                    obj.kadhi=row['Kadhi']
                                    obj.gl_adv=row['GL_Adv']
                                    obj.hort=row['Hort']
                                    obj.mbf=row['MBF']
                                    obj.roud_off_net=row['RoudOff_net']
                                    obj.total_ded=row['Total_Ded']
                                    obj.net_payable=row['Net_Payable']
                                    obj.cb=row['CB']
                                    obj.ob=row['OB']
                                    obj.payment_rcpt_no=row['Payment_Rcpt_No']
                                    obj.payment_date=row['Payment_Date']
                                    obj.updated_by=request.user
                                    obj.save()
                                    successful_update +=1
                                    for i in range(1,32):
                                        i=str(i)
                                        if row['Wt'+i]:
                                            if EasyWeightWt.cmobjects.filter(easy_weight=obj,wt="day"+i).exists():
                                                obj2=EasyWeightWt.cmobjects.filter(easy_weight=obj,wt="day"+i).update(value=row['Wt'+i])
                                            else:
                                                obj2=EasyWeightWt(easy_weight=obj)
                                                obj2.wt="day"+i
                                                obj2.value=row['Wt'+i]
                                                obj2.save()
                                        if row['Adv'+i] :
                                            if EasyWeightAdv.cmobjects.filter(easy_weight=obj,adv="day"+i).exists():
                                                obj3=EasyWeightAdv.cmobjects.filter(easy_weight=obj,adv="day"+i).update(value=row['Adv'+i])
                                            else:
                                                obj3=EasyWeightAdv(easy_weight=obj)
                                                obj3.adv="day"+i
                                                obj3.value=row['Adv'+i]
                                                obj3.save()
                                        if row['GWt'+i] :
                                            if EasyWeightGwt.cmobjects.filter(easy_weight=obj,gwt="day"+i).exists():
                                                obj4=EasyWeightGwt.cmobjects.filter(easy_weight=obj,gwt="day"+i).update(value=row['GWt'+i])
                                            else:
                                                obj4=EasyWeightGwt(easy_weight=obj)
                                                obj4.gwt="day"+i
                                                obj4.value=row['GWt'+i]
                                                obj4.save()   
                                    for i in range(1,4)  :  
                                        i=str(i)       
                                        if row['Misc'+i] :
                                            if EasyWeightMisc.cmobjects.filter(easy_weight=obj,misc="day"+i).exists():
                                                obj5=EasyWeightMisc.cmobjects.filter(easy_weight=obj,misc="day"+i).update(value=row['Misc'+i])
                                            else:
                                                obj5 = EasyWeightMisc(easy_weight=obj)
                                                obj5.misc="day"+i
                                                obj5.value=row['Misc'+i]
                                                obj5.save()

                                    messages.success(request, "Total "+ str(successful_update)  +' data updated successfully in leaf receipt(easy weight)')        
                                except EasyWeightMaster.DoesNotExist:
                                      messages.error(request,"")  
                                       
                            else:

                                try :
                                    # for i in range(1,4)  :  
                                    #     i=str(i)       
                                    #     if row['Misc'+i] is not None:
                                    #         if type(row['Misc'+i] ) == str:
                                    #             messages.error(request,"Please enter Misc" + i + "in number only")  
                                    #             break 
                                    # for i in range(1,32):
                                    #     i=str(i)
                                    #     if row['Wt'+i] is not None :
                                    #         if type(row['Wt'+i] ) == str:
                                    #             messages.error(request,"Please enter Wt" + i + "in number only")  

                                    #     if row['Adv'+i] is not None :
                                    #         if type(row['Adv'+i]) == str :
                                    #             messages.error(request,"Please enter Adv" + i + "in number only") 

                                    #     if row['GWt'+i] is not None :
                                    #         if type(row['GWt'+i])  == str:
                                    #             messages.error(request,"Please enter Gwt" + i + "in number only")
                                    try:
                                        tracetead_id=row['tracetea ID'].strip()
                                        tracetead_id=User.objects.get(username=tracetead_id)
                                    except User.DoesNotExist:
                                        tracetead_id=None

                                    if tracetead_id: 
                                        obj = EasyWeightMaster.cmobjects.create(collection_center=collection_center,)
                                        obj.tracetea_id=tracetead_id   
                                        obj.member_no=row['Member_No']
                                        obj.member_name=row['Member_Name']
                                        obj.mobile_number=row['Phone No']
                                        obj.month_year=  month_year #row['Month_Year']
                                        obj.total_weight=row['Total_Weight']
                                        obj.rate_gl=row['RateGL']
                                        obj.total_value=row['Total_Value']
                                        obj.rate_tf=row['RateTF']
                                        obj.tft=row['Tft']
                                        obj.ss=row['SS']
                                        obj.rate_fa=row['RateFA']
                                        obj.fa=row['FA']
                                        obj.manure=row['Manure']
                                        obj.kadhi=row['Kadhi']
                                        obj.gl_adv=row['GL_Adv']
                                        obj.hort=row['Hort']
                                        obj.mbf=row['MBF']
                                        obj.roud_off_net=row['RoudOff_net']
                                        obj.total_ded=row['Total_Ded']
                                        obj.net_payable=row['Net_Payable']
                                        obj.cb=row['CB']
                                        obj.ob=row['OB']
                                        obj.payment_rcpt_no=row['Payment_Rcpt_No']
                                        obj.payment_date=row['Payment_Date']
                                        obj.created_by=request.user
                                        obj.save()
                                        for i in range(1,32):
                                            i=str(i)
                                            if row['Wt'+i]:
                                                obj2=EasyWeightWt(easy_weight=obj)
                                                obj2.wt="day"+i
                                                obj2.value=row['Wt'+i]
                                                obj2.save()
                                            if row['Adv'+i] :
                                                obj3=EasyWeightAdv(easy_weight=obj)
                                                obj3.adv="day"+i
                                                obj3.value=row['Adv'+i]
                                                obj3.save()
                                            if row['GWt'+i] :
                                                obj4=EasyWeightGwt(easy_weight=obj)
                                                obj4.gwt="day"+i
                                                obj4.value=row['GWt'+i]
                                                obj4.save()   
                                        for i in range(1,4)  :  
                                            i=str(i)       
                                            if row['Misc'+i] :
                                                obj5=EasyWeightMisc(easy_weight=obj)
                                                obj5.misc="day"+i
                                                obj5.value=row['Misc'+i]
                                                obj5.save() 
                                        successful_upload +=1
                                        # messages.success(request, str(row['tracetea ID']) + ' Data uploaded successfully in leaf receipt(easy weight)')                         
                                    else:
                                        messages.error(request,'TraceTea ID'+ " : " + str(row['tracetea ID']) + ' not exist')
                                except  User.DoesNotExist:
                                        # messages.error(request,'please check the excel data') 
                                        pass
                messages.success(request,"Total " + str(successful_upload) + ' data uploaded successfully in leaf receipt(easy weight)')                         
            except  KeyError:
                    messages.error(request,"something went wrong")
        else:
            form = EasyWeightForm()

        context={
		'form' : form,
	    }
    context={
		'form' : EasyWeightForm(),
	    }

    return CommonMixin.render(request, 'import_easy_weight.html',context)







# EXCEL EASY WEITGHT 

import openpyxl
from django.http import HttpResponse
from .models import EasyWeightMaster, EasyWeightWt, EasyWeightAdv, EasyWeightGwt, EasyWeightMisc













@login_required
def export_easy_weight_data(request):

    entity_id = request.GET.get('entity_id', '')
    month_year = request.GET.get('month_year', '')

    print("month_year", month_year)

    # Assuming BlfProfile and User are your models and 'cmobjects' is a custom manager
    blf_details = BlfProfile.objects.filter(pk=entity_id).first()
    if blf_details:
        blf_username = blf_details.user
        blf_user_details = User.objects.filter(username=blf_username).first()
    else:
        blf_user_details = None

    easy_weight_masters = EasyWeightMaster.objects.filter(created_by=blf_user_details, month_year=month_year)

    print(f"easy_weight_masters ###={easy_weight_masters}")

    # Create a workbook and activate a worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Easy Weight Data"

    # Define the header
    header = [
        'tracetea ID', 'Member_No', 'Member_Name', 'Phone No', 'Month_Year', 'Total_Weight',
        'Wt1', 'Wt2', 'Wt3', 'Wt4', 'Wt5', 'Wt6', 'Wt7', 'Wt8', 'Wt9', 'Wt10', 'Wt11', 'Wt12', 'Wt13', 'Wt14', 'Wt15', 
        'Wt16', 'Wt17', 'Wt18', 'Wt19', 'Wt20', 'Wt21', 'Wt22', 'Wt23', 'Wt24', 'Wt25', 'Wt26', 'Wt27', 'Wt28', 'Wt29', 
        'Wt30', 'Wt31', 'Adv1', 'Adv2', 'Adv3', 'Adv4', 'Adv5', 'Adv6', 'Adv7', 'Adv8', 'Adv9', 'Adv10', 'Adv11', 'Adv12',
        'Adv13', 'Adv14', 'Adv15', 'Adv16', 'Adv17', 'Adv18', 'Adv19', 'Adv20', 'Adv21', 'Adv22', 'Adv23', 'Adv24', 'Adv25',
        'Adv26', 'Adv27', 'Adv28', 'Adv29', 'Adv30', 'Adv31', 'RateGL', 'Total_Value', 'RateTF', 'Tft', 'SS', 'RateFA', 
        'FA', 'Manure', 'Kadhi', 'GL_Adv', 'Hort', 'MBF', 'Misc1', 'Misc2', 'Misc3', 'RoudOff_net', 'Total_Ded', 'Net_Payable',
        'CB', 'OB', 'Payment_Rcpt_No', 'Payment_Date', 'GWt1', 'GWt2', 'GWt3', 'GWt4', 'GWt5', 'GWt6', 'GWt7', 'GWt8', 'GWt9',
        'GWt10', 'GWt11', 'GWt12', 'GWt13', 'GWt14', 'GWt15', 'GWt16', 'GWt17', 'GWt18', 'GWt19', 'GWt20', 'GWt21', 'GWt22',
        'GWt23', 'GWt24', 'GWt25', 'GWt26', 'GWt27', 'GWt28', 'GWt29', 'GWt30', 'GWt31'
    ]
    ws.append(header)

    for master in easy_weight_masters:
        # Get related data from EasyWeightWt, EasyWeightAdv, EasyWeightGwt, and EasyWeightMisc
        wts = master.wt_easy_weight_master.all()
        advs = master.adv_easy_weight_master.all()
        gwts = master.gwt_easy_weight_master.all()
        miscs = master.misc_easy_weight_master.all()

        # Convert User instance to a string (e.g., using the username or email)
        tracetea_id = master.tracetea_id.username if master.tracetea_id else ''

        # Create row data
        row = [
            tracetea_id, master.member_no, master.member_name, master.mobile_number, master.month_year,
            master.total_weight
        ]

        # Add Wt1 to Wt31
        row.extend([wt.wt for wt in wts])

        # Add Adv1 to Adv31
        row.extend([adv.adv for adv in advs])

        # Add RateGL, Total_Value, etc.
        row.extend([
            master.rate_gl, master.total_value, master.rate_tf, master.tft, master.ss, master.rate_fa, master.fa,
            master.manure, master.kadhi, master.gl_adv, master.hort, master.mbf
        ])

        # Add Misc1 to Misc3
        row.extend([misc.misc for misc in miscs])

        # Add RoudOff_net, Total_Ded, etc.
        row.extend([
            master.roud_off_net, master.total_ded, master.net_payable, master.cb, master.ob,
            master.payment_rcpt_no, master.payment_date
        ])

        # Add GWt1 to GWt31
        row.extend([gwt.gwt for gwt in gwts])

        # Append row data to the worksheet
        ws.append(row)

    # Create a response object with the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=easy_weight_data.xlsx'

    # Save the workbook to the response
    wb.save(response)

    return response
