#!/bin/env python
# -*- coding: utf-8 -*-

import copy


def traverseDict(d):
    if type(d) == dict:
        for k, v in d.items():
            if k == "$ref":
                return False
            else:
                if not traverseDict(v):
                    return False
    return True


def convertRef(d, ref):
    if type(d) != dict:
        return d
    if "$ref" in d.keys():
        url = d["$ref"]
        url = url.split("/")[-1]
        if url in ref.keys():
            return ref[url]
    else:
        for k, v in d.items():
            d[k] = convertRef(v, ref)
        return d


def convertDefinitions(definitions, ref=None):
    ret = definitions
    while not traverseDict(definitions):
        keys = definitions.keys()
        remains = []
        for k in keys:
            if not traverseDict(definitions[k]):
                remains.append(k)
        for k in remains:
            if ref is None:
                ref = ret
            ret[k] = convertRef(definitions[k], ref)
    return ret


def convertProperties(paths):  # noqa
    for key, value in paths.items():
        for method in ["post", "get", "put", "head", "options", "delete"]:
            try:
                params = value[method]["parameters"]
                properties = []
                delete = set()
                for i in range(len(params)):
                    if params[i]["in"] != "body":
                        continue
                    required = False
                    if "required" in params[i]:
                        required = params[i]["required"]
                    r_l = []
                    if required in params[i]["schema"]:
                        r_l = params[i]["schema"]["required"]
                    for name, spec in \
                            params[i]["schema"]["properties"].items():
                        sspec = copy.deepcopy(spec)
                        sspec.update(
                            {
                                "in": "body",
                                "required": required and (name in r_l),
                                "name": name,
                            }
                        )
                        properties.append(sspec)
                        delete.add(i)
            except KeyError:
                continue
            l = [i for i in delete]
            l.reverse()
            for i in l:
                params.pop(i)
            for p in properties:
                params.append(p)
    return paths


def expand(j):
    if "definitions" in j and j["definitions"]:
        definitions = j["definitions"]
        j["definitions"] = convertDefinitions(definitions)
        for url in j["paths"]:
            for method in j["paths"][url]:
                try:
                    list_p = j["paths"][url][method]["parameters"]
                except:
                    continue
                for i in range(len(j["paths"][url][method]["parameters"])):
                    if "$ref" in list_p[i]:
                        list_p[i] = j[
                            "parameters"][list_p[i]["$ref"].split("/")[-1]]
                    else:
                        list_p[i] = convertDefinitions(
                            list_p[i], j["definitions"])
    return j
