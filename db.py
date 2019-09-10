from SPARQLWrapper import SPARQLWrapper, JSON, JSONLD

from utils.exceptions import NoResultException

ODPW_GRAPH = "https://data.wu.ac.at/portalwatch/ld"

class DB:
    def __init__(self, endpoint):
        self.sparql = SPARQLWrapper(endpoint)

    def get_latest_snapshot(self, portal_ref=None):
        if portal_ref:
            statement = "SELECT MAX(?s) AS ?snapshot WHERE {{ ?a odpw:snapshot ?s. ?a odpw:fetched <{0}> }}".format(portal_ref)
        else:
            statement = "SELECT MAX(?s) AS ?snapshot WHERE {{ ?a odpw:snapshot ?s }}".format(portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        r = res['results']['bindings'][0]
        if len(res['results']['bindings']) == 0:
            raise NoResultException('Portal ' + portal_ref + ' not found.', DB.get_latest_snapshot.__name__)
        result = int(r['snapshot']['value'])
        return result


    def get_snapshots_info(self):
        statement = "SELECT ?p MAX(?s) AS ?snLast COUNT(?s) AS ?snCount WHERE { ?a odpw:snapshot ?s. ?a odpw:fetched ?p }"
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = {}
        for r in res['results']['bindings']:
            results[r['p']['value']] = {'snLast': int(r['snLast']['value']), 'snCount': int(r['snCount']['value'])}
        return results


    def get_graphs(self):
        statement = "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }"
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = []
        for r in res['results']['bindings']:
            g = r['g']['value']
            if ODPW_GRAPH + '/' in g:
                results.append(g)
        return sorted(results, reverse=True)


    def get_portals(self, active=True):
        if active:
            statement = "SELECT * FROM <{0}> WHERE {{?p a dcat:Catalog. ?p odpw:active true. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier ?id. ?p odpw:software ?s. ?p odpw:iso ?iso}}".format(ODPW_GRAPH)
        else:
            statement = "SELECT * FROM <{0}> WHERE {{?p a dcat:Catalog. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier ?id. ?p odpw:software ?s. ?p odpw:iso ?iso}}".format(ODPW_GRAPH)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = {}
        for r in res['results']['bindings']:
            results[r['p']['value']] = {'title': r['t']['value'], 'apiuri': r['a']['value'], 'uri': r['p']['value'], 'id': r['id']['value'], 'software': r['s']['value'].split('#')[1], 'iso': r['iso']['value']}
        return results


    def get_dead_portals(self):
        statement = "SELECT * WHERE {?p a dcat:Catalog. ?p odpw:active false. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier ?id. ?p odpw:software ?s. ?p odpw:iso ?iso}"
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = {}
        for r in res['results']['bindings']:
            results[r['p']['value']] = {'title': r['t']['value'], 'apiuri': r['a']['value'], 'uri': r['p']['value'], 'id': r['id']['value'], 'software': r['s']['value'].split('#')[1], 'iso': r['iso']['value']}
        return results


    def get_portals_info(self, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        # datasets, resources, snLast
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?p COUNT(DISTINCT ?d) AS ?datasets COUNT(?r) AS ?resources FROM <{0}> WHERE {{ ?p dcat:dataset ?d. ?d dcat:distribution ?r }}".format(sn_graph)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = {}
        for r in res['results']['bindings']:
            results[r['p']['value']] = {'uri': r['p']['value'], 'datasets': int(r['datasets']['value']), 'resources': int(r['resources']['value']), 'snLast': snapshot}
        return results

    def get_top_portals_info(self, snapshot=None, limit=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        # datasets, resources, snLast
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT DISTINCT ?p COUNT(DISTINCT ?d) AS ?datasets COUNT(?r) AS ?resources FROM <{0}> WHERE {{?p dcat:dataset ?d. ?d dcat:distribution ?r }} ORDER BY DESC(?datasets)".format(sn_graph)
        if limit:
            statement += " LIMIT " + str(limit)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        results = []
        for r in res['results']['bindings']:
            results.append({'uri': r['p']['value'], 'datasets': int(r['datasets']['value']), 'resources': int(r['resources']['value']), 'snLast': snapshot})
        return results



    def get_portal(self, id):
        statement = "SELECT * WHERE {{?p a dcat:Catalog. ?p odpw:active true. ?p dct:title ?t. ?p odpw:api ?a. ?p odpw:identifier \"{0}\". ?p odpw:software ?s. ?p odpw:iso ?iso}}".format(id)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        if len(res['results']['bindings']) == 0:
            raise NoResultException('Portal ID "' + id + '" not found.', DB.get_portal.__name__)
        r = res['results']['bindings'][0]
        result = {'title': r['t']['value'], 'apiuri': r['a']['value'], 'uri': r['p']['value'], 'id': id, 'software': r['s']['value'].split('#')[1], 'iso': r['iso']['value']}
        return result

    def get_portal_info(self, portal_ref, snapshot=None):
        if snapshot == None:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT COUNT(DISTINCT ?d) AS ?datasets COUNT(?r) AS ?resources FROM <{0}> WHERE {{<{1}> dcat:dataset ?d. ?d dcat:distribution ?r }}".format(sn_graph, portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        if len(res['results']['bindings']) == 0:
            raise NoResultException('Portal ' + portal_ref + ' with snapshot ' + str(snapshot) + ' not found.', DB.get_portal_info.__name__)
        r = res['results']['bindings'][0]
        result = {'uri': portal_ref, 'datasets': int(r['datasets']['value']), 'resources': int(r['resources']['value'])}
        return result

    def get_portal_quality(self, portal_ref, snapshot=None):
        if snapshot == None:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?metric ?id SUM(?value)/COUNT(?value) AS ?measurement COUNT(?value) AS ?numValues COUNT(?d) AS ?datasets FROM <{0}> FROM <{1}> WHERE {{ <{2}> dcat:dataset ?d. ?d dqv:hasQualityMeasurement ?m. ?m dqv:isMeasurementOf ?metric. ?metric odpw:identifier ?id. ?m dqv:value ?value }} GROUP BY ?metric ?id".format(ODPW_GRAPH, sn_graph, portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = {}
        for r in res['results']['bindings']:
            result[r['id']['value']] = {k: r[k]['value'] for k in r}
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

    def get_portal_datasets(self, portal_ref, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?d ?title ?id FROM <{0}> WHERE {{ <{1}> dcat:dataset ?d. ?d dct:title ?title. ?d dct:identifier ?id }}".format(sn_graph, portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = []
        for r in res['results']['bindings']:
            result.append({'dataset': r['d']['value'], 'title': r['title']['value'], 'id': r['id']['value']})
        return result
    
    
    def get_formats(self, snapshot=None, limit=10):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?format COUNT(?format) AS ?count xsd:float(COUNT(?format))/xsd:float(?allformat) AS ?perc FROM <{0}> WHERE {{ {{ SELECT COUNT(*) AS ?allformat FROM <{0}> WHERE {{ ?dist dct:format ?format }} }} {{?dist dct:format ?format . FILTER(isLiteral(?format)) }} UNION {{ ?dist dct:format ?b . ?b rdfs:label ?format }} }} GROUP BY ?format ?allformat ORDER BY DESC(?count)".format(sn_graph)
        if limit:
            statement += " LIMIT " + str(limit)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = []
        for r in res['results']['bindings']:
            result.append({'label': r['format']['value'], 'count': int(r['count']['value']), 'perc': float(r['perc']['value'])})
        return result

    def get_licenses(self, snapshot=None, limit=10):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?license COUNT(?license) AS ?count xsd:float(COUNT(?license))/xsd:float(?alllicense) AS ?perc FROM <{0}> WHERE {{ {{ SELECT COUNT(*) AS ?alllicense FROM <{0}> WHERE {{ ?dist dct:license ?license }} }} {{ ?dist dct:license ?license . FILTER(isLiteral(?license)) }} UNION {{ ?dist dct:license ?b . ?b rdfs:label ?license }} }} GROUP BY ?license ?alllicense ORDER BY DESC(?count)".format(sn_graph)
        if limit:
            statement += " LIMIT " + str(limit)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = []
        for r in res['results']['bindings']:
            result.append({'label': r['license']['value'], 'count': int(r['count']['value']), 'perc': float(r['perc']['value'])})
        return result


    def get_organisations(self, snapshot=None, limit=10):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?orga COUNT(?orga) AS ?count xsd:float(COUNT(?orga))/xsd:float(?allorga) AS ?perc FROM <{0}> WHERE {{ {{ SELECT COUNT(*) AS ?allorga FROM <{0}> WHERE {{?d dct:publisher ?orga }} }} {{ ?d dct:publisher ?orga . FILTER(isLiteral(?orga)) }} UNION {{ ?d dct:publisher ?b . ?b foaf:name ?orga }} }} GROUP BY ?orga ?allorga ORDER BY DESC(?count)".format(sn_graph)
        if limit:
            statement += " LIMIT " + str(limit)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = []
        for r in res['results']['bindings']:
            result.append({'label': r['orga']['value'], 'count': int(r['count']['value']), 'perc': float(r['perc']['value'])})
        return result


    def get_portal_formats(self, portal_ref, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?format COUNT(?format) AS ?count xsd:float(COUNT(?format))/xsd:float(?allformat) AS ?perc FROM <{0}> WHERE {{ {{ SELECT COUNT(*) AS ?allformat FROM <{0}> WHERE {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:format ?format }} }} {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:format ?format . FILTER(isLiteral(?format)) }} UNION {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:format ?b . ?b rdfs:label ?format }} }} GROUP BY ?format ?allformat ORDER BY DESC(?count)".format(sn_graph, portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = []
        for r in res['results']['bindings']:
            result.append({'label': r['format']['value'], 'count': int(r['count']['value']), 'perc': float(r['perc']['value'])})
        return result

    def get_portal_format_count(self, portal_ref, format, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT COUNT(?format) AS ?count FROM <{0}> WHERE {{ {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:format ?format . }} UNION {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:format ?b . ?b rdfs:label ?format }} FILTER (lcase(str(?format)) = \"{2}\") }}".format(sn_graph, portal_ref, format)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        if len(res['results']['bindings']) == 0:
            raise NoResultException('Error while counting formats for portal ' + portal_ref + ' with snapshot ' + str(snapshot) + '.', DB.get_portal_format_count.__name__)
        r = res['results']['bindings'][0]
        return int(r['count']['value'])

    def get_portal_licenses(self, portal_ref, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?license COUNT(?license) AS ?count xsd:float(COUNT(?license))/xsd:float(?alllicense) AS ?perc FROM <{0}> WHERE {{ {{ SELECT COUNT(*) AS ?alllicense FROM <{0}> WHERE {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:license ?license }} }} {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:license ?license . FILTER(isLiteral(?license)) }} UNION {{ <{1}> dcat:dataset ?d . ?d dcat:distribution ?dist . ?dist dct:license ?b . ?b rdfs:label ?license }} }} GROUP BY ?license ?alllicense ORDER BY DESC(?count)".format(sn_graph, portal_ref)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = []
        for r in res['results']['bindings']:
            result.append({'label': r['license']['value'], 'count': int(r['count']['value']), 'perc': float(r['perc']['value'])})
        return result


    def get_portal_organisations(self, portal_ref, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "SELECT ?orga COUNT(?orga) AS ?count xsd:float(COUNT(?orga))/xsd:float(?allorga) AS ?perc FROM <{0}> WHERE {{ {{ SELECT COUNT(*) AS ?allorga FROM <{0}> WHERE {{ <{1}> dcat:dataset ?d . ?d dct:publisher ?orga }} }} {{ <{1}> dcat:dataset ?d . ?d dct:publisher ?orga . FILTER(isLiteral(?orga)) }} UNION {{ <{1}> dcat:dataset ?d . ?d dct:publisher ?b . ?b foaf:name ?orga }} }} GROUP BY ?orga ?allorga ORDER BY DESC(?count)".format(sn_graph, portal_ref)
        print(statement)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = []
        for r in res['results']['bindings']:
            result.append({'label': r['orga']['value'], 'count': int(r['count']['value']), 'perc': float(r['perc']['value'])})
        return result


    def get_portals_count(self, active=True):
        if active:
            statement = "SELECT COUNT(DISTINCT ?p) AS ?c FROM <{0}> WHERE {{?p a dcat:Catalog. ?p odpw:active true}}".format(ODPW_GRAPH)
        else:
            statement = "SELECT COUNT(DISTINCT ?p) AS ?c FROM <{0}> WHERE {{?p a dcat:Catalog}}".format(ODPW_GRAPH)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        count = res['results']['bindings'][0]['c']['value']
        return count

    def get_full_dataset(self, d_uri, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "CONSTRUCT {{ <{1}> ?p ?o. ?o ?r ?q }}  FROM <{0}>  WHERE {{ <{1}> ?p ?o . ?o ?r ?q . }}".format(sn_graph, d_uri)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSONLD)
        res = self.sparql.query().convert()
        return res


    def get_full_dataset_by_id(self, datasetid, snapshot=None):
        if not snapshot:
            snapshot = self.get_latest_snapshot()
        sn_graph = ODPW_GRAPH + '/' + str(snapshot)
        statement = "CONSTRUCT {{ ?d ?p ?o. ?o ?r ?q }}  FROM <{0}>  WHERE {{ ?d ?p ?o . ?o ?r ?q . ?d dct:identifier \"{1}\" }}".format(sn_graph, datasetid)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        return res


    def get_dataset_graphs(self, dataset_uri):
        statement = "SELECT ?g WHERE {{ GRAPH ?g {{ <{0}> a dcat:Dataset }} }}".format(dataset_uri)
        self.sparql.setQuery(statement)
        self.sparql.setReturnFormat(JSON)
        res = self.sparql.query().convert()
        result = [g['g']['value'] for g in res['results']['bindings']]
        return result



if __name__ == '__main__':
    db = DB("http://localhost:8890/sparql")
    print(db.get_portals_count())