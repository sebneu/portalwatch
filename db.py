from SPARQLWrapper import SPARQLWrapper, JSON
from utils.snapshots import getCurrentSnapshot

ODPW_GRAPH = "http://data.wu.ac.at/portalwatch/ld"

class DB:
    def __init__(self, endpoint):
        self.sparql = SPARQLWrapper(endpoint)

    def get_portals(self):
        statement = "SELECT * WHERE {?p a dcat:Catalog. ?p odpw:active true. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier ?id. ?p odpw:software ?s. ?p odpw:iso ?iso}"
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = {}
        for r in res['results']['bindings']:
            results[r['p']['value']] = {'title': r['t']['value'], 'apiuri': r['a']['value'], 'uri': r['p']['value'], 'id': r['id']['value'], 'software': r['s']['value'].split('#')[1], 'iso': r['iso']['value']}
        return results

    def get_portals_info(self, snapshot=None):
        if not snapshot:
            snapshot = getCurrentSnapshot()
        # datasets, resources, snLast
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?p COUNT(DISTINCT ?d) AS ?datasets COUNT(?r) AS ?resources FROM <{0}> WHERE {{?p dcat:dataset ?d. ?d dcat:distribution ?r }}".format(sn_graph)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = {}
        for r in res['results']['bindings']:
            results[r['p']['value']] = {'uri': r['p']['value'], 'datasets': r['datasets']['value'], 'resources': r['resources']['value'], 'snLast': snapshot}
        return results


    def get_portal(self, id):
        statement = "SELECT * WHERE {{?p a dcat:Catalog. ?p odpw:active true. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier \"{0}\". ?p odpw:software ?s. ?p odpw:iso ?iso}}".format(id)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        r = res['results']['bindings'][0]
        result = {'title': r['t']['value'], 'apiuri': r['a']['value'], 'uri': r['p']['value'], 'id': id, 'software': r['s']['value'].split('#')[1], 'iso': r['iso']['value']}
        return result

    def get_portal_info(self, portal_ref, snapshot=None):
        if not snapshot:
            snapshot = getCurrentSnapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT COUNT(DISTINCT ?d) AS ?datasets COUNT(?r) AS ?resources FROM <{0}> WHERE {{<{1}> dcat:dataset ?d. ?d dcat:distribution ?r }}".format(sn_graph, portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        r = res['results']['bindings'][0]
        result = {'uri': portal_ref, 'datasets': r['datasets']['value'], 'resources': r['resources']['value'], 'snLast': snapshot}
        return result

    def get_portal_quality(self, portal_ref, snapshot=None):
        if not snapshot:
            snapshot = getCurrentSnapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?metric SUM(?value)/COUNT(?value) AS ?measurement COUNT(?value) AS ?numValues COUNT(?d) AS ?datasets FROM <{0}> WHERE {{ {1} dcat:dataset ?d. ?d dqv:hasQualityMeasurement ?m. ?m dqv:isMeasurementOf ?metric. ?m dqv:value ?value }} GROUP BY(?metric)".format(sn_graph, portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = {}
        for r in res['results']['bindings']:
            result[r['metric']['value']] = {k: r[k]['value'] for k in r}
        return result

    def get_portal_snapshots(self, id):
        statement = "SELECT ?s WHERE {{ ?p odpw:identifier \"{0}\". ?p odpw:wasFetchedBy ?a. ?a odpw:snapshot ?s }}".format(id)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        snapshots = []
        for r in res['results']['bindings']:
            snapshots.append(int(r['s']['value']))
        snapshots.sort()
        return snapshots


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