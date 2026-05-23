from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0005_passwordresettoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='builderrun',
            name='ai_analysis_json',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='builderrun',
            name='final_plan_json',
            field=models.TextField(blank=True, default=''),
        ),
    ]
