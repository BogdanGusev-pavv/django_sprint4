from django.db import models


class PublishedModel(models.Model):
    """Абстрактная модель. Добавляет флаг is_published."""

    is_published = models.BooleanField('Опубликовано',
                                       default=True,
                                       help_text="Снимите галочку, "
                                       "чтобы скрыть публикацию.")

    class Meta:
        abstract = True


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет флаг is_published."""

    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True
