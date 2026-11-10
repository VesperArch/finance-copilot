from django.db import migrations


def migrate_owners(apps, schema_editor):
    Space = apps.get_model("finance", "FinancialSpace")
    Membership = apps.get_model("accounts", "Membership")
    alias = schema_editor.connection.alias
    for space in Space.objects.using(alias).order_by("pk").iterator():
        Membership.objects.using(alias).get_or_create(
            financial_space_id=space.pk, user_id=space.owner_id, defaults={"role": "ADMIN"},
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    # Reversing the data step preserves memberships; schema rollback is separate.
    operations = [migrations.RunPython(migrate_owners, migrations.RunPython.noop)]
