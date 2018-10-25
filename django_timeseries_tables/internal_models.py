from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django_pgviews import view as pg
from model_utils.models import TimeStampedModel

from django_timeseries_tables.query_set import TimeSeriesViewManager


class TimeSeriesMaterializedView(pg.MaterializedView):
    """Read-only version of the materialized view
    """
    _base_manager = TimeSeriesViewManager()
    objects = TimeSeriesViewManager()
    submodels = {}

    @classmethod
    def get_or_build_from_db(cls, pk):
        try:
            return cls.objects.get(pk=pk)
        except Exception:
            h = cls.historical_model.objects.get(pk=pk)
            obj = cls(id=pk)
            for field_name, sub_table in cls.submodels.items():
                most_recent = sub_table.get_most_recent(pk)
                if most_recent:
                    setattr(obj, field_name, most_recent.value)

            for field in h._meta.local_fields:
                setattr(obj, field.name, getattr(h, field.name))
            return obj

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        h = self.historical_version
        h.save()  # We need an ID
        for field in self._meta.local_fields:
            submodel = self.__class__.submodels.get(field.name)
            if hasattr(field, 'keep_on_master_model') and field.keep_on_master_model:
                setattr(h, field.name, getattr(self, field.name))
            elif submodel:
                kwargs = {
                    'value': getattr(self, field.name),
                    submodel.foreign_key_name + '_id': h.id
                }
                try:
                    submodel(**kwargs).save()
                except IntegrityError as e:
                    if 'null value in column "value" violates not-null constraint' in e.args[0]:
                        raise IntegrityError(f'null value in column "{field.name}" violates not-null constraint') from e
                    else:
                        raise e

        return h.save()

    @property
    def historical_version(self):
        if hasattr(self, 'historical_model'):
            return self.historical_model.objects.get(pk=self.pk)
        else:
            return self.__class__.objects.get(pk=self.pk)

    class Meta(pg.BaseManagerMeta):
        abstract = True
        managed = False


class SubTableModel(TimeStampedModel):

    @classmethod
    def get_most_recent(cls, foreign_id):
        filter_kwarg = {cls.foreign_key_name: foreign_id}
        return cls.objects.filter(**filter_kwarg).order_by('-modified').first()

    def validate_unique(self, exclude=None):
        try:
            super(SubTableModel, self).validate_unique()
        except ValidationError as e:
            self.modified = None
            return super(SubTableModel, self).validate_unique()

    class Meta:
        abstract = True