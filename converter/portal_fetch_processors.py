import json
from ast import literal_eval
import random
import urllib.parse
import time
import requests
import ckanapi

import rdflib
from rdflib import URIRef
from rdflib.namespace import RDF
from rdflib import Namespace

from utils.ssl_ignore import no_ssl_verification

PROV = Namespace('http://www.w3.org/ns/prov#')

PROV_ACTIVITY = 'https://data.wu.ac.at/portalwatch/ld/activity#'

import logging
logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

from converter.dataset_converter import namespaces, DCAT, convert_socrata, graph_from_opendatasoft, \
    graph_from_data_gouv_fr, CKANConverter
import quality


def getPortalProcessor(software):
    if software == 'CKAN':
        return CKAN()
    elif software == 'Socrata':
        return Socrata()
    elif software == 'OpenDataSoft':
        return OpenDataSoft()
    elif software == 'XMLDCAT':
        return XMLDCAT()
    elif software == 'CKANDCAT':
        return CKANDCAT()
    elif software == 'SPARQL':
        return SPARQL()
    elif software == 'DataGouvFr':
        return DataGouvFr()
    else:
        raise NotImplementedError(software + ' is not implemented')


class PortalProcessor:
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity):
        raise NotImplementedError("Should have implemented this")

class CKAN(PortalProcessor):
    def _waiting_time(self, attempt):
        if attempt == 1:
            return 3
        else:
            return attempt*attempt*5

    def _get_datasets(self, api, timeout_attempts, rows, start):
        for attempt in range(timeout_attempts):
            time.sleep(self._waiting_time(attempt))
            try:
                response = api.action.package_search(rows=rows, start=start)
                return response
            except ckanapi.errors.CKANAPIError as e:
                err = literal_eval(e.extra_msg)
                if 500 <= err[1] < 600:
                    rows =rows/3 if rows>=3 else rows
                else:
                    raise e

    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity, timeout_attempts=5, timeout=24*60*60):
        starttime=time.time()
        start=0
        rows=1000
        total=0
        processed_ids=set([])
        processed_names=set([])

        try:
            with no_ssl_verification():
                session = requests.Session()
                session.verify = False
                api = ckanapi.RemoteCKAN(portal_api, get_only=True, session=session)
                response = api.action.package_search(rows=0)
                total = response["count"]
                # TODO store total

                while True:
                    response = self._get_datasets(api, timeout_attempts, rows, start)

                    #print Portal.apiurl, start, rows, len(processed)
                    datasets = response["results"] if response else None
                    if datasets:
                        rows = len(datasets)
                        start+=rows
                        for datasetJSON in datasets:
                            datasetID = datasetJSON['id']
                            try:
                                if datasetID not in processed_ids:
                                    converter = CKANConverter(graph, portal_api)
                                    dataset_ref = converter.graph_from_ckan(datasetJSON)
                                    graph.add((portal_ref, DCAT.dataset, dataset_ref))
                                    quality.add_quality_measures(dataset_ref, graph, activity)
                                    processed_ids.add(datasetID)
                                    processed_names.add(datasetJSON['name'])


                                    now = time.time()
                                    if now-starttime>timeout:
                                        raise TimeoutError("Timeout of "+portal_api+" and "+str(timeout)+" seconds", timeout)
                            except Exception as e:
                                logger.error("CKANDSFetchDatasetBatchError: " + str(e))
                        rows = min([int(rows*1.2),1000])
                    else:
                        break
        except TimeoutError as e:

            raise e
        except Exception as e:
            logger.error("CKANDSFetchBatchError " + portal_api + ": " + str(e))

        if len(processed_ids) != total:
            logger.info("Not all datasets processed: fetched=" + str(len(processed_ids)) + ", total=" + str(total))

            try:
                package_list, status = getPackageList(portal_api)
                tt=len(package_list)
                if total==0:
                    # TODO store total tt
                    pass
                # TODO parameter:
                NOT_SUPPORTED_PENALITY = 100
                TIMEOUT_PENALITY = 100
                not_supported_count = 0
                timeout_counts = 0
                for entity in package_list:
                    #WAIT between two consecutive GET requests
                    if entity not in processed_ids and entity not in processed_names:
                        time.sleep(random.uniform(0.5, 1))
                        try:
                            resp, status = getPackage(apiurl=portal_api, id=entity)
                            if resp:
                                data = resp
                                processed_names.add(entity)
                                converter = CKANConverter(graph, portal_api)
                                dataset_ref = converter.graph_from_ckan(data)
                                graph.add((portal_ref, DCAT.dataset, dataset_ref))
                                quality.add_quality_measures(dataset_ref, graph, activity)
                                if entity not in processed_ids:
                                    processed_ids.add(entity)
                        except Exception as e:
                            logger.error('fetchDS: ' + str(e))

                            # if we get too much exceptions we assume this is not supported
                            not_supported_count += 1
                            if not_supported_count > NOT_SUPPORTED_PENALITY:
                                return

                    now = time.time()
                    if now - starttime > timeout:
                        raise TimeoutError(
                            "Timeout of " + portal_api + " and " + str(timeout) + " seconds", timeout)
            except Exception as e:
                if len(processed_ids)==0 or isinstance(e,TimeoutError):
                    raise e


class Socrata(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity):

        api = urllib.parse.urljoin(portal_api, '/api/')
        page = 1
        processed=set([])

        with no_ssl_verification():
            while True:
                resp = requests.get(urllib.parse.urljoin(api, '/views/metadata/v1?page=' + str(page)), verify=False)
                if resp.status_code != requests.codes.ok:
                    # TODO wait? appropriate message
                    pass

                res = resp.json()
                # returns a list of datasets
                if not res:
                    break
                for datasetJSON in res:
                    if 'id' not in datasetJSON:
                        continue

                    datasetID = datasetJSON['id']
                    if datasetID not in processed:
                        dataset_ref = convert_socrata(graph, datasetJSON, portal_api)
                        graph.add((portal_ref, DCAT.dataset, dataset_ref))
                        quality.add_quality_measures(dataset_ref, graph, activity)
                        processed.add(datasetID)

                        if len(processed) % 1000 == 0:
                            logger.info("ProgressDSFetch: " + portal_api + ", processed= " + str(len(processed)))
                page += 1
                # TODO store total len(processed)


class OpenDataSoft(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity):
        
        start=0
        rows=10000
        processed=set([])

        with no_ssl_verification():
            while True:
                query = '/api/datasets/1.0/search?rows=' + str(rows) + '&start=' + str(start)
                resp = requests.get(urllib.parse.urljoin(portal_api, query), verify=False)
                res = resp.json()
                datasets = res['datasets']
                if datasets:
                    rows = len(datasets) if start==0 else rows
                    start+=rows
                    for datasetJSON in datasets:
                        if 'datasetid' not in datasetJSON:
                            continue
                        datasetID = datasetJSON['datasetid']

                        if datasetID not in processed:
                            dataset_ref = graph_from_opendatasoft(graph, datasetJSON, portal_api)
                            graph.add((portal_ref, DCAT.dataset, dataset_ref))
                            quality.add_quality_measures(dataset_ref, graph, activity)
                            processed.add(datasetID)

                            if len(processed) % 1000 == 0:
                                logger.info("ProgressDSFetch: " + portal_api + ", processed= " + str(len(processed)))
                else:
                    break
            # TODO store total len(processed)


class XMLDCAT(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity):

        with no_ssl_verification():
            graph = rdflib.Graph()
            graph.parse(portal_api, format="xml")

            for d in graph.subjects(RDF.type, DCAT.Dataset):
                quality.add_quality_measures(d, graph, activity)

            # TODO store total len(processed)


class SPARQL(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity):

        url = portal_api + "?format=text/turtle&query="
        query = """
        construct {?dataset a dcat:Dataset}  {
            ?dataset a dcat:Dataset.
        }
        """

        limit = 10000
        offset = 0
        download_url = url + urllib.parse.quote(query + " OFFSET " + str(offset) + " LIMIT " + str(limit))
        tmpgraph = rdflib.Graph()
        tmpgraph.parse(download_url, format='ttl')
        datasets = [d for d in tmpgraph.subjects(RDF.type, DCAT.Dataset)]

        with no_ssl_verification():
            while len(datasets) > 0:
                for dataset_uri in tmpgraph.subjects(RDF.type, DCAT.Dataset):
                    construct_query = """
                    CONSTRUCT {{ <{0}> ?p ?o. ?o ?q ?r}}
                    WHERE {{
                    <{0}> a dcat:Dataset.
                    <{0}> ?p ?o
                    OPTIONAL {{?o ?q ?r}}
                    }}
                    """.format(str(dataset_uri))

                    ds_url = url + urllib.parse.quote(construct_query)
                    graph.parse(ds_url, format='ttl')
                    graph.add((portal_ref, DCAT.dataset, dataset_uri))
                    graph.add((dataset_uri, RDF.type, DCAT.Dataset))
                    quality.add_quality_measures(dataset_uri, graph, activity)

                offset += limit
                download_url = url + urllib.parse.quote(query + " OFFSET " + str(offset) + " LIMIT " + str(limit))
                tmpgraph = rdflib.Graph()
                tmpgraph.parse(download_url, format='ttl')
                datasets = [d for d in tmpgraph.subjects(RDF.type, DCAT.Dataset)]



class CKANDCAT(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity, format="ttl"):

        logger.debug('Fetching CKAN portal via RDF endpoint: ' + portal_api)

        with no_ssl_verification():
            graph.parse(portal_api, format=format)
            cur = graph.value(predicate=RDF.type, object=namespaces['hydra'].PagedCollection)
            next_page = graph.value(subject=cur, predicate=namespaces['hydra'].nextPage)
            page = 0
            while next_page:
                page += 1
                if page % 10 == 0:
                    logger.debug('Processed pages:' + str(page))

                p = str(next_page)
                g = rdflib.Graph()
                g.parse(p, format=format)
                next_page = g.value(subject=URIRef(next_page), predicate=namespaces['hydra'].nextPage)
                graph.parse(p, format=format)

            logger.debug('Total pages:' + str(page))
            logger.info('Fetching finished')

            for d in graph.subjects(RDF.type, DCAT.Dataset):
                quality.add_quality_measures(d, graph, activity)


class DataGouvFr(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, activity, dcat=True):

        api = urllib.parse.urljoin(portal_api, '/api/1/datasets/?page_size=100')
        processed = set([])

        with no_ssl_verification():
            while True:
                resp = requests.get(api, verify=False)
                if resp.status_code != requests.codes.ok:
                    # TODO wait? appropriate message
                    pass

                res = resp.json()
                # returns a list of datasets
                if not res or 'data' not in res:
                    break
                for datasetJSON in res['data']:
                    if 'id' not in datasetJSON:
                        continue

                    datasetID = datasetJSON['id']
                    if datasetID not in processed:
                        processed.add(datasetID)
                        dataset_ref = graph_from_data_gouv_fr(graph, datasetJSON, portal_api)
                        graph.add((portal_ref, DCAT.dataset, dataset_ref))
                        quality.add_quality_measures(dataset_ref, graph, activity)

                        if len(processed) % 1000 == 0:
                            logger.info("ProgressDSFetch: " + portal_api + ", processed= " + str(len(processed)))
                if 'next_page' in res and res['next_page']:
                    api = res['next_page']
                else:
                    break
            # TODO store total len(processed)


def getPackageList(apiurl):
    """ Try api 3 and api 2 to get the full package list"""
    ex =None

    status=200
    package_list=set([])
    try:
        with no_ssl_verification():
            session = requests.Session()
            session.verify = False
            api = ckanapi.RemoteCKAN(apiurl, get_only=True, session=session)

            start=0
            steps=1000
            while True:
                p_l = api.action.package_list(limit=steps, offset=start)
                if p_l:
                    c=len(package_list)
                    steps= c if start==0 else steps
                    package_list.update(p_l)
                    if c == len(package_list):
                        #no new packages
                        break
                    start+=steps
                else:
                    break
    except Exception as e:
        logger.error("getPackageListRemoteCKAN: " + str(e))
        ex = e

    ex1=None
    try:
        with no_ssl_verification():
            url = urllib.parse.urljoin(apiurl, "api/2/rest/dataset")
            resp = requests.get(url, verify=False)
            if resp.status_code == requests.codes.ok:
                p_l = resp.json()
                package_list.update(p_l)
            else:
                status = resp.status_code
    except Exception as e:
        logger.error("getPackageListHTTPGet: " + str(e))
        ex1=e

    if len(package_list) == 0:
        if ex1:
            raise ex1
        if ex:
            raise ex
    return package_list, status

def getPackage(apiurl, id):
    try:
        with no_ssl_verification():
            url = urllib.parse.urljoin(apiurl, "api/2/rest/dataset/" + id)
            resp = requests.get(url, verify=False)
            if resp.status_code == requests.codes.ok:
                package = resp.json()
                return package,resp.status_code
            else:
                return None, resp.status_code
    except Exception as ex:
        logger.error("getPackageList: " + str(ex))
        raise ex

