# Generated migration for adding supervisor_feedback field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logbook', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='weeklylogbookentry',
            name='supervisor_feedback',
            field=models.TextField(blank=True, help_text='Supervisor feedback specific to this weekly entry'),
        ),
        migrations.AlterField(
            model_name='weeklylogbookentry',
            name='student_logbook',
            field=models.ForeignKey(
                help_text='The StudentLogbook that created this weekly entry',
                on_delete=models.deletion.CASCADE,
                related_name='weekly_entries',
                to='logbook.studentlogbook'
            ),
        ),
    ]
