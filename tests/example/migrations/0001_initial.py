# Generated by Django 4.2.4 on 2023-08-15 19:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Apartment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("completion_date", models.DateField(null=True)),
                ("street_address", models.CharField(max_length=200)),
                ("stair", models.CharField(max_length=16)),
                ("floor", models.IntegerField(null=True)),
                ("apartment_number", models.PositiveIntegerField()),
                ("shares_start", models.PositiveIntegerField(null=True)),
                ("shares_end", models.PositiveIntegerField(null=True)),
                ("surface_area", models.DecimalField(decimal_places=2, max_digits=9, null=True)),
                ("rooms", models.PositiveIntegerField(null=True)),
            ],
            options={
                "verbose_name": "Apartment",
                "verbose_name_plural": "Apartments",
                "ordering": ["street_address", "stair", "-apartment_number"],
            },
        ),
        migrations.CreateModel(
            name="Building",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("street_address", models.CharField(max_length=200)),
            ],
            options={
                "verbose_name": "Building",
                "verbose_name_plural": "Buildings",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Developer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Developer",
                "verbose_name_plural": "Developers",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="HousingCompany",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("street_address", models.CharField(max_length=200)),
                ("city", models.CharField(max_length=200)),
            ],
            options={
                "verbose_name": "Housing company",
                "verbose_name_plural": "Housing companies",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Owner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=256)),
                ("identifier", models.CharField(blank=True, max_length=11, null=True)),
                ("email", models.EmailField(blank=True, max_length=200, null=True)),
                ("phone", models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                "verbose_name": "Owner",
                "verbose_name_plural": "Owners",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Sale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purchase_date", models.DateField(editable=False)),
                ("purchase_price", models.DecimalField(decimal_places=2, editable=False, max_digits=12)),
                (
                    "apartment",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sales",
                        to="example.apartment",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sale",
                "verbose_name_plural": "Sales",
                "ordering": ["-purchase_date"],
            },
        ),
        migrations.CreateModel(
            name="RealEstate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("surface_area", models.DecimalField(decimal_places=2, max_digits=9, null=True)),
                (
                    "housing_company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="real_estates",
                        to="example.housingcompany",
                    ),
                ),
            ],
            options={
                "verbose_name": "Real estate",
                "verbose_name_plural": "Real estates",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="PropertyManager",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=1024)),
                ("email", models.EmailField(blank=True, max_length=254)),
            ],
            options={
                "verbose_name": "Property manager",
                "verbose_name_plural": "Property managers",
                "ordering": ["name"],
                "indexes": [models.Index(fields=["name"], name="example_pro_name_33b8c8_idx")],
            },
        ),
        migrations.CreateModel(
            name="PostalCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=5, unique=True)),
            ],
            options={
                "verbose_name": "Postal code",
                "verbose_name_plural": "Postal codes",
                "ordering": ["code"],
                "indexes": [models.Index(fields=["code"], name="example_pos_code_11411c_idx")],
            },
        ),
        migrations.CreateModel(
            name="Ownership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("percentage", models.DecimalField(decimal_places=0, editable=False, max_digits=3)),
                (
                    "owner",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ownerships",
                        to="example.owner",
                    ),
                ),
                (
                    "sale",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ownerships",
                        to="example.sale",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ownership",
                "verbose_name_plural": "Ownership",
            },
        ),
        migrations.AddIndex(
            model_name="owner",
            index=models.Index(fields=["name"], name="example_own_name_ae4a28_idx"),
        ),
        migrations.AddField(
            model_name="housingcompany",
            name="developers",
            field=models.ManyToManyField(related_name="housing_companies", to="example.developer"),
        ),
        migrations.AddField(
            model_name="housingcompany",
            name="postal_code",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="housing_companies",
                to="example.postalcode",
            ),
        ),
        migrations.AddField(
            model_name="housingcompany",
            name="property_manager",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="housing_companies",
                to="example.propertymanager",
            ),
        ),
        migrations.AddIndex(
            model_name="developer",
            index=models.Index(fields=["name"], name="example_dev_name_70c267_idx"),
        ),
        migrations.AddField(
            model_name="building",
            name="real_estate",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="buildings",
                to="example.realestate",
            ),
        ),
        migrations.AddField(
            model_name="apartment",
            name="building",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="apartments",
                to="example.building",
            ),
        ),
        migrations.AddIndex(
            model_name="sale",
            index=models.Index(fields=["-purchase_date"], name="example_sal_purchas_3a6659_idx"),
        ),
        migrations.AddIndex(
            model_name="realestate",
            index=models.Index(fields=["name"], name="example_rea_name_165404_idx"),
        ),
        migrations.AddIndex(
            model_name="housingcompany",
            index=models.Index(fields=["name"], name="example_hou_name_33e5dd_idx"),
        ),
        migrations.AddIndex(
            model_name="building",
            index=models.Index(fields=["name"], name="example_bui_name_f06b41_idx"),
        ),
        migrations.AddIndex(
            model_name="apartment",
            index=models.Index(
                fields=["street_address", "stair", "-apartment_number"],
                name="example_apa_street__b3d673_idx",
            ),
        ),
    ]