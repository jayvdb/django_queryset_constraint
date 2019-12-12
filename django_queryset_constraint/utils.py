from __future__ import unicode_literals

import json
import threading
from functools import partial

from django.apps import apps

# Thread local storage used for forwarding model/app to recursive M objects
tlocals = threading.local()


class M:
    """A :code:`M()` object is a lazy object utilized in place of Queryset(s).

    It is utilized when a Queryset cannot be used directly, for instance when a
    Queryset needs to be symbolically serialized to the disk, as is the case
    when generating migration files.

    It is a simple object, which simply records model name and app_label, such
    that the model can be retrieved, along with a stack of operations applied
    to the M object, such that these operations can be replayed to reconstruct
    the Queryset at a later time.
    """

    # TODO: Inherit from queryset + implement destruct() method?

    def __init__(
        self, model_name_override=None, app_label_override=None, operations=None
    ):
        """Construct an M object.

        Args:
            model (str, optional):
                Name of the model to apply the recorded M operations to.
                If :code:`None`, it defaults to the model upon which the M 
                object is constructed.
            app_label (str, optional):
                Application label for the model (previous argument).
                If :code:`None`, it defaults to the label where the M object
                is constructed.
            operations (list of dict, optional):
                Should not be supplied by the user.
        """
        self.model_name_override = model_name_override
        self.app_label_override = app_label_override
        self.operations = operations
        self.finalized = False
        if self.operations is None:
            self.operations = []
        else:
            self.finalized = True

    def recursive_unpartial(self, p):
        # Unfold args
        unfolded_args = []
        for arg in p.args:
            if isinstance(arg, partial):
                unfolded_args.append(self.recursive_unpartial(arg))
            else:
                unfolded_args.append(arg)
        # Unfold kwargs
        unfolded_kwargs = {}
        for key in p.keywords:
            value = p.keywords[key]
            if isinstance(value, partial):
                unfolded_kwargs[key] = self.recursive_unpartial(value)
            else:
                unfolded_kwargs[key] = value
        # Call function with unfolded arguments
        return p.func(*unfolded_args, **unfolded_kwargs)

    def _construct_queryset(self, app_label, model_name):
        # Run through all operations to generate our queryset
        # TODO: Apply rules recursively to subqueries
        if app_label is None or model_name is None:
            raise ValueError("app_label or model_name is None")
        model = apps.get_model(app_label, model_name)
        result = model
        for operation in self.operations:
            if operation["type"] == "__getitem__":
                arg = operation["key"]
                if isinstance(arg, partial):
                    arg = self.recursive_unpartial(arg)
                result = result.__getitem__(arg)
            elif operation["type"] == "__getattribute__":
                result = getattr(
                    result, *operation["args"], **operation["kwargs"]
                )
            elif operation["type"] == "__call__":
                operation["args"] = list(operation["args"])
                for idx, arg in enumerate(operation["args"]):
                    if isinstance(arg, partial):
                        operation["args"][idx] = self.recursive_unpartial(arg)
                for arg in operation["kwargs"]:
                    if isinstance(operation["kwargs"][arg], partial):
                        operation["kwargs"][arg] = self.recursive_unpartial(
                            operation["kwargs"][arg]
                        )
                result = result(*operation["args"], **operation["kwargs"])
            else:
                raise Exception("Unknown operation!")
        return result

    def construct_queryset(
        self, app_label_default=None, model_name_default=None
    ):
        # Take default from caller
        app_label = (
            self.app_label_override or app_label_default or tlocals.app_label
        )
        model_name = (
            self.model_name_override or model_name_default or tlocals.model_name
        )
        # Update thread-local storage to push it down the stack
        tlocals.app_label = app_label
        tlocals.model_name = model_name
        # Reply to build queryset
        result = self._construct_queryset(app_label, model_name)
        # Clean up thread-local storage
        try:
            del tlocals.app_label
        except AttributeError:
            pass
        try:
            del tlocals.model_name
        except AttributeError:
            pass
        # Return queryset
        return result

    def __getitem__(self, key):
        try:
            return object.__getitem__(self, key)
        except:
            if self.finalized:
                return self.construct_queryset().__getitem__(key)

            if isinstance(key, slice):
                self.operations.append(
                    {
                        "type": "__getitem__",
                        "key": partial(slice, key.start, key.stop, key.step),
                    }
                )
            else:
                self.operations.append({"type": "__getitem__", "key": key})
            return self

    def __getattribute__(self, *args, **kwargs):
        try:
            return object.__getattribute__(self, *args, **kwargs)
        except AttributeError as exc:
            if self.finalized:
                # Note: Needed to handle M objects inside subquery constructs
                return self.construct_queryset().__getattribute__(
                    *args, **kwargs
                )
            self.operations.append(
                {"type": "__getattribute__", "args": args, "kwargs": kwargs}
            )
            return self

    def __call__(self, *args, **kwargs):
        try:
            return object.__call__(self, *args, **kwargs)
        except TypeError as exc:
            if self.finalized:
                # Note: Needed to handle M objects inside subquery constructs
                return self.construct_queryset().__call__(self, *args, **kwargs)
            self.operations.append(
                {"type": "__call__", "args": args, "kwargs": kwargs}
            )
            return self

    def deconstruct(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        kwargs = {"operations": self.operations}
        if self.model_name_override is not None:
            kwargs["model_name_override"] = self.model_name_override
        if self.app_label_override is not None:
            kwargs["app_label_override"] = self.app_label_override
        return path, [], kwargs

    def __eq__(self, other):
        if not isinstance(other, M):
            return NotImplemented
        # Note: We cannot use self.operations == other.operations as we end up
        #       comparing BaseExpressions containing M objects (recursively).
        #       This comparison depends on M objects being hashable.
        return self.as_json() == other.as_json()

    def as_json(self):
        def deconstructor(argument):
            # Attempt to deconstruct
            try:
                result = argument.deconstruct()
                if len(result) == 4:
                    name, path, args, kwargs = result
                else:  # if len(result) == 3:
                    path, args, kwargs = result
            # If we cannot deconstruct, use repr instead
            except AttributeError:
                path = repr(argument)
                args = []
                kwargs = []
            # Convert to json string recursively, by deconstructing each step
            json_string = json.dumps(
                {"path": path, "args": args, "kwargs": kwargs},
                default=lambda o: deconstructor(o),
                sort_keys=True,
            )
            # Convert back to dict after handling all the deconstruction
            return json.loads(json_string)

        # Convert entire object to json string
        json_string = json.dumps(deconstructor(self), sort_keys=True)
        return json_string

    def __str__(self):
        return self.as_json()
