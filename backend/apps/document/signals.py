from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Document


@receiver(post_delete, sender=Document)
def delete_files_on_record_delete(sender, instance, **kwargs):
    """When a Document is deleted, also delete its files from MinIO."""
    if instance.file:
        instance.file.delete(save=False)
    if instance.image:
        instance.image.delete(save=False)


@receiver(pre_save, sender=Document)
def delete_old_file_on_change(sender, instance, **kwargs):
    """When a file is replaced, delete the old one from MinIO."""
    if not instance.pk:
        return 

    try:
        old = Document.objects.get(pk=instance.pk)
    except Document.DoesNotExist:
        return

    if old.file and old.file != instance.file:
        old.file.delete(save=False)

    if old.image and old.image != instance.image:
        old.image.delete(save=False)