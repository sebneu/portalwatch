from SPARQLWrapper import SPARQLWrapper, JSON


class DB:
    def __init__(self, endpoint):
        self.sparql = SPARQLWrapper(endpoint)

    def get_portals(self):
        statement = "SELECT * WHERE {?p a dcat:Catalog. ?p odpw:active true. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier ?id. ?p odpw:software ?s. ?p odpw:iso ?iso}"
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = []
        for r in res['results']['bindings']:
            results.append({'title': r['t']['value'], 'apiuri': r['a']['value'], 'uri': r['p']['value'], 'pid': r['id']['value'], 'software': r['s']['value'].split('#')[1], 'iso': r['iso']['value']})
        return results


    def get_portal(self, id):
        statement = "SELECT * WHERE {{?p a dcat:Catalog. ?p odpw:active true. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier \"{0}\". ?p odpw:software ?s. ?p odpw:iso ?iso}}".format(id)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()

        r = res['results']['bindings'][0]
        result = {'title': r['t']['value'], 'apiuri': r['a']['value'], 'uri': r['p']['value'], 'pid': id, 'software': r['s']['value'].split('#')[1], 'iso': r['iso']['value']}
        return result


    def get_portals_count(self):
        statement = "SELECT COUNT(?p) AS ?c WHERE {?p a dcat:Catalog. ?p odpw:active true}"
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        count = res['results']['bindings'][0]['c']['value']
        return count


if __name__ == '__main__':
    db = DB("http://localhost:8890/sparql")
    print(db.get_portals_count())