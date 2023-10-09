import glob
import requests
import json
from tqdm import tqdm
from lxml.etree import XMLParser
from lxml import etree as ET
from rdflib import Graph, URIRef, Namespace, Dataset, plugin, ConjunctiveGraph
from rdflib.store import Store
from rdflib.namespace import DCTERMS, VOID
from acdh_cidoc_pyutils.namespaces import CIDOC, FRBROO


NSMAP_RDF = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xml:base": "https://sk.acdh.oeaw.ac.at/model#",
    "frbroo": "https://cidoc-crm.org/frbroo/sites/default/files/FRBR2.4-draft.rdfs#",
    "crm": "http://www.cidoc-crm.org/cidoc-crm/",
    "intro": "https://w3id.org/lso/intro/beta202304#",
    "schema": "https://schema.org/",
    "prov": "http://www.w3.org/ns/prov#",
    "dcterms": "http://purl.org/dc/terms/"
}
SK_MODEL_URL = "https://raw.githubusercontent.com/semantic-kraus/sk_general/main/sk_model.owl"
DOMAIN = "https://sk.acdh.oeaw.ac.at/"
SK = Namespace(DOMAIN)
LK = Namespace("https://sk.acdh.oeaw.ac.at/project/legal-kraus")
DW = Namespace("https://sk.acdh.oeaw.ac.at/project/dritte-walpurgisnacht")
FA = Namespace("https://sk.acdh.oeaw.ac.at/project/fackel")

store = plugin.get("Memory", Store)()
project_store = plugin.get("Memory", Store)()


def parse_xml(url):
    p = XMLParser(huge_tree=True)
    response = requests.get(url)
    doc = ET.fromstring(response.content, parser=p)
    return doc


def get_inverse_of(model_doc):
    inverse_of_dict = []
    inverse = model_doc.xpath(".//*[owl:inverseOf]", namespaces=NSMAP_RDF)
    for i, x in tqdm(enumerate(inverse), total=len(inverse)):
        value = x.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"]
        inverseOf = x.xpath("./owl:inverseOf", namespaces=NSMAP_RDF)[0] \
            .attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]
        inverse_of_dict.append([inverseOf, value])
    return inverse_of_dict


def parse_rdf_trig(file):
    print(f"parsing file: {file}")
    d = Dataset()
    d.parse(file, format="trig")
    return d


def parse_rdf_ttl(file):
    print(f"parsing file: {file}")
    g = Graph()
    g.parse(file, format="ttl")
    return g


def query_for_inverse(ttl_input, prop):
    prop = f"<{prop}>"
    query = f"""
    SELECT ?sbj ?obj
    WHERE {{
        ?sbj {prop} ?obj .
    }}"""
    qres = ttl_input.query(query)
    print(len(qres))
    return qres


def create_inverse_dict(query_result):
    props_with_inverse = {}
    for i, row in enumerate(tqdm(query_result, total=len(query_result))):
        sbj = row[0]
        obj = row[1]
        try:
            props_with_inverse[i].append({sbj: obj})
        except KeyError:
            props_with_inverse[i] = []
            props_with_inverse[i].append({sbj: obj})
    return props_with_inverse


def save_dict(dict, file):
    with open(file, "w") as f:
        json.dump(dict, f)
    print(f"saved dict {file}")


def create_triples(dict_result, output, inverse):
    for key, value in dict_result.items():
        print("length values", len(value))
        pred = inverse
        for v in value:
            sbj = list(v.keys())[0]
            obj = list(v.values())[0]
            output.append(
                {"sbj": obj, "pred": pred, "obj": sbj}
            )


rdf_files = sorted(glob.glob("./rdf/*/*.ttl"))
lookup_dict = get_inverse_of(parse_xml(SK_MODEL_URL))

for file in tqdm(rdf_files, total=len(rdf_files)):
    ttl = parse_rdf_ttl(file)
    all_inverse_triples = []
    for x in tqdm(lookup_dict, total=len(lookup_dict)):
        inverse_of = x[0]
        inverse = x[1]
        qres = query_for_inverse(ttl, inverse_of)
        dict_result = create_inverse_dict(qres)
        if dict_result is not None:
            create_triples(dict_result, all_inverse_triples, inverse)
    if len(all_inverse_triples) != 0:
        unique_triples = [dict(t) for t in {tuple(d.items()) for d in all_inverse_triples}]
        trig_path = file.replace(".ttl", ".trig")
        project_path = file.split("/")[2]
        if project_path == "lk":
            project_uri = URIRef(f"{SK}project/legal-kraus")
            prefix = "lk"
            ns = LK
        elif project_path == "fa":
            project_uri = URIRef(f"{SK}project/fackel")
            prefix = "fa"
            ns = FA
        elif project_path == "dw":
            project_uri = URIRef(f"{SK}project/dritte-walpurgisnacht")
            prefix = "dw"
            ns = DW
        g = Graph(store=project_store, identifier=project_uri)
        g.bind(prefix, ns)
        g.bind("dct", DCTERMS)
        g.bind("void", VOID)
        g.bind("sk", SK)
        g.bind("cidoc", CIDOC)
        g.bind("frbroo", FRBROO)
        g.parse(trig_path, format="trig")
        for triple in unique_triples:
            s = URIRef(triple["sbj"])
            p = URIRef(triple["pred"])
            o = URIRef(triple["obj"])
            g.add((s, p, o))
        print("saved file: ", file)
        save_dict(unique_triples, f"{file.replace('.ttl', '')}.json")

print("saving combined graph")
g_all = ConjunctiveGraph(store=project_store)
g_all.serialize("rdf/sk_fa_m_combined.trig", format="trig")
print("done")
