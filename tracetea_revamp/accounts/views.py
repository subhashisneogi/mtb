import json
import urllib
import requests
import random
import datetime
import collections
from master.utils import send_sms
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login 
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from .forms import CreateUserForm, UserCustomPasswordChangeForm
from rest_framework.response import Response
from rest_framework.views import APIView
import qrcode
import io
from django.http import HttpResponse
from PIL import Image
from user_profile.models import * 
from .serializers import *
from django.utils import timezone  # Import Django's timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from master.common import CommonMixin
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from django.contrib.auth import login,logout
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from django.db import transaction
from master.common import CommonMixin
from .utils import *
import pytz
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
import httpagentparser
from datetime import datetime, date, timedelta
import pyotp
from django.utils.decorators import method_decorator

def admin_login(request):
	context = {}
	if request.method == "POST":
		email = request.POST['email']
		password = request.POST['password']
		user_details = User.objects.filter(Q(email=email) | Q(username=email)).first()
		if user_details:
			username = user_details.username
			user = authenticate(username=username,password=password)
			if user:
				profile_details = Profile.objects.filter(user=user_details).first()
				usery_type = profile_details.user_type.name
				if usery_type == "blf" or usery_type == "ADMIN":
					login(request, user_details)
					request.session['email'] = email
					request.session['password'] = password
					request.session['username'] = username
					messages.success(request, 'Login Successfully')
					return redirect(reverse('index'))
				else:
					messages.error(request,'User Type must be BLF or Admin')
			else:
				print("Username or Password is wrong")
				messages.error(request,'Email or password is wrong')
		else:
			print("Username or Password is wrong")
			messages.error(request,'Username or Password is wrong')
	return render(request,'accounts/login.html', context)

class LoginFailedException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = {"msg": "Please check the username and password"}
    default_code = "login_failed"

class AccountDisabledException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = {"msg": "The account has been disabled!"}
    default_code = "account_disabled"

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(KnoxLoginView):
	permission_classes = [AllowAny]
	def post(self, request, *args, **kwargs):
		if 'id' in request.data:
			user = User.objects.get(pk=request.data['id'])
			odict = self.getUserDetails(user, request)
			return Response(odict)
		serializer = LoginSerializer(data=request.data)
		try:
			serializer.is_valid(raise_exception=True)
		except ValidationError as e:
			detail = e.detail if hasattr(e, "detail") else {"msg": ["Login failed"]}
			raise LoginFailedException(detail)

		user = serializer.validated_data
		update_last_login(None, user)
		login_data = login(request, user)
		if user:
			odict = self.getUserDetails(user, request)
			return Response(odict)

	def generate_qr_code(self, qr_code, user_id,user_type):
		qr_code=json.dumps(qr_code)
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_L,
			box_size=10,
			border=4,
		)
		qr.add_data(qr_code)
		qr.make(fit=True)
		qr_code_image = qr.make_image(fill_color="black", back_color="white")	
		qr_code_directory = os.path.join(settings.MEDIA_DIR, "qrcode")  # Create a 'qrcodes' directory
		os.makedirs(qr_code_directory, exist_ok=True)		
		qr_code_image_filename = f"{user_type}_{user_id}_qrcode.png"	
		qr_code_image_path = os.path.join(qr_code_directory, qr_code_image_filename)
		qr_code_image.save(qr_code_image_path)		
		return qr_code_image_path

	def getUserDetails(self, user, request):	
		profile_model=[AggregatorProfile,GrowerProfile,BlfProfile,]
		if AggregatorProfile.objects.filter(user_id=user).exists():
			user_details =AggregatorProfile.objects.filter(user_id=user).first()
			print(user_details)

		elif GrowerProfile.objects.filter(user_id=user).exists():
			user_details =GrowerProfile.objects.filter(user_id=user).first()
			print(user_details)
		elif BlfProfile.objects.filter(user_id=user).exists(): 
			user_details =BlfProfile.objects.filter(user_id=user).first()	
			print(user_details)
		else:
			odict = collections.OrderedDict()
			print("check user")
			odict['user_id'] = user.pk
			odict['token'] = AuthToken.objects.create(user)[1]
			odict['username'] = user.username
			odict['first_name'] = user.first_name
			odict['last_name'] = user.last_name
			odict['email'] = user.email
			odict['is_admin'] = user.is_superuser
			odict['profile_type'] = ""
			odict['is_superuser'] = user.is_superuser
			odict['request_status'] = 1
			odict['msg'] = "Logged in successfully .."
			odict['switchUser'] = ''
			log = LoginLogoutLoggedTable.objects.create(user=user, token=odict['token'],  )
			return odict		
		if user_details:
			grower= GrowerProfile.objects.filter(user_id=user)
			aggregator= AggregatorProfile.objects.filter(user_id=user)
			blf= BlfProfile.objects.filter(user_id=user)
			if 	grower:
				qr_code=GrowerProfile.objects.filter(user_id=user).first()	
				user_type="grower"
				user_id=qr_code.user
				print("print qr",qr_code)
				qr_code = {
						'user_id': qr_code.user.id,
						'name': qr_code.name,
						'id': qr_code.id,
						'username': qr_code.user.username
					}
				qr_code_image_path = self.generate_qr_code(qr_code,user_id ,user_type)
				if not qr_code_image_path:
					return Response({
						'msg': 'Failed to generate and save QR code image',
						'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
					}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
				http_or_https ='https'
				media_url = settings.MEDIA_URL.rstrip('/')
				absolute_qr_code_image_url = request.build_absolute_uri(
					qr_code_image_path.replace(settings.MEDIA_DIR, media_url).replace("\\", "/")
				)
				absolute_qr_code_image_url = absolute_qr_code_image_url.replace(
					'http', http_or_https, 1
				)
			elif aggregator:
				qr_code=AggregatorProfile.objects.filter(user_id=user).first()	
				user_type="aggregator"
				user_id=qr_code.user
				qr_code = {
						'user_id': qr_code.user.id,
						'name': qr_code.name,
						'id': qr_code.id,
						'username': qr_code.user.username
					}
				qr_code_image_path = self.generate_qr_code(qr_code,user_id ,user_type)
				if not qr_code_image_path:
					return Response({
						'msg': 'Failed to generate and save QR code image',
						'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
					}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
				http_or_https ='https'
				media_url = settings.MEDIA_URL.rstrip('/')
				absolute_qr_code_image_url = request.build_absolute_uri(
					qr_code_image_path.replace(settings.MEDIA_DIR, media_url).replace("\\", "/")
				)
				absolute_qr_code_image_url = absolute_qr_code_image_url.replace(
					'http', http_or_https, 1
				)
			elif blf:
				qr_code=BlfProfile.objects.filter(user_id=user).first()	
				user_type="blf"
				user_id=qr_code.user
				qr_code = {
						'userid': qr_code.user.id,
						'name': qr_code.entity_unit,
						'id': qr_code.id,
						'username': qr_code.user.username
					}
				qr_code_image_path = self.generate_qr_code(qr_code,user_id ,user_type)
				if not qr_code_image_path:
					return Response({
						'msg': 'Failed to generate and save QR code image',
						'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
					}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
				http_or_https ='https'
				media_url = settings.MEDIA_URL.rstrip('/')
				absolute_qr_code_image_url = request.build_absolute_uri(
					qr_code_image_path.replace(settings.MEDIA_DIR, media_url).replace("\\", "/")
				)
				absolute_qr_code_image_url = absolute_qr_code_image_url.replace(
					'http', http_or_https, 1
				)
			else:
				absolute_qr_code_image_url=""
			odict = collections.OrderedDict()
			odict['user_id'] = user.pk
			odict['token'] = AuthToken.objects.create(user)[1]    
			odict['username'] = user.username
			odict['first_name'] = user.first_name
			odict['last_name'] = user.last_name
			odict['email'] = user.email
			odict['is_admin'] = user.is_superuser
			odict['profile_type'] = ProfileType.objects.filter(id=user_details.profile_type_id).values('name') if user_details else ""
			odict['profile_id']=  user_details.id  if user_details else ""
			for item in odict['profile_type']:
				if item['name'] == 'blf':
					odict['name']=   user_details.entity_unit  if user_details else ""
				else:
					odict['name']=  user_details.name  if user_details else ""
			odict['qr_code']=  absolute_qr_code_image_url 
			odict['is_superuser'] = user.is_superuser 
			odict['cu_mobile_number'] = user_details.mobile_number if user_details else ""
			if user_details and hasattr(user_details, 'region') and hasattr(user_details.region, 'region_name'):
				odict['region'] = user_details.region.region_name
			else:
				odict['region'] = ""
			if user_details and hasattr(user_details, 'state') and hasattr(user_details.state, 'name'):
				odict['state'] = user_details.state.name
			else:
				odict['state'] = ""		
			if user_details and hasattr(user_details, 'district') and hasattr(user_details.district, 'name'):
				odict['district'] = user_details.district.name
			else:
				odict['district'] = ""			
			if user_details and hasattr(user_details, 'aadhar_no'):
				odict['aadhar_no'] = user_details.aadhar_no
			else:
				odict['aadhar_no'] = ""
			if user_details and hasattr(user_details, 'voter_id'):
				odict['voter_id'] = user_details.voter_id
			else:
				odict['voter_id'] = ""		
			if user_details and hasattr(user_details, 'pincode'):
				odict['pincode'] = user_details.pincode
			else:
				odict['pincode'] = ""	
			if user_details and hasattr(user_details, 'address'):
				odict['address'] = user_details.address
			else:
				odict['address'] = ""	
			if user_details and hasattr(user_details, 'tea_board_id'):
				odict['tea_board_id'] = user_details.tea_board_id
			else:
				odict['tea_board_id'] = ""		
			if user_details and hasattr(user_details, 'total_male_worker'):
				odict['total_male_worker'] = str(user_details.total_male_worker)
			else:
				odict['total_male_worker'] = ""			
			if user_details and hasattr(user_details, 'total_female_worker'):
				odict['total_female_worker'] = str(user_details.total_female_worker)
			else:
				odict['total_female_worker'] = ""				
			if user_details and hasattr(user_details, 'user_file') and user_details.user_file:
				print(user_details.user_file)
				user_file_path = os.path.join(settings.MEDIA_URL, str(user_details.user_file))
				complete_url = request.build_absolute_uri(user_file_path)
				odict['image'] = complete_url
			elif user_details and hasattr(user_details, 'photo') and user_details.photo:
				user_file_path = os.path.join(settings.MEDIA_URL, str(user_details.photo))
				complete_url = request.build_absolute_uri(user_file_path)
				odict['image'] = complete_url		
			else:
				odict['image'] = ""
			odict['is_active'] = user_details.is_active if user_details else ""
			odict['request_status'] = 1
			odict['msg'] = "Logged in successfully .."
			odict['switchUser'] = ''
			log = LoginLogoutLoggedTable.objects.create(user=user, token=odict['token'])
			return odict
		
	def detectBrowser(self):
		user_ip = self.request.META.get('REMOTE_ADDR')
		agent = self.request.META.get('HTTP_USER_AGENT')
		browser = httpagentparser.detect(agent)
		browser_name = agent.split('/')[0] if not "browser" in browser.keys() else browser['browser']['name']
		os_name = "" if not "os" in browser.keys() else browser['os']['name']
		return browser_name, user_ip, os_name

class RequestOTPAPIView(APIView):
	permission_classes = [AllowAny]
	def post(self, request, *args, **kwargs):
		phone_no = request.data['phone_no']
		user_details = Profile.cmobjects.filter(phone_no=phone_no, is_allow_otp_login=True).first()
		data = {}
		if user_details:
			# expiry_time = int(os.getenv('OTP_EXPIRY', '5'))
			# hotp = pyotp.HOTP(pyotp.random_base32(),digits=int(os.getenv('OTP_LENGTH', '4')))
			# otp_rand = int(os.getenv('OTP_RAND', '1234'))
			# expiry = datetime.now() + timedelta(minutes=expiry_time)
			# user_otp = UserOTP.objects.create(user=user_details.user,otp_secret=hotp.secret,expiry=expiry)

			expiry_time = int(os.getenv('OTP_EXPIRY', '5'))
			secret = pyotp.random_base32()
			totp = pyotp.TOTP(secret, digits=4)
			otp_value = totp.now()  
			expiry = datetime.now() + timedelta(minutes=expiry_time)
			user_otp = UserOTP.objects.create(
				user=user_details.user,
				otp_secret=secret,
				expiry=expiry
			)
			otp = otp_value
			if user_otp:
				pass
				# ist_time = timezone.now().astimezone(timezone.pytz.timezone('Asia/Kolkata'))  # Convert to IST
				# if mobile_number:
				# 	template_id='1007983856203558873'
				# 	message=f"Hi, Your one time password is:{otp}. Please don't share this with anyone - Trustea."
				# 	print(message)
				# 	send_sms(mobile_number, message, template_id)
			data = {
				'otp': otp,
				'phone_no': phone_no,
				'username':user_details.user.username if user_details.user.username else '',
				'user_id':user_details.user.id if user_details.user else None,
				'user_type':user_details.user_type.name if user_details.user_type else "",
			}
		else:
			raise APIException({'request_status': 1, 'msg': "The phone number entered is invalid!"})
		return Response ({
			'results': {'Data': data},
			'msg': 'We have sent you an OTP to your mobile number',
			'status': status.HTTP_200_OK,
		})
	
class ValidateOTP(APIView):
	permission_classes = [AllowAny]
	def post(self, request, *args, **kwargs):
		otp = request.data.get('otp')
		user_id = request.data.get('user_id')
		try:	
			with transaction.atomic():
				if not (user_id and otp):
					raise APIException({'request_status': 0, 'msg': "Mobile number, user_id or OTP not received in request"})
				try:
					user_otp = UserOTP.cmobjects.filter(user_id=user_id, is_used=False).latest('created_at')
				except UserOTP.DoesNotExist:
					raise APIException({'request_status': 0,'msg': "No active OTP found for this user"})
				if timezone.now() > user_otp.expiry:
					raise APIException({'request_status': 0, 'msg': "OTP has expired"})
				totp = pyotp.TOTP(user_otp.otp_secret, digits=4)
				if not totp.verify(str(otp), valid_window=1): 
					raise APIException({'request_status': 0, 'msg': "Invalid OTP"})
				user_otp.is_used = True
				user_otp.save(update_fields=['is_used'])
				return Response({
					'request_status': 1,
					'msg': "OTP validated successfully",
					'user_id': user_id
				})
		except APIException as e:
			raise e
		except Exception as e:
			raise APIException({
				'request_status': 0,
				'msg': str(e)
			})
		
class SetNewPassWordAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SetNewPasswordSerializer
    def put(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'msg': 'Password successfully reset.'}, status=status.HTTP_200_OK)

@login_required
def change_password_view(request):
	"""
	Change Password View
	"""
	if request.method == 'POST':
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # Important!
			messages.success(
				request, 'Your password was successfully updated!')
			return redirect('accounts:change_password')

		messages.error(request, 'Please correct the error below.')
	else:
		form = PasswordChangeForm(request.user)
	context = {
		'form': form,
	}
	return CommonMixin.render(request, 'change_password.html', context)

@login_required
def users_change_password_view(request, user_id):
	"""
	Users Change Password View
	"""
	user_details = User.objects.filter(id=user_id).first()

	if request.method == 'POST':
		form = CustomPasswordChangeForm(user_id, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # Important!
			messages.success(
				request, 'Your password was successfully updated!')
			return redirect('accounts:change_password')

		messages.error(request, 'Please correct the error below.')
	else:
		form = PasswordChangeForm(request.user)

	context = {
		'form': form,
	}
	return CommonMixin.render(request, 'users_change_password.html', context)




from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
User = get_user_model()
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from master.common import CommonMixin
from django.contrib.auth import get_user_model

# class PasswordChangeView(LoginRequiredMixin, UpdateView):
#     template_name = 'users_change_password.html'

#     def get(self, request, user_id):
#         form = UserCustomPasswordChangeForm()
#         context = {'form': form}
#         user_type_details = Profile.objects.filter(user_id=self.kwargs['user_id']).first()
#         context['user_type_details'] = user_type_details
#         user_type = user_type_details.user_type
#         context['user_type'] = user_type

#         context['usertype_list'] = ProfileType.objects.exclude(name="ADMIN").order_by('-id')
#         context['blf_details'] = BlfProfile.objects.filter(user_id=self.kwargs['user_id']).first()

#         user_details = Profile.objects.filter(user_id=self.request.user.id).first()
#         context['logged_user_type'] = str(user_details.user_type)

#         return render(request, self.template_name, context)

#     def post(self, request, user_id):
#         user = get_object_or_404(get_user_model(), id=user_id)
#         form = UserCustomPasswordChangeForm(request.POST, instance=user)

#         if form.is_valid():
#             form.save()

#             user_type_details = Profile.objects.filter(user_id=user_id).first()
#             user_type = user_type_details.user_type

#             update_session_auth_hash(request, user)
#             messages.success(request, 'Your password was successfully updated!')
#             return redirect(reverse('user_profile:all_users', kwargs={"usertype_slug": user_type}))

#         messages.error(request, 'Please correct the error below.')
#         context = {'form': form}
#         return render(request, self.template_name, context)












# class PasswordChangeView(LoginRequiredMixin, UpdateView):
# 	template_name = 'users_change_password.html'
# 	form_class = UserCustomPasswordChangeForm

# 	def get(self, request, user_id):
# 		form = self.form_class()
# 		context = {'form': form}
# 		user_type_details = Profile.objects.filter(user_id=self.kwargs['user_id']).first()
# 		context['user_type_details'] = user_type_details
# 		user_type = user_type_details.user_type
# 		context['user_type'] = user_type

# 		context['usertype_list'] = ProfileType.objects.exclude(name="ADMIN").order_by('-id')
# 		context['blf_details'] = BlfProfile.objects.filter(user_id=self.kwargs['user_id']).first()

# 		user_details = Profile.objects.filter(user_id=self.request.user.id).first()
# 		context['logged_user_type'] = str(user_details.user_type)

# 		return render(request, self.template_name, context)

# 	def post(self, request, user_id):
# 		user = get_object_or_404(get_user_model(), id=user_id)
# 		form = self.form_class(request.POST)
# 		user_type_details = Profile.objects.filter(user_id=self.kwargs['user_id']).first()
# 		user_type = user_type_details.user_type

# 		if form.is_valid():
# 			form.save()

# 			user_type_details = Profile.objects.filter(user_id=user_id).first()
# 			user_type = user_type_details.user_type

# 			update_session_auth_hash(request, user)
# 			messages.success(request, 'Your password was successfully updated!')
# 			return redirect(reverse('user_profile:all_users', kwargs={"usertype_slug": user_type}))

# 		messages.error(request, 'Please correct the error below.')
# 		context = {'form': form}

# 		redirect(reverse('user_profile:all_users', kwargs={"usertype_slug": user_type}))

@login_required
def profile_change_password(request, user_id):
	user = get_object_or_404(User, pk=user_id)
	user_type_details = Profile.objects.filter(user_id=user_id).first()
	if not user_type_details or not user_type_details.user_type:
		messages.error(request, "User profile type was not found.")
		return redirect(reverse('index'))

	user_type = user_type_details.user_type.name

	if request.method == 'POST':
		form = UserCustomPasswordChangeForm(user, request.POST)
		if form.is_valid():
			form.save()
			if request.user.pk == user.pk:
				update_session_auth_hash(request, user)
			messages.success(request, f"Password updated successfully for {user.username}.")
			return redirect(reverse('user_profile:all_users', kwargs={"usertype_slug": user_type}))
		for field, errors in form.errors.items():
			field_label = form.fields[field].label if field in form.fields else None
			for error in errors:
				if field_label:
					messages.error(request, f"{field_label}: {error}")
				else:
					messages.error(request, error)
	else:
		form = UserCustomPasswordChangeForm(user)

	context = {
		'form': form,
		'target_user': user,
		'user_type': user_type,
		'user_type_details': user_type_details,
		'user_id' : user_id,
		"current_url": True,
	}
	return CommonMixin.render(request, 'users_change_password.html', context)

# @csrf_protect
class LogoutView(APIView):
		"""Logout details view @vivek"""
		authentication_classes=(TokenAuthentication,)
		permission_classes=(IsAuthenticated,)

		def get(self,request,format=None):
			import datetime
			token= request.META.get('HTTP_AUTHORIZATION').replace('Token', '')
			print(token)
			LoginLogoutLoggedTable.objects.filter(user=request.user, token=token).update( \
            logout_time=datetime.datetime.now())
			request._auth.delete()
			# logout(request)
			return Response({'request_status': 1, 'msg': "Logout Success..."}, status=status.HTTP_200_OK)




def send_otp(mobile_number):
    """
    This is an helper function to send otp to session stored phones or 
    passed phone number as argument.
    """

    if mobile_number:
        
        key = otp_generator()
        mobile_number = str(mobile_number)
        otp_key = str(key)

        #link = f'https://2factor.in/API/R1/?module=TRANS_SMS&apikey=fc9e5177-b3e7-11e8-a895-0200cd936042&to={phone}&from=wisfrg&templatename=wisfrags&var1={otp_key}'
   
        #result = requests.get(link, verify=False)

        return otp_key
    else:
        return False
'''
Send otp to user
'''
class SendPhoneOTP(APIView):
	permission_classes =[AllowAny]	
	def post(self, request, format=None):
		username = request.data.get('username', None)
		try:
			with transaction.atomic(): 
				if username:
					user_details = None
					# Find the user profile based on the provided username
					if AggregatorProfile.cmobjects.filter(user__username=username).exists():
						user_details = AggregatorProfile.cmobjects.filter(user__username=username).first()
					elif GrowerProfile.cmobjects.filter(user__username=username).exists():
						user_details = GrowerProfile.cmobjects.filter(user__username=username).first()
					elif BlfProfile.cmobjects.filter(user__username=username).exists(): 
						user_details = BlfProfile.cmobjects.filter(user__username=username).first()
					else:
						return Response ({
						    'status': status.HTTP_404_NOT_FOUND,
						    'message': 'Username is not registered'
						}, status=status.HTTP_404_NOT_FOUND)
					# Check if the user profile has a mobile number
					if user_details is not None:
						mobile_number = user_details.mobile_number
						if mobile_number:
							# otp = send_otp(mobile_number)
							# if otp:
							# 	# Save the OTP to the user's profile in the database
							# 	user_details.otp = otp
							# 	user_details.otp_created_at = timezone.now() # Save OTP creation time
							# 	# ist_time = timezone.now().astimezone(timezone.pytz.timezone('Asia/Kolkata'))  # Convert to IST
							# 	# user_details.otp_created_at = ist_time
							# 	user_details.save()		
							# 	## send sms #######
							# 	# if mobile_number:
							# 	# 	template_id='1007983856203558873'
							# 	# 	message=f"Hi, Your one time password is:{otp}. Please don't share this with anyone - Trustea."
							# 	# 	print(message)
							# 	# 	send_sms(mobile_number, message, template_id)	
								return Response ({
								    'status': status.HTTP_200_OK,
								    # 'otp': otp,
								    'mobile_number': mobile_number,
									'username':user_details.user.username if user_details.user.username else '',
									'user_id':user_details.user.id if user_details.user else None,
									'user_type':user_details.profile_type.name if user_details.profile_type else "",
									'message': 'User found with mobile number.',
								})
							# else:
							# 	return Response ({
							# 	    'status': status.HTTP_400_BAD_REQUEST,
							# 	    'message': 'Failed to send OTP. Please try again.'
							# 	}, status=status.HTTP_400_BAD_REQUEST)
						else:
							
							return Response ({
							    'status': status.HTTP_200_OK,
								'mobile_number': "",
								'username':user_details.user.username if user_details.user.username else '',
								'user_id':user_details.user.id if user_details.user else None,
								'user_type':user_details.profile_type.name if user_details.profile_type else "",
								'message': 'Mobile number is not registered for the user.',
							}, status=status.HTTP_200_OK)
					else:
							return Response ({
							    'status': status.HTTP_404_NOT_FOUND,
							    'message': 'User details is not found for username.'
							}, status=status.HTTP_404_NOT_FOUND)		
				else:
					return Response ({
					    'status': status.HTTP_400_BAD_REQUEST,
					    'message': 'Username is required.'
					}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
		    return Response ({
		        'status': status.HTTP_400_BAD_REQUEST,
		        'message': f'Error: {str(e)}'
		    }, status=status.HTTP_400_BAD_REQUEST)	
		


# class SetNewPassWordAPIView(APIView):
# 	""" @vivek jaiswal
# 	Set a new password 
# 	"""
# 	# authentication_classes = (TokenAuthentication,)
# 	# permission_classes=(IsAuthenticated,)
# 	permission_classes = [AllowAny]
# 	serializer_class = SetNewPasswordSerializer

# 	def put(self, request):
# 		serializer = self.serializer_class(data=request.data)
# 		serializer.is_valid(raise_exception=True)	
# 		return Response({'msg': 'Password successfully reset.'}, status=status.HTTP_200_OK)
# class SetNewPassWordAPIView(APIView):
#     permission_classes = [AllowAny]
#     serializer_class = SetNewPasswordSerializer

#     def put(self, request):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         try:
#             user = serializer.save()  # Get the user instance from serializer
#             return Response({'msg': 'Password successfully reset.'}, status=status.HTTP_200_OK)
#         except AuthenticationFailed as e:
#             return Response({'msg': str(e.detail)}, status=e.status_code)


class ChangePasswordAPIView(APIView):
	""" Change Password API View"""
	authentication_classes = (TokenAuthentication,)
	permission_classes=(IsAuthenticated,)
	def put(self, request):
		serializer = ChangePasswordSerializer(data=request.data)
		user = request.user
		if serializer.is_valid():
			old_password = serializer.validated_data['old_password']
			new_password = serializer.validated_data['new_password']
			confirm_password = serializer.validated_data['confirm_password']
			if not user.check_password(old_password):		
				return Response({'msg': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
			if new_password != confirm_password	:	
				return Response({'msg': 'New password and Confirm Password do not match.'}, status=status.HTTP_400_BAD_REQUEST)
			user.set_password(new_password)
			user.save()
			return Response({'msg': 'Password successfully changed.'}, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	




from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import qrcode
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

class GenerateQRCodeView(APIView):
	def get(self, request):
		user_type = self.request.query_params.get('user_type', None)
		user_id = self.request.query_params.get('user_id', None)

		if not user_type or not user_id:
			return Response({
				'msg': "Both 'user_type' and 'user_id' are required.",
				'status': status.HTTP_400_BAD_REQUEST,
				'request_status': 0
			}, status=status.HTTP_400_BAD_REQUEST)

		try:
			qr_code_data = None
			if user_type.lower() == 'grower':
				qr_code = GrowerProfile.objects.filter(user_id=user_id).first()
				if qr_code:
					user_id = qr_code.user
					# qr_code_data = "Grower ID : " + str(qr_code.user) + "\n" + "Name : " + str(qr_code.name) + "\n" + "id : " + str(qr_code.id) + "\n" + "user_id: " + str(qr_code.user.id)
					qr_code_data = {
						'userid': qr_code.user.id,
						'name': qr_code.name,
						'id': qr_code.id,
						'username': qr_code.user.username
					}
			elif user_type.lower() == 'aggregator':
				qr_code = AggregatorProfile.objects.filter(user_id=user_id).first()
				if qr_code:
					user_id = qr_code.user
					# qr_code_data = "Aggregator ID : " + str(qr_code.user) + "\n" + "Name : " + str(qr_code.name) + "\n" + "id : " + str(qr_code.id) + "\n" + "user_id: " + str(qr_code.user.id)
					qr_code_data = {
						'userid': qr_code.user.id,
						'name': qr_code.name,
						'id': qr_code.id,
						'username': qr_code.user.username
					}
			elif user_type.lower() == 'blf':
				qr_code = BlfProfile.objects.filter(user_id=user_id).first()
				if qr_code:
					user_id = qr_code.user
					# qr_code_data = "BLF ID : " + str(qr_code.user) + "\n" + "Name : " + str(qr_code.entity_unit) + "\n" + "id : " + str(qr_code.id) + "\n" + "user_id: " + str(qr_code.user.id)
					qr_code_data = {
						'userid': qr_code.user.id,
						'name': qr_code.entity_unit,
						'id': qr_code.id,
						'username': qr_code.user.username
					}
			else:
				return Response({
					'msg': "Invalid user type. Please provide 'grower', 'aggregator', or 'blf'.",
					'status': status.HTTP_400_BAD_REQUEST,
					'request_status': 0
				}, status=status.HTTP_400_BAD_REQUEST)

			if qr_code_data is None:
				return Response({
					'msg': "No data found for the given user type and ID.",
					'status': status.HTTP_404_NOT_FOUND,
					'request_status': 0
				}, status=status.HTTP_404_NOT_FOUND)
			qr_code_data_json = json.dumps(qr_code_data)
			qr = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_L,
				box_size=10,
				border=4,
			)
			qr.add_data(qr_code_data_json)
			qr.make(fit=True)

			qr_code_image = qr.make_image(fill_color="black", back_color="white")

			buffer = BytesIO()

			# Create a PDF canvas
			pdf = canvas.Canvas(buffer, pagesize=letter)
			qr_width, qr_height = qr_code_image.size
			x_position = (letter[0] - qr_width) / 2
			y_position = (letter[1] - qr_height) / 2

			# Draw the QR code image onto the PDF canvas
			pdf.drawInlineImage(qr_code_image, x_position, y_position, width=qr_width, height=qr_height)
			
			pdf.save()

			buffer.seek(0)
			response = HttpResponse(buffer, content_type='application/pdf')
			response['Content-Disposition'] = 'attachment; filename="qrcode.pdf"'
			return response

		except Exception as e:
			return Response({
				'msg': f"Error generating QR code in PDF: {str(e)}",
				'status': status.HTTP_400_BAD_REQUEST,
				'request_status': 0
			}, status=status.HTTP_400_BAD_REQUEST)


