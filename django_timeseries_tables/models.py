from model_utils.models import TimeStampedModel
from django_timeseries_tables.base import ModelViewBase


class TimeSeriesModel(TimeStampedModel, metaclass=ModelViewBase):
    class Meta:
        abstract = True