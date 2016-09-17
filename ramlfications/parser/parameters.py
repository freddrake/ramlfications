# -*- coding: utf-8 -*-
# Copyright (c) 2015 Spotify AB

from __future__ import absolute_import, division, print_function

from six import iteritems, itervalues, string_types

from ramlfications.config import MEDIA_TYPES
from ramlfications.models.parameters import (
    Body, Header, Response, URIParameter
)
from ramlfications.utils import load_schema, NodeList
from ramlfications.utils.common import _get, substitute_parameters
from ramlfications.utils.parameter import (
    map_object, resolve_scalar_data, add_missing_uri_data
)


class BaseParameterParser(object):
    def create_base_param_obj(self, attribute_data, param_obj,
                              config, errors, **kw):
        """
        Helper function to create a child of a
        :py:class:`.parameters.BaseParameter` object
        """
        objects = NodeList()

        for key, value in list(iteritems(attribute_data)):
            if param_obj is URIParameter:
                required = _get(value, "required", default=True)
            else:
                required = _get(value, "required", default=False)
            if kw['root'].raml_version == "0.8":
                examples = None
            else:
                examples = _get(value, "examples")
            kwargs = dict(
                name=key,
                raw={key: value},
                desc=_get(value, "description"),
                display_name=_get(value, "displayName", key),
                min_length=_get(value, "minLength"),
                max_length=_get(value, "maxLength"),
                minimum=_get(value, "minimum"),
                maximum=_get(value, "maximum"),
                default=_get(value, "default"),
                enum=_get(value, "enum"),
                example=_get(value, "example"),
                examples=examples,
                required=required,
                repeat=_get(value, "repeat", False),
                pattern=_get(value, "pattern"),
                type=_get(value, "type", "string"),
                config=config,
                errors=errors
            )
            if param_obj is Header:
                kwargs["method"] = _get(kw, "method")

            item = param_obj(**kwargs)
            objects.append(item)

        return objects or None


class BodyParserMixin(object):
    def parse_body(self, mime_type, data, root, method):
        """
        Create a :py:class:`.parameters.Body` object.
        """
        raw = {mime_type: data}
        kwargs = dict(
            data=data,
            method=method,
            root=root,
            errs=root.errors,
            conf=root.config
        )
        form_param_parser = ParameterParser("formParameters", kwargs)
        form_params = form_param_parser.parse()
        return Body(
            mime_type=mime_type,
            raw=raw,
            schema=load_schema(_get(data, "schema")),
            example=load_schema(_get(data, "example")),
            form_params=form_params,
            config=root.config,
            errors=root.errors
        )


class ParameterParser(BaseParameterParser, BodyParserMixin):
    """
    Base parser for Named Parameters.
    """
    def __init__(self, param, kwargs, resolve_from=[]):
        self.param = param
        self.resolve_from = resolve_from
        self.kwargs = kwargs
        self.method = _get(kwargs, "method", None)
        self.path = _get(kwargs, "resource_path")
        self.is_ = _get(kwargs, "is_", None)
        self.type_ = _get(kwargs, "type_", None)
        self.root = _get(kwargs, "root")

    def _set_param_data(self, param_data, path, path_name):
        param_data["resourcePath"] = path
        param_data["resourcePathName"] = path_name
        return param_data

    def _substitute_params(self, resolved):
        """
        Returns dict of param data with relevant ``<<parameter>>`` substituted.
        """
        # this logic ain't too pretty...
        if self.path:
            _path = self.path
            _path_name = _path.lstrip("/")
        else:
            _path = "<<resourcePath>>"
            _path_name = "<<resourcePathName>>"

        if self.is_:
            if isinstance(self.is_, list):
                # I think validate.py would error out if this is not a list
                for i in self.is_:
                    if isinstance(i, dict):
                        param_data = list(itervalues(i))[0]
                        param_data = self._set_param_data(param_data, _path,
                                                          _path_name)
                        resolved = substitute_parameters(resolved, param_data)

        if self.type_:
            if isinstance(self.type_, dict):
                param_type = self.type_
                param_data = list(itervalues(param_type))[0]
                param_data = self._set_param_data(param_data, _path,
                                                  _path_name)
                resolved = substitute_parameters(resolved, param_data)
        return resolved

    def resolve(self):
        resolved = resolve_scalar_data(self.param, self.resolve_from,
                                       **self.kwargs)
        resolved = self._substitute_params(resolved)

        if self.param == "uriParameters":
            if self.path:
                resolved = add_missing_uri_data(self.path, resolved)
        return resolved

    def parse_bodies(self, resolved):
        """
        Returns a list of :py:class:`.parameters.Body` objects.
        """
        root = _get(self.kwargs, "root")
        method = _get(self.kwargs, "method")
        body_objects = []
        for k, v in list(iteritems(resolved)):
            if v is None:
                continue
            body = self.parse_body(k, v, root, method)
            body_objects.append(body)
        return body_objects or None

    def parse_responses(self, resolved):
        """
        Returns a list of :py:class:`.parameters.Response` objects.
        """
        # root = _get(self.kwargs, "root")
        method = _get(self.kwargs, "method")
        response_objects = []

        for key, value in list(iteritems(resolved)):
            response_parser = ResponseParser(key, value, method, self.root)
            response = response_parser.parse()
            response_objects.append(response)
        return sorted(response_objects, key=lambda x: x.code) or None

    def parse(self):
        if not self.resolve_from:
            self.resolve_from = ["method", "resource"]  # set default

        resolved = self.resolve()
        if self.param == "body":
            return self.parse_bodies(resolved)
        if self.param == "responses":
            return self.parse_responses(resolved)

        conf = _get(self.kwargs, "conf", None)
        errs = _get(self.kwargs, "errs", None)
        if self.root:
            conf = self.root.config
            errs = self.root.errors

        object_name = map_object(self.param)
        params = self.create_base_param_obj(resolved, object_name, conf,
                                            errs, method=self.method,
                                            root=self.root)
        return params or None


class ResponseParser(BaseParameterParser, BodyParserMixin):
    def __init__(self, code, data, method, root):
        self.code = code
        self.data = data
        self.method = method
        self.root = root

    def parse_response_headers(self):
        headers = _get(self.data, "headers", default={})

        header_objects = self.create_base_param_obj(headers, Header,
                                                    self.root.config,
                                                    self.root.errors,
                                                    method=self.method)
        return header_objects or None

    def parse_response_body(self):
        """
        Create :py:class:`.parameters.Body` objects for a
        :py:class:`.parameters.Response` object.
        """
        body = _get(self.data, "body", default={})
        body_list = []
        no_mime_body_data = {}
        for key, spec in list(iteritems(body)):
            if key not in MEDIA_TYPES:
                # if a root mediaType was defined, the response body
                # may omit the mime_type definition
                if key in ('schema', 'example'):
                    no_mime_body_data[key] = load_schema(spec) if spec else {}
            else:
                # spec might be '!!null'
                raw = spec or body
                _body = self.parse_body(key, raw, self.root, self.method)
                body_list.append(_body)
        if no_mime_body_data:
            _body = self.parse_body(self.root.media_type,
                                    no_mime_body_data, self.root,
                                    self.method)
            body_list.append(_body)

        return body_list or None

    def parse(self):
        headers = self.parse_response_headers()
        body = self.parse_response_body()
        desc = _get(self.data, "description", None)

        if isinstance(self.code, string_types):
            try:
                self.code = int(self.code)
            except ValueError:
                # this should be caught by validate.py
                pass

        return Response(
            code=self.code,
            raw={self.code: self.data},
            method=self.method,
            desc=desc,
            headers=headers,
            body=body,
            config=self.root.config,
            errors=self.root.errors
        )
