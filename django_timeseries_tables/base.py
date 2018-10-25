from copy import copy

from django.db import models
from django.db.models.base import ModelBase

from django_timeseries_tables.internal_models import SubTableModel, TimeSeriesMaterializedView


class ModelViewBase(ModelBase):

    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__

        # Create the class.
        module = attrs.get('__module__')
        new_attrs = {'__module__': module}
        classcell = attrs.get('__classcell__', None)
        attr_meta = attrs.pop('Meta', None)
        abstract = getattr(attr_meta, 'abstract', False)

        if classcell is not None:
            new_attrs['__classcell__'] = classcell

        subtable_attr_base = new_attrs.copy()

        if abstract:
            new_attrs['Meta'] = attr_meta

        for obj_name, obj in attrs.items():
            keep_on_master_model = hasattr(obj, 'keep_on_master_model') and obj.keep_on_master_model
            if keep_on_master_model:
                new_attrs[obj_name] = obj

        if not abstract:
            master_model = super_new(cls, name + 'Historical', bases, new_attrs, **kwargs)
        else:
            master_model = super_new(cls, name, bases, new_attrs, **kwargs)

        submodels = []
        submodels_on_master_model = {}
        fields = {}

        for obj_name, obj in attrs.items():

            ctc = hasattr(obj, 'contribute_to_class')
            keep_on_master_model = hasattr(obj, 'keep_on_master_model') and obj.keep_on_master_model

            if ctc:
                fields[obj_name] = copy(obj)

            if keep_on_master_model:
                pass
            elif ctc:
                table_model, foreign_key_name = cls.create_table_from_field(obj_name, obj, master_model,
                                                                            subtable_attr_base)
                submodels.append((obj_name, table_model, foreign_key_name))
                submodels_on_master_model[obj_name] = table_model

        if not abstract:
            view = cls.create_materialized_view(name, master_model, submodels, subtable_attr_base, fields)
            setattr(view, 'historical_model', master_model)
            setattr(view, 'submodels', submodels_on_master_model)
            return view

        return master_model

    @classmethod
    def create_table_from_field(cls, field_name, field, master_model, subtable_attr_base):
        table_name = master_model.__name__ + '_' + field_name
        foreign_key_name = master_model.__name__.lower()

        subtable_attr = subtable_attr_base.copy()

        subtable_attr['value'] = field
        subtable_attr[foreign_key_name] = models.ForeignKey(master_model, on_delete=models.CASCADE)
        subtable_attr['Meta'] = type('Meta', (object,), {
            'unique_together': ('modified', foreign_key_name)
        })

        table_model = ModelBase.__new__(cls, table_name, (SubTableModel,), subtable_attr)
        setattr(table_model, 'foreign_key_name', foreign_key_name)
        return table_model, foreign_key_name

    @classmethod
    def create_materialized_view(cls, original_name, master_model: models.Model, submodels, subtable_attr_base, fields):

        def create_subquery(st, foreign_key):
            v_name = 'value'
            if hasattr(st, 'value_id'):
                v_name = 'value_id'
            return f"SELECT {v_name}, id, {st._meta.db_table}.{foreign_key}_id FROM {st._meta.db_table} JOIN (SELECT {foreign_key}_id, MAX(modified) AS MAX FROM {st._meta.db_table} GROUP BY {foreign_key}_id) z ON {st._meta.db_table}.modified = z.max"

        fields_to_join = []
        tables_to_join = []
        for field_name, st, foreign_key in submodels:
            tables_to_join.append(
                f'LEFT JOIN ({create_subquery(st, foreign_key)}) AS {st._meta.db_table} ON o.id = {st._meta.db_table}.{foreign_key}_id')
            if hasattr(st, 'value_id'):
                # It's a foreign key, switch up the tactic
                fields_to_join.append(f'{st._meta.db_table}.value_id AS {field_name}_id')
            else:
                fields_to_join.append(f'{st._meta.db_table}.value AS {field_name}')

        join_string = '\n'.join(tables_to_join)

        view_attrs = subtable_attr_base.copy()
        field_string = ', '.join(fields_to_join) if submodels else None
        select_items = filter(None, ['CURRENT_TIME AS last_refresh', 'o.*', field_string])
        view_attrs['sql'] = f"SELECT {', '.join(select_items)} FROM {master_model._meta.db_table} o {join_string}"

        view_attrs['concurrent_index'] = 'id'
        view_attrs['last_refresh'] = models.DateTimeField()
        for field_name, field_def in fields.items():
            field_def.name = field_name
            view_attrs[field_name] = field_def

        print(view_attrs['sql'])
        return type(original_name, (TimeSeriesMaterializedView,), view_attrs)
