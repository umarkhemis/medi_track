# Generated migration: add question_keys to DailyCheckIn

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkins', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailycheckin',
            name='question_keys',
            field=models.JSONField(
                default=list,
                blank=True,
                help_text=(
                    'Ordered list of question keys expected for this check-in, '
                    'populated when the check-in message is sent.'
                ),
            ),
        ),
    ]
