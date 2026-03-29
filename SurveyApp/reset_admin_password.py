from django.contrib.auth import get_user_model
User = get_user_model()
admin_users = User.objects.filter(is_superuser=True)
if admin_users.exists():
    admin = admin_users.first()
    admin.set_password('Admin123!')
    admin.save()
    print(f"PASS_RESET_SUCCESS: The password for superuser '{admin.username}' has been reset to 'Admin123!'")
else:
    print("NO_SUPERUSER_FOUND: Please create a superuser first.")
