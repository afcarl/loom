import copy
from django.apps import AppConfig
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rest_framework import serializers


POLYMORPHIC_TYPE_FIELD = 'polymorphic_ctype'

def _get_class_from_string(kls):

    try:
        if issubclass(kls, serializers.Serializer):
            return kls
    except TypeError:
        pass

    # Get class from string
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

class NestedPolymorphicModelSerializer(serializers.ModelSerializer):

    """This class supplements the features of django-rest-framework
    and django-polymorphic to handle serialization/deserialization of
    nested models with polymorphic (multitable inheritance) relationships.
    It implements the following features:
      1. Extend DRF serializers to support creation and update with nested models
      2. When creating a model from serialized data, select the best subclass model 
         to use in a polymorphic relationship. Selection is based on whether model 
         fields match keys in input data. You can also explicitly select the class
         using the "_class" field in the data to be deserialized.
    """

    def to_representation(self, instance):
        if isinstance(instance, models.Model):
            serializer = self._select_subclass_serializer_by_model_instance(instance)
            if serializer == self:
                repr = super(NestedPolymorphicModelSerializer, serializer).to_representation(instance)
                repr.update({'_class': self.Meta.model.__name__})
            else:
                # Recurse until we reach the lowest subclass
                repr = serializer.to_representation(instance)
                repr.update({'_class': self.Meta.model.__name__})
        else:
            # If the Serializer was instantiated from data with no model,
            # "instance" is an OrderedDict, not a Model
            repr = super(NestedPolymorphicModelSerializer, self).to_representation(instance)
            repr.update({'_class': self.Meta.model.__name__})

        return repr

    def create(self, validated_data):

        # Instead of using "self" to serialize, see if we should use the serializer for
        # a subclass of the current model instead.
        # If not, this call returns "self" as "serializer", meaning the current model is
        # the best match.
        #
        serializer = self._select_subclass_serializer_by_data(self.initial_data)

        if serializer is self:
            # No need to use subclass, proceed with serialization

            # First create child instances, to be added to the model when it is created
            data_with_children = self._create_x_to_one_children(validated_data)

            # Create model, minus X2Many relationships since these
            # have to be added after the model is saved
            #
            # Don't worry, x_to_many data is still in initial_data and we'll
            # validate it on the child models
            #
            self._strip_x_to_many_data(data_with_children)
            self._strip_reverse_x_to_one_data(data_with_children)

            # Create model
            instance = self.Meta.model.objects.create(**data_with_children)

            # Now add X2Many and reverse X2One to existing model
            instance = self._create_x_to_many_children(instance)
            instance = self._create_reverse_x_to_one_children(instance)

        else:
            # A subclass model matches the data better than the current model.
            # Defer deserialization to the serializer of the subclass.
            #
            if not serializer.is_valid():
                raise Exception("Invalid data for model %s. Errors: %s" %
                                (serializer.Meta.model.__name__, serializer.errors))

            # Calling "save" will trigger the "create" method on the new serializer
            instance = serializer.save()

        instance.send_post_create()
        return instance
            

    def _strip_x_to_many_data(self, data):

        if hasattr(self.Meta, 'nested_x_to_many_serializers'):

            for field_name, ChildSerializer in self.Meta.nested_x_to_many_serializers.iteritems():
                try:
                    data.pop(field_name)
                except KeyError:
                    pass

    def _strip_reverse_x_to_one_data(self, data):

        if hasattr(self.Meta, 'nested_reverse_x_to_one_serializers'):

            for field_name, ChildSerializer in self.Meta.nested_reverse_x_to_one_serializers.iteritems():
                try:
                    data.pop(field_name)
                except KeyError:
                    pass

    def _create_x_to_one_children(self, data):

        data_with_children = data
        
        # For models with nested children, handle that serialization here:
        if hasattr(self.Meta, 'nested_x_to_one_serializers'):

            for field_name, ChildSerializer in self.Meta.nested_x_to_one_serializers.iteritems():
                ChildSerializer = _get_class_from_string(ChildSerializer)
                data = self.initial_data.get(field_name)

                if data:
                    child_serializer = ChildSerializer(data=data)
                    child_serializer.is_valid()
                    model = child_serializer.save()

                    # Replace raw data for child with model instance
                    data_with_children[field_name] = model

        return data_with_children

    def _create_x_to_many_children(self, model):

        if hasattr(self.Meta, 'nested_x_to_many_serializers'):

            for field_name, ChildSerializer in self.Meta.nested_x_to_many_serializers.iteritems():
                ChildSerializer = _get_class_from_string(ChildSerializer)

                if self.initial_data.get(field_name):
                    for data in self.initial_data.get(field_name):
                        child_serializer = ChildSerializer(data=data)
                        child_serializer.is_valid()
                        child = child_serializer.save()
                        getattr(model, field_name).add(child)

        return model

    def _get_related_field_name(self, field_name):
        return getattr(self.Meta.model, field_name).related.field.name
        
    def _create_reverse_x_to_one_children(self, model):

        if hasattr(self.Meta, 'nested_reverse_x_to_one_serializers'):

            for field_name, ChildSerializer in self.Meta.nested_reverse_x_to_one_serializers.iteritems():
                ChildSerializer = _get_class_from_string(ChildSerializer)

                child_serializer = ChildSerializer(data=self.initial_data.get(field_name))
                child_serializer.is_valid()
                child = child_serializer.save()
                setattr(model, field_name, child)
                child.save()

        return model

    def _select_subclass_serializer_by_data(self, data):

        """For a given set of data to be deserialized, and for the model class associated with
        the current serializer (self), determine whether this model or one of its subclass
        models is the best match for the data, and return the serializer associated with
        the matching model class
        """

        # If not polymorphic, keep the current model
        if not hasattr(self.Meta, 'subclass_serializers'):
            return self

        # Check if the model class is given explicitly in the data
        _class = data.get('_class')
        if _class is not None:

            if self.Meta.model.__name__ == _class:
                # Current model matches the class specified
                return self
            else:
                # Look for matches in the subclasses
                matching_serializers = filter(lambda s: s.Meta.model.__name__==_class, self.Meta.subclass_serializers.values())

        # Class is not explicitly specified, so we try to infer it from the data.

        # If all keys in the data match fields on the current model class, keep the current class.
        elif self._do_all_fields_match(self.Meta.model, data.keys()):
            return self

        # Otherwise select subclass model classes whose fields match all keys in the data
        else:
            matching_serializers = []
            for SubclassSerializer in self.Meta.subclass_serializers.values():
                SubclassSerializer = _get_class_from_string(SubclassSerializer)
                if self._do_all_fields_match(SubclassSerializer.Meta.model, data.keys()):
                    matching_serializers.append(SubclassSerializer)

        # Verify just one match.
        if len(matching_serializers) == 0:
            raise Exception("Neither model %s nor its subclasses match the data given: %s"
                            % (self.Meta.model.__name__, data))
        elif len(matching_serializers) > 1:
            raise Exception("Multiple subclasses (%s) of model %s match the input data: %s"
                            % (','.join([s.Meta.model.__name__ for s in matching_serializers]),
                               self.Meta.model.__name__, data))

        # Since we found a better matching subclass model class, substitute its serializer for the current one
        SubclassSerializer = matching_serializers[0]

        return SubclassSerializer(data=data, context=self.context)

    def _do_all_fields_match(self, model, fields):

        # All values in 'fields' can be found as fields on the model class
        return set(fields).issubset(set(model._meta.get_all_field_names()))

    def update(self, instance, validated_data):

        # Instead of using "self" to serialize, see if we should use the serializer for
        # a subclass of the current model class
        # If not, this call returns "self" as "serializer", meaning the current model is
        # the best match.
        serializer = self._select_subclass_serializer_by_model_instance(self.instance, data=self.initial_data)

        if serializer is self:
            # No need to use subclass, proceed with serialization for update

            # First update child instances, to be added to the model when it is created
            data_with_children = self._update_x_to_one_children(validated_data)

            # Update model, minus X2Many relationship
            #
            # Don't worry, x_to_many data is still in initial_data and we'll
            # validate it on the child models
            self._strip_x_to_many_data(data_with_children)
            self._strip_reverse_x_to_one_data(data_with_children)
            
            for field_name, field_data in data_with_children.iteritems():
                setattr(instance, field_name, field_data)
            instance.save()

            # Now update X2Many children
            instance = self._update_x_to_many_children(instance)
            
        else:
            # A subclass model exists. Defer deserialization to the serializer of the subclass.
            if not serializer.is_valid():
                raise Exception("Invalid data for model %s. Errors: %s" %
                                (serializer.Meta.model.__name__, serializer.errors))
            # Calling "save" will trigger the "create" method on the new serializer
            instance = serializer.save()

        instance.send_post_update()
        return instance

    def _update_x_to_one_children(self, validated_data):

        data_with_children = copy.deepcopy(validated_data)
        # For models with nested children, handle that serialization here:
        if hasattr(self.Meta, 'nested_x_to_one_serializers'):
            for field_name, ChildSerializer in self.Meta.nested_x_to_one_serializers.iteritems():
                data = self.initial_data.get(field_name)
                ChildSerializer = _get_class_from_string(ChildSerializer)
                try:
                    child_instance = getattr(self.instance, field_name)
                except ObjectDoesNotExist:
                    child_instance = None
                if data:
                    if child_instance:
                        # Update the existing child instance
                        child_serializer = ChildSerializer(child_instance, data=data, partial=False)
                    else:
                        # Create a new child instance
                        child_serializer = ChildSerializer(data=data)

                    if not child_serializer.is_valid():
                        raise Exception("Invalid data for model %s. Errors: %s" %
                                        (child_serializer.Meta.model.__name__, serializer.errors))

                    model = child_serializer.save()

                    # Replace raw data for child with model instance
                    data_with_children[field_name] = model

        return data_with_children

    def _update_x_to_many_children(self, model):

        # On update, we don't allow a change in the number of children.
        # Instead updates are passed through to each child.
        
        if hasattr(self.Meta, 'nested_x_to_many_serializers'):

            for field_name, ChildSerializer in self.Meta.nested_x_to_many_serializers.iteritems():
                ChildSerializer = _get_class_from_string(ChildSerializer)

                if self.initial_data.get(field_name):
                    for data, child_model in zip(self.initial_data.get(field_name), getattr(model, field_name).all()):
                        child_serializer = ChildSerializer(child_model, data=data)
                        child_serializer.is_valid()
                        child = child_serializer.save()

        return model

    def _select_subclass_serializer_by_model_instance(self, instance, data=None):

        # If not polymorphic, keep the current model instance
        if not hasattr(self.Meta, 'subclass_serializers'):
            return self

        subclass_serializers=[]
        for (field, SubclassSerializer) in self.Meta.subclass_serializers.iteritems():
            SubclassSerializer = _get_class_from_string(SubclassSerializer)
            try:
                # If a model instance is assigned to 'field', it means there
                # is a subclass instance of the current model. If so, get the
                # Serializer for the subclass model instance
                #
                subclass_instance = getattr(instance, field)
                if data is not None:
                    subclass_serializers.append(SubclassSerializer(subclass_instance, data=data))
                else:
                    subclass_serializers.append(SubclassSerializer(subclass_instance))
            except ObjectDoesNotExist:
                pass

        if len(subclass_serializers) == 1:
            # We found a matching subclass instance, so we'll return its serializer
            # to replace the current one
            #
            return subclass_serializers[0]
        
        elif len(subclass_serializers) == 0:
            # Model instance is does not belong to any subclass. Continue with the current serializer
            return self
        
        else:
            # We expect at most 1 matching subclass, but let's
            # verify because this is not enforced by Django.
            #
            raise Exception("Could not deserialize because the model instance to be updated has multiple "\
                            "subclass instances, and we don't know which one to update. %s" % instance)
