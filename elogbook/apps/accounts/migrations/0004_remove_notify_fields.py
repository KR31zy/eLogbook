# Generated manually to remove notify fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_notify_email_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='notify_email',
        ),
        migrations.RemoveField(
            model_name='user',
            name='notify_sms',
        ),
    ]
