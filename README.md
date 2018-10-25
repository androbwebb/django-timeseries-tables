# django-timeseries-tables

![https://travis-ci.org/androbwebb/django-timeseries-tables](https://travis-ci.org/androbwebb/django-timeseries-tables.svg?branch=master)
![https://codecov.io/gh/androbwebb/django-timeseries-tables](https://codecov.io/gh/androbwebb/django-timeseries-tables/branch/master/graph/badge.svg)
![https://pypi.python.org/pypi/django-timeseries-tables](https://img.shields.io/pypi/v/django-timeseries-tables.svg)

### Django model mixins and utilities.

`django-timeseries-tables` supports `Django`_ 1.8 to 2.1.

Django: http://www.djangoproject.com/

This app is available on `PyPI`.

PyPI: https://pypi.python.org/pypi/django-timeseries-tables/

## Getting Help

Documentation for django-timeseries-tables is available
https://django-timeseries-tables.readthedocs.io/

## Brief Overview
Let's say you want to qualify companies to see if they'd make good clients for your SaaS business.

Normally when you create django models, you would write something like this:

```python
from django.db import models
class Company(models.Model):
    name = models.TextField()
    revenue = models.FloatField()
    phone_number = models.TextField()
    number_of_employees = models.IntegerField(null=True)
    is_qualified = models.BooleanField(default=True)
 ```
 
And wind up with a single table `company` with 6 columns (id, phone_number, name, revenue, number_of_employees, is_qualified).
 
But what if you want to the value of all those fields over all of time for your data/eng teams, but still provide a `Company` table for your business team to query against?
 
You'd have to write separate models for all the columns you want to track, and then either a (possibly materlized) view or a real Company model that you would update periodically. 
 
 That's exactly what this package does for you:
 
 ```python
from django_timeseries_tables import TimeSeriesModel, NormalField, ForeignKey
from django.db import models


class TimeSeriesCompany(TimeSeriesModel):
    name = models.TextField()
    revenue = models.FloatField()
    number_of_employees = models.IntegerField(null=True)
  
    phone_number = NormalField(models.TextField())
    is_qualified = NormalField(models.BooleanField(default=True))
 ```
 
This will create 4 tables and a materialized view. You'll have access to the full history of `name`, `revenue` and `number_of_employees` in their own tables: `timeseriescompany_name`, `timeseriescompany_revenue`, `timeseriescompany_number_of_employees`, respectively. It will also create a `timeseriescompany_historical` table that will hold an ID as well as any fields that are wrapped with `NormalField`. Finally, it creates a ready-only materialized view `timeseriescompany`, that can be used to access the data. (To update the view, call `TimeSeriesCompany.refresh()`)

## Contributing

Please file bugs and send pull requests to the `GitHub repository`_ and `issue
tracker`_. See `CONTRIBUTING.rst`_ for details.

[GitHub repository](https://github.com/androbwebb/django-timeseries-tables/)

[Issue Tracker](https://github.com/androbwebb/django-timeseries-tables/issues)

[Contributing](https://github.com/androbwebb/django-timeseries-tables/blob/master/CONTRIBUTING.rst)
