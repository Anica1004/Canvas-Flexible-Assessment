# Generated by Django 4.0.4 on 2022-05-12 17:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('user_id', models.IntegerField(primary_key=True, serialize=False)),
                ('login_id', models.CharField(max_length=100)),
                ('display_name', models.CharField(max_length=255)),
                ('role', models.IntegerField(choices=[(1, 'Admin'), (2, 'Teacher'), (3, 'Ta'), (4, 'Student')])),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('default', models.FloatField()),
                ('max', models.FloatField()),
                ('min', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('availability', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flex.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FlexAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flex', models.FloatField()),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flex.assessment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AssessmentCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flex.assessment')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flex.course')),
            ],
        ),
        migrations.AddConstraint(
            model_name='usercourse',
            constraint=models.UniqueConstraint(fields=('user_id', 'course_id'), name='User and Course unique'),
        ),
        migrations.AddConstraint(
            model_name='assessmentcourse',
            constraint=models.UniqueConstraint(fields=('assessment_id', 'course_id'), name='Assessment and Course unique'),
        ),
    ]
