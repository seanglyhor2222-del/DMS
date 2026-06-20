from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from config import settings
from django.conf import settings
import pyotp

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'roles'
    
    def __str__(self):
        return self.role_name

class UserSession(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.CharField(max_length=255)
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    # 2FA Fields
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    otp_enabled = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.username
    
    @property
    def is_manager(self):
        return self.role and self.role.role_name == 'manager'
    
    @property
    def is_admin_user(self):
        return self.is_superuser or (self.role and self.role.role_name == 'admin')
    
    def get_otp_uri(self):
        """Generate OTP URI for QR code"""
        if not self.otp_secret:
            self.otp_secret = pyotp.random_base32()
            self.save()
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.email or self.username,
            issuer_name="DMS System"
        )
    
    def verify_otp(self, code):
        """Verify OTP code"""
        if not self.otp_secret:
            return False
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(code)
    
    def enable_2fa(self):
        """Enable 2FA for user"""
        if not self.otp_secret:
            self.otp_secret = pyotp.random_base32()
        self.otp_enabled = True
        self.save()
    
    def disable_2fa(self):
        """Disable 2FA for user"""
        self.otp_enabled = False
        self.save()
