from django.db import models
from django.db.utils import IntegrityError
from django_pgviews import view as pg


class TimeSeriesQuerySet(pg.ReadOnlyViewQuerySet):

    def update(self, **kwargs):
        raise NotImplementedError("TODO")

    def _update(self, values):
        count = 0
        for obj in self:
            h = obj.historical_version
            h.save()  # We need an ID
            for f, _, val in values:
                if hasattr(f, 'keep_on_master_model') and f.keep_on_master_model:
                    print('keep_on_master_model', f.name)
                    setattr(h, f.name, val)
                else:
                    submodel = self.model.submodels.get(f.name)
                    kwargs = {
                        'value': val,
                        submodel.foreign_key_name + '_id': h.id
                    }
                    try:
                        submodel(**kwargs).save()
                    except IntegrityError as e:
                        if 'null value in column "value" violates not-null constraint' in e.args[0]:
                            raise IntegrityError(f'null value in column "{f.name}" violates not-null constraint')
                        else:
                            raise e

            h.save()
            count += 1
        return count

    def create(self, **kwargs):
        historical_kwargs = {}
        other_kwargs = {}

        for field, val in kwargs.items():
            if self.model.submodels.get(field):
                other_kwargs[field] = val
            else:
                historical_kwargs[field] = val

        h = self.model.historical_model(**historical_kwargs)
        h.save()

        for field, val in other_kwargs.items():
            submodel = self.model.submodels.get(field)
            ks = {
                'value': val,
                submodel.foreign_key_name + '_id': h.id
            }
            try:
                submodel(**ks).save()
            except IntegrityError as e:
                if 'null value in column "value" violates not-null constraint' in e.args[0]:
                    raise IntegrityError(f'null value in column "{field}" violates not-null constraint') from e
                else:
                    raise e from e

        return self.model.get_or_build_from_db(h.pk)

    def update_or_create(self, defaults=None, **kwargs):
        raise NotImplementedError("TODO")

    def bulk_create(self, objs, batch_size=None):
        raise NotImplementedError("TODO")


class TimeSeriesViewManager(models.Manager):
    def get_queryset(self):
        return TimeSeriesQuerySet(self.model, using=self._db)
