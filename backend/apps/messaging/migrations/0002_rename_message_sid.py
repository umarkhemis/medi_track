# Generated migration: rename twilio_sid to message_sid

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='twilio_sid',
            new_name='message_sid',
        ),
    ]
