from django.db import models


class NoReverseRelationship(models.ManyToOneRel):
    def __init__(self, *args, **kwargs):
        new_kwargs = kwargs.copy()
        new_kwargs['related_name'] = '+'  # Prevent reverse relationships
        super().__init__(*args, **new_kwargs)


class ForeignKey(models.ForeignKey):
    rel_class = NoReverseRelationship

    def __init__(self, to, on_delete, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None,
                 db_constraint=True, **kwargs):
        if hasattr(to, 'historical_model'):
            to = to.historical_model

        super().__init__(to, on_delete, related_name=related_name, related_query_name=related_query_name,
                         limit_choices_to=limit_choices_to, parent_link=parent_link, to_field=to_field,
                         db_constraint=db_constraint, **kwargs)


def NormalField(field):
    setattr(field, 'keep_on_master_model', True)
    return field
