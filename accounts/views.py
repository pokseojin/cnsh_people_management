### --------
# secrets.json 읽어오기

from pathlib import Path
import os, json
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
secret_file = os.path.join(BASE_DIR, "secrets.json")

with open(secret_file) as f:
    secrets = json.loads(f.read())

def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)

GOOGLE_SCOPE_USERINFO = get_secret("GOOGLE_SCOPE_USERINFO")
GOOGLE_REDIRECT = get_secret("GOOGLE_REDIRECT")
GOOGLE_CALLBACK_URI = get_secret("GOOGLE_CALLBACK_URI")
GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID")
GOOGLE_SECRET = get_secret("GOOGLE_SECRET")

### --------

from django.shortcuts import redirect
from json import JSONDecodeError
from django.http import JsonResponse
from allauth.socialaccount.models import SocialAccount
import requests

#로그인이 되지 않은 사용자가 접근 시

# 로그인 페이지 연결
def google_login(request):
   scope = GOOGLE_SCOPE_USERINFO        # + "https://www.googleapis.com/auth/drive.readonly" 등 scope 설정 후 자율적으로 추가
   return redirect(f"{GOOGLE_REDIRECT}?client_id={GOOGLE_CLIENT_ID}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}")

# 인가 코드를 받아 로그인 처리
def google_callback(request):
    code = request.GET.get("code")      # Query String 으로 넘어옴
    
    token_req = requests.post(f"https://oauth2.googleapis.com/token?client_id={GOOGLE_CLIENT_ID}&client_secret={GOOGLE_SECRET}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}")
    token_req_json = token_req.json()
    error = token_req_json.get("error")

    if error is not None:
        raise JSONDecodeError(error)

    google_access_token = token_req_json.get('access_token')

    email_response = requests.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={google_access_token}")
    res_status = email_response.status_code

    if res_status != 200:
        return JsonResponse({"status": 400,"message": "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)
    
    email_res_json = email_response.json()
    email = email_res_json.get('email')

    from django.contrib.auth.models import User # User를 데려옵니다 (또는 get_user_model() 사용)
    from django.http import JsonResponse        # JsonResponse를 데려옵니다
    from rest_framework import status           # status(HTTP 상태 코드)를 데려옵니다
    from allauth.socialaccount.models import SocialAccount # SocialAccount를 데려옵니다
    from rest_framework_simplejwt.tokens import RefreshToken # RefreshToken을 데려옵니다
    from django.contrib.auth import login

    try:
        user = User.objects.get(email=email)

        if user is None:
            return JsonResponse({"status": 404,"message": "User Account Not Exists"}, status=status.HTTP_404_NOT_FOUND) 
		
        # 소셜로그인 계정 유무 확인
        social_user = SocialAccount.objects.get(user=user)  
        if social_user.provider != "google":
            return JsonResponse({"status": 400,"message": "User Account Not Exists"}, status=status.HTTP_400_BAD_REQUEST) 
            
        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)
		
        response = redirect('/cnsh_map')
        login(request, user)
        res = JsonResponse(
                {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                    },
                    "message": "login success",
                    "token": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )
        return response
        
    except User.DoesNotExist:
        response = redirect('/cnsh_map')

        # 1. 우리 DB에 새로운 유저를 만들어줍니다 (회원가입)
        user = User.objects.create_user(
            email=email, 
            username=email.split('@')[0], # 이메일 앞부분을 임시 아이디로 사용
            password=None # 소셜 로그인이니 비밀번호는 비워둡니다
        )
        
        # 2. 이 유저가 '구글'로 가입했다는 꼬리표(SocialAccount)도 달아줍니다
        SocialAccount.objects.create(
            user=user,
            provider="google",
            uid=email # 구글에서 받아온 고유 ID를 넣는 것이 가장 좋습니다
        )
        
        # 3. 가입을 시켰으니 곧바로 로그인 인증 토큰을 발급해 줍니다
        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)
        
        response = redirect('/cnsh_map')
        res = JsonResponse({
            "message": "Signup and Login success!",
            "user": {"id": user.id, "email": user.email},
            "token": {"access_token": access_token, "refresh_token": refresh_token}
        }, status=status.HTTP_201_CREATED)
        login(request, user)
        return response
    
    except Exception as e: 
        # 그 외에 예상치 못한 에러가 났을 때의 처리
        return JsonResponse({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)