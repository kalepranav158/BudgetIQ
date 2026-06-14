"""Migration to add active learning and retraining cycle models."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_app', '0010_reparsejob'),
    ]

    operations = [
        migrations.CreateModel(
            name='LowConfidenceFlagRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_category', models.CharField(max_length=32)),
                ('original_confidence', models.FloatField()),
                ('confidence_threshold', models.FloatField(default=0.6)),
                ('status', models.CharField(choices=[('flagged', 'Flagged'), ('reviewed', 'Reviewed'), ('corrected', 'Corrected')], default='flagged', max_length=10)),
                ('corrected_category', models.CharField(blank=True, default='', max_length=32)),
                ('human_review_notes', models.TextField(blank=True, default='')),
                ('flagged_at', models.DateTimeField(auto_now_add=True)),
                ('corrected_at', models.DateTimeField(blank=True, null=True)),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='low_confidence_flag', to='django_app.transaction')),
            ],
            options={
                'db_table': 'low_confidence_flag_record',
            },
        ),
        migrations.CreateModel(
            name='RetrainingCycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cycle_id', models.CharField(db_index=True, max_length=64, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('trigger_reason', models.CharField(max_length=255)),
                ('corrections_count', models.IntegerField(default=0)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('new_model_metrics', models.JSONField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'retraining_cycle',
            },
        ),
        migrations.AddIndex(
            model_name='retrainingcycle',
            index=models.Index(fields=['status'], name='retraining_cycle_status_idx'),
        ),
        migrations.AddIndex(
            model_name='retrainingcycle',
            index=models.Index(fields=['created_at'], name='retraining_cycle_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='lowconfidenceflagrecord',
            index=models.Index(fields=['status'], name='low_conf_status_idx'),
        ),
        migrations.AddIndex(
            model_name='lowconfidenceflagrecord',
            index=models.Index(fields=['flagged_at'], name='low_conf_flagged_at_idx'),
        ),
        migrations.AddIndex(
            model_name='lowconfidenceflagrecord',
            index=models.Index(fields=['original_confidence'], name='low_conf_confidence_idx'),
        ),
    ]
