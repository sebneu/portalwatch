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

import logging
logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

from converter.dataset_converter import namespaces, DCAT, convert_socrata, graph_from_opendatasoft, \
    graph_from_data_gouv_fr, CKANConverter
import quality

#from odpw.utils import extras_to_dicts, extras_to_dict
#from odpw.utils.error_handling import ErrorHandler, TimeoutError, getExceptionCode, getExceptionString
#from odpw.utils.timing import progressIndicator, Timer


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
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot):
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
                    logger.warn("CKANPackageSearchFetch", pid=api, error='Internal Server Error. Retrying after waiting time.', errorCode=str(err[1]), attempt=attempt, waiting=self._waiting_time(attempt), rows=rows)
                else:
                    raise e

    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, timeout_attempts=5, timeout=24*60*60):
        starttime=time.time()
        api = ckanapi.RemoteCKAN(portal_api, get_only=True)
        start=0
        rows=1000
        p_steps=1
        total=0
        processed_ids=set([])
        processed_names=set([])

        tstart=time.time()
        try:
            response = api.action.package_search(rows=0)
            total = response["count"]
            PortalSnapshot.datasetcount = total
            p_steps=total/10
            if p_steps ==0:
                p_steps=1

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
                                quality.add_quality_measures(dataset_ref, graph, snapshot)
                                processed_ids.add(datasetID)
                                processed_names.add(datasetJSON['name'])


                                now = time.time()
                                if now-starttime>timeout:
                                    raise TimeoutError("Timeout of "+portal_api+" and "+str(timeout)+" seconds", timeout)
                        except Exception as e:
                            logger.error("CKANDSFetchDatasetBatchError", portal=portal_api, dataset=datasetID, exception=e, exc_info=True)
                    rows = min([int(rows*1.2),1000])
                else:
                    break
        except TimeoutError as e:

            raise e
        except Exception as e:
            logger.error("CKANDSFetchBatchError", portal=portal_api, exception=e)

        if len(processed_ids) != total:
            logger.info("Not all datasets processed", fetched=len(processed_ids), total=total)

            try:
                package_list, status = getPackageList(portal_api)
                if total >0 and len(package_list) !=total:
                    logger.info("PackageList_COUNT", total=total, portal=portal_api, pl=len(package_list))
                #len(package_list)
                tt=len(package_list)
                if total==0:
                    PortalSnapshot.datasetcount=tt
                p_steps=tt/100
                if p_steps == 0:
                    p_steps=1
                p_count=0
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
                                quality.add_quality_measures(dataset_ref, graph, snapshot)
                                if entity not in processed_ids:
                                    processed_ids.add(entity)
                        except Exception as e:
                            logger.error('fetchDS', exception=e,portal=portal_api, did=entity)

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
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot):
        api = urllib.parse.urljoin(portal_api, '/api/')
        page = 1
        processed=set([])

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
                    quality.add_quality_measures(dataset_ref, graph, snapshot)
                    processed.add(datasetID)

                    if len(processed) % 1000 == 0:
                        logger.info("ProgressDSFetch", portal=portal_api, processed=len(processed))
            page += 1
        PortalSnapshot.datasetcount = len(processed)


class OpenDataSoft(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot):
        start=0
        rows=10000
        processed=set([])

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
                        quality.add_quality_measures(dataset_ref, graph, snapshot)
                        processed.add(datasetID)

                        if len(processed) % 1000 == 0:
                            logger.info("ProgressDSFetch", portal=portal_api, processed=len(processed))
            else:
                break
        PortalSnapshot.datasetcount = len(processed)


class XMLDCAT(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot):
        graph = rdflib.Graph()
        graph.parse(portal_api, format="xml")

        for d in graph.subjects(RDF.type, DCAT.Dataset):
            quality.add_quality_measures(d, graph, snapshot)

        PortalSnapshot.datasetcount = len(processed)


class SPARQL(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot):
        url = portal_api + "?format=text/turtle&query="
        query = """
        construct {?dataset a dcat:Dataset}  {
            ?dataset a dcat:Dataset.
        }
        """

        limit = 10000
        offset = 0
        download_url = url + urllib.parse.quote(query + " OFFSET " + str(offset) + " LIMIT " + str(limit))

        graph.parse(download_url, format='ttl')

        for dataset_uri in graph.subjects(RDF.type, DCAT.Dataset):
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

            quality.add_quality_measures(dataset_uri, graph, snapshot)
            offset = offset + limit


class CKANDCAT(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, format="ttl"):
        logger.debug('Fetching CKAN portal via RDF endpoint: ' + portal_api)

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
            quality.add_quality_measures(d, graph, snapshot)


class DataGouvFr(PortalProcessor):
    def fetchAndConvertToDCAT(self, graph, portal_ref, portal_api, snapshot, dcat=True):
        api = urllib.parse.urljoin(portal_api, '/api/1/datasets/?page_size=100')
        processed = set([])

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
                    quality.add_quality_measures(dataset_ref, graph, snapshot)

                    if len(processed) % 1000 == 0:
                        logger.info("ProgressDSFetch", portal=portal_api, processed=len(processed))
            if 'next_page' in res and res['next_page']:
                api = res['next_page']
            else:
                break
        PortalSnapshot.datasetcount = len(processed)


def getPackageList(apiurl):
    """ Try api 3 and api 2 to get the full package list"""
    ex =None

    status=200
    package_list=set([])
    try:
        api = ckanapi.RemoteCKAN(apiurl, get_only=True)

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
        logger.error("getPackageListRemoteCKAN", exception=e, exc_info=True, apiurl=apiurl)
        ex = e

    ex1=None
    try:
        url = urllib.parse.urljoin(apiurl, "api/2/rest/dataset")
        resp = requests.get(url, verify=False)
        if resp.status_code == requests.codes.ok:
            p_l = resp.json()
            package_list.update(p_l)
        else:
            status = resp.status_code
    except Exception as e:
        logger.error("getPackageListHTTPGet", exception=e, exc_info=True,apiurl=apiurl)
        ex1=e

    if len(package_list) == 0:
        if ex1:
            raise ex1
        if ex:
            raise ex
    return package_list, status

def getPackage(apiurl, id):
    try:
        url = urllib.parse.urljoin(apiurl, "api/2/rest/dataset/" + id)
        resp = requests.get(url, verify=False)
        if resp.status_code == requests.codes.ok:
            package = resp.json()
            return package,resp.status_code
        else:
            return None, resp.status_code
    except Exception as ex:
        logger.error("getPackageList", exception=ex, id=id, apiurl=apiurl)
        raise ex

