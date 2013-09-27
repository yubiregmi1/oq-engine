#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains converter classes working on nodes of kind

- vulnerabilitymodel
- fragilitymodel
- exposuremodel
- gmfset
- gmfcollection

Each converter has three methods get_fields, build_node and build_tables.
"""
import csv
import warnings
import itertools
from openquake.nrmllib.node import node_copy, Node, node_to_xml
from openquake.nrmllib import InvalidFile
from abc import ABCMeta, abstractmethod


# A write-only table, essentially the opposite of the read-only
# tables in the nrmllib.tables module.
class EdiTable(object):
    """
    Given a triple suffix, metadata and data matrix returns a sequence yielding
    dictionaries when iterated over. This kind of table keeps everything in
    memory and it is used in the conversion NRML -> CSV. It is the conversion
    CSV -> NRML which is lazy (and does not use this function).
    The suffix is a string used as a suffix in the name of the .csv and .mdata
    files associated to the table, which are generated when the .save method
    is called.
    """
    def __init__(self, suffix, metadata, matrix):
        self.suffix = suffix
        self.metadata = metadata
        self.rows = matrix

    @property
    def fieldnames(self):
        return converter(self.metadata).get_fields()

    def __iter__(self):
        """Yield a record dictionary for each row"""
        for row in self.rows:
            yield dict(zip(self.fieldnames, row))

    def __getitem__(self, i):
        """Return the underlying rows"""
        return self.rows[i]

    def __len__(self):
        """The number of rows of the table"""
        return len(self.rows)

    def save(self, basename):
        """
        Save the table as a pair of files .mdata and .csv.

        :param basename: pathname where to save the table
        :returns: the .mdata and .csv filenames (with suffix)
        """
        name = basename + ('__' + self.suffix if self.suffix else '')
        with open(name + '.mdata', 'w') as mdatafile, \
                open(name + '.csv', 'w') as csvfile:
            # save metadata
            node_to_xml(self.metadata, mdatafile)
            # save data
            cw = csv.writer(csvfile)
            cw.writerow(self.fieldnames)
            cw.writerows(self.rows)
        return mdatafile.name, csvfile.name


def mkgetter(name, ref):
    dic = {}
    s = 'def _get_%s(self): return self.%s' % (name, ref)
    exec(s, dic)
    return dic['_get_' + name]


def mksetter(name, ref):
    dic = {}
    s = 'def _set_%s(self, value): self.%s = value' % (name, ref)
    exec(s, dic)
    return dic['_set_' + name]


def no_getter(self):
    raise NotImplementedError


def no_setter(self, value):
    raise NotImplementedError


class PropertyList(object):
    """
    """
    def __init__(self, *namerefs):
        def __getitem__(rec, i):
            if isinstance(i, str):
                i = rec.name2index[i]
            return rec.getters[i](rec)

        def __setitem__(rec, i, v):
            if isinstance(i, str):
                i = rec.name2index[i]
            rec.setters[i](rec, v)

        def __len__(rec):
            return len(rec.fields)

        self.dict = dict(
            fields=[],
            name2index={},
            getters=[],
            setters=[],
            __getitem__=__getitem__,
            __setitem__=__setitem__,
            __len__=__len__)

        for name, ref in namerefs:
            self.add(name, ref)

    def add(self, field, ref, mode='rw'):
        getter = mkgetter(field, ref) if 'r' in mode else no_getter
        setter = mksetter(field, ref) if 'w' in mode else no_setter
        self.dict['getters'].append(getter)
        self.dict['setters'].append(setter)
        self.dict['fields'].append(field)
        self.dict['name2index'][field] = len(self.dict['fields'])

    def attach(self, cls):
        for k, v in self.dict.iteritems():
            setattr(cls, k, v)


class BaseConverter(object):
    """
    Abstract base class. Each converter takes a node in input and has methods
    get_fields, build_tables and build_node.
    """
    __metaclass__ = ABCMeta

    def __init__(self, node):
        self.node = node

    @abstractmethod
    def get_fields(self):
        """Return the CSV fields by parsing the metadata node"""

    @abstractmethod
    def build_tables(self):
        """Convert the node into a list of table objects"""

    @abstractmethod
    def build_node(self, tables):
        """Convert a list of tables objects into a full node"""


def converter(node):
    """
    Given a node with the right tag, return the corresponding Converter
    instance. For example, a node with tag exposureModel returns an
    instance of ExposureModel.
    """
    name = node.tag[0].upper() + node.tag[1:]
    clsname = name if name.endswith('Model') else name + 'Model'
    cls = globals()[clsname]
    return cls(node)


def _floats_to_text(fname, colname, records):
    """
    A convenience function for reading floats from columns in a
    CSV file.

    :param fname: the pathname of the file
    :param colname: the name of the column
    :param records: a list of dictionaries with the CSV data
    """
    floats = []
    for i, r in enumerate(records, 1):
        col = r[colname]
        try:
            float(col)
        except (ValueError, TypeError) as e:
            raise InvalidFile('%s:row #%d:%s:%s' % (
                              fname, i, colname, e))
        floats.append(col)
    return ' ' .join(floats)


############################# vulnerability #################################

class VulnerabilityModel(BaseConverter):
    """A converter for vulnerabilityModel nodes"""

    def get_fields(self):
        """
        Extract the names of the fields of the CSV file from the node.
        For instance, if the node contains two vulnerabilityFunctionIDs
        IR and PK there will be 5 fields ['IMT', 'IR.lossRatio',
       'IR.coefficientsVariation', 'PK.lossRatio', 'PK.coefficientsVariation'].
        """
        fieldnames = ['IML']
        for vf in self.node.discreteVulnerabilitySet.getnodes(
                'discreteVulnerability'):
            vf_id = vf['vulnerabilityFunctionID']
            lossRatio, coefficientsVariation = vf
            fieldnames.append('%s.%s' % (vf_id, lossRatio.tag))
            fieldnames.append('%s.%s' % (vf_id, coefficientsVariation.tag))
        return fieldnames

    def build_tables(self):
        """
        Yield a table for each vulnerabilitySetID in the model.
        """
        node = self.node
        for vset in self.node.getnodes('discreteVulnerabilitySet'):
            vset = node_copy(vset)
            metadata = Node(node.tag, node.attrib, nodes=[vset])
            matrix = [vset.IML.text.split()]  # data in transposed form
            vset.IML.text = None
            for vf in vset.getnodes('discreteVulnerability'):
                matrix.append(vf.lossRatio.text.split())
                matrix.append(vf.coefficientsVariation.text.split())
                vf.lossRatio.text = None
                vf.coefficientsVariation.text = None
            yield EdiTable(vset['vulnerabilitySetID'], metadata, zip(*matrix))

    def build_node(self, tables):
        """
        Build a full vulnerability Node from a group of tables.
        """
        vsets = []
        for table in tables:
            md = table.metadata
            fname = table.name
            rows = list(table)
            if not rows:
                warnings.warn('No data in %s' % table.name)
            vset = md.discreteVulnerabilitySet
            for vf in vset.getnodes('discreteVulnerability'):
                vf_id = vf['vulnerabilityFunctionID']
                for node in vf:  # lossRatio, coefficientsVariation
                    node.text = _floats_to_text(
                        fname, '%s.%s' % (vf_id, node.tag),  rows)
            vset.IML.text = _floats_to_text(fname, 'IML', rows)
            vsets.append(vset)
        return Node('vulnerabilityModel', nodes=vsets)

PropertyList(
    ('vulnerabilitySetID',
     "node.discreteVulnerabilitySet['vulnerabilitySetID']"),
    ('assetCategory',
     "node.discreteVulnerabilitySet['assetCategory']"),
    ('lossCategory',
     "node.discreteVulnerabilitySet['lossCategory']"),
    ('IMT',
     "node.discreteVulnerabilitySet.IML['IMT']"),
    ('vulnerabilityFunctionID',
     "node.discreteVulnerabilitySet.discreteVulnerability"
     "['vulnerabilityFunctionID']"),
    ('probabilisticDistribution',
     "node.discreteVulnerabilitySet.discreteVulnerability"
     "['probabilisticDistribution']"),
).attach(VulnerabilityModel)


############################# fragility #################################

class FragilityModel(BaseConverter):
    """A converter for fragilityModel nodes"""

    def get_fields(self):
        """
        Extract the names of the fields of the CSV file from the model.
        For instance, if the model is discrete and has limit states minor,
        moderate, severe and collapse, returns

        ['IML', 'minor', 'moderate', 'severe', 'collapse']

        If the model is continuous and has limit states slight, moderate,
        extensive and complete returns

        ['param', 'slight', 'moderate', 'extensive', 'complete']
        """
        a = self.node.attrib
        if a['format'] == 'discrete':
            return ['IML'] + self.node.limitStates.text.split()
        elif a['format'] == 'continuous':
            return ['param'] + self.node.limitStates.text.split()

    def build_tables(self):
        """
        Yield a table for each Fragility Function Set (ffs) keyed by
        the ordinal of the set, starting from 1. Here is an example
        of a table for a discrete model::

          IML,minor,moderate,severe,collapse
          7,0.0,0.0,0.0,0.0
          8,0.09,0.00,0.00,0.00
          9,0.56,0.04,0.00,0.00

        Here is an example for a continuous model::

          param,slight,moderate,extensive,complete
          mean,11.19,27.98,48.05,108.9
          stddev,8.27,20.677,42.49,123.7
        """
        node = self.node
        format = node['format']
        limitStates = node.limitStates.text.split()
        for i, ffs in enumerate(node.getnodes('ffs'), 1):
            md = Node('fragilityModel', node.attrib,
                      nodes=[node.description, node.limitStates])
            if format == 'discrete':
                matrix = [ffs.IML.text.split()]  # data in transposed form
                for ls, ffd in zip(limitStates, ffs.getnodes('ffd')):
                    assert ls == ffd['ls'], 'Expected %s, got %s' % (
                        ls, ffd['ls'])
                    matrix.append(ffd.poEs.text.split())
            elif format == 'continuous':
                matrix = ['mean stddev'.split()]
                for ls, ffc in zip(limitStates, ffs.getnodes('ffc')):
                    assert ls == ffc['ls'], 'Expected %s, got %s' % (
                        ls, ffc['ls'])
                    matrix.append([ffc.params['mean'], ffc.params['stddev']])
            else:
                raise ValueError('Invalid format %r' % format)
            md.append(Node('ffs', ffs.attrib))
            md.ffs.append(ffs.taxonomy)
            md.ffs.append(Node('IML', ffs.IML.attrib))
            # append the two nodes taxonomy and IML
            yield EdiTable(str(i), md, zip(*matrix))

    def build_node(self, tables):
        """
        Build a full fragility Node from a group of tables.
        """
        fm = node_copy(tables[0].metadata)
        del fm[2]  # ffs node
        discrete = fm.attrib['format'] == 'discrete'
        for table in tables:
            rows = list(table)
            ffs = node_copy(table.metadata.ffs)
            if discrete:
                ffs.IML.text = _floats_to_text(table.name, 'IML', rows)
            for ls in fm.limitStates.text.split():
                if discrete:
                    poes = _floats_to_text(table.name, ls, rows)
                    ffs.append(Node('ffd', dict(ls=ls),
                                    nodes=[Node('poEs', {}, poes)]))
                else:
                    mean, stddev = rows  # there are exactly two rows
                    params = dict(mean=mean[ls], stddev=stddev[ls])
                    ffs.append(Node('ffc', dict(ls=ls),
                                    nodes=[Node('params', params)]))
            fm.append(ffs)
        return fm


class FragilityModelDiscrete(FragilityModel):
    pass

PropertyList(
    ('format', "node['format']"),
    ('description', "node.description.text"),
    ('limitStates', "node,limitStates.text"),
    ('taxonomy', 'node.ffs.taxonomy.text'),
    ('IMT', "node.ffs.IML['IMT']"),
    ('imlUnit', "node.ffs.IML['imlUnit']"),
).attach(FragilityModelDiscrete)


class FragilityModelContinuous(FragilityModel):
    pass

PropertyList(
    ('format', "node['format']"),
    ('description', "node.description.text"),
    ('limitStates', "node.limitStates.text"),
    ('noDamageLimit', "node.ffs['noDamageLimit']"),
    ('type', "node.ffs['type']"),
    ('taxonomy', 'node.ffs.taxonomy.text'),
    ('IMT', "node.ffs.IML['IMT']"),
    ('imlUnit', "node.ffs.IML['imlUnit']"),
    ('maxIML', "node.ffs.IML['maxIML']"),
    ('minIML', "node.ffs.IML['minIML']"),
).attach(FragilityModelContinuous)

############################# exposure #################################

COSTCOLUMNS = 'value deductible insuranceLimit retrofitted'.split()
PERIODS = 'day', 'night', 'transit', 'early morning', 'late afternoon'
## TODO: the occupancy periods should be inferred from the NRML file,
## not hardcoded, exactly as the cost types


def getcosts(asset, costcolumns):
    """
    Extracts different costs from an asset node. If a cost is not available
    returns an empty string for it. Returns a list with the same length of
    the cost columns.
    """
    row = dict.fromkeys(costcolumns, '')
    for cost in asset.costs:
        for kind in COSTCOLUMNS:
            row['%s.%s' % (cost['type'], kind)] = cost.attrib.get(kind, '')
    return [row[cc] for cc in costcolumns]


def getcostcolumns(costtypes):
    """
    Extracts the kind of costs from a CostTypes node. Those will correspond
    to columns names in the .csv representation of the exposure.
    """
    cols = []
    for cost in costtypes:
        for kind in COSTCOLUMNS:
            cols.append('%s.%s' % (cost['name'], kind))
    return cols


def getoccupancies(asset):
    """
    Extracts the occupancies from an asset node.
    """
    dic = dict(('occupancy.' + occ['period'], occ['occupants'])
               for occ in asset.occupancies)
    return [dic.get('occupancy.%s' % period, '') for period in PERIODS]


def assetgenerator(records, costtypes):
    """
    Convert records into asset nodes.

    :param records: an iterable over dictionaries
    :param costtypes: list of dictionaries with the cost types

    :returns: an iterable over Node objects describing exposure assets
    """
    for record in records:
        nodes = [Node('location', dict(lon=record['lon'], lat=record['lat']))]
        costnodes = []
        for costtype in costtypes:
            keepnode = True
            attr = dict(type=costtype['name'])
            for costcol in COSTCOLUMNS:
                value = record['%s.%s' % (costtype['name'], costcol)]
                if value:
                    attr[costcol] = value
                elif costcol == 'value':
                    keepnode = False  # ignore costs without value
            if keepnode:
                costnodes.append(Node('cost', attr))
        if costnodes:
            nodes.append(Node('costs', {}, nodes=costnodes))
        has_occupancies = any('occupancy.%s' % period in record
                              for period in PERIODS)
        if has_occupancies:
            occ = []
            for period in PERIODS:
                occupancy = record['occupancy.' + period]
                if occupancy:
                    occ.append(Node('occupancy',
                                    dict(occupants=occupancy, period=period)))
            nodes.append(Node('occupancies', {}, nodes=occ))
        attr = dict(id=record['id'], number=record['number'],
                    taxonomy=record['taxonomy'])
        if 'area' in record:
            attr['area'] = record['area']
        yield Node('asset', attr, nodes=nodes)


class ExposureModel(BaseConverter):
    """A converter for exposureModel nodes"""

    def get_fields(self):
        """
        Extract the names of the fields of the CSV file from the metadata file

        :param self: metadata node object
        """
        node = self.node
        fieldnames = ['id', 'taxonomy', 'lon', 'lat', 'number']
        if node['category'] == 'buildings':
            fieldnames.append('area')
            costcolumns = getcostcolumns(node.conversions.costTypes)
            fieldnames.extend(
                costcolumns + ['occupancy.%s' % period for period in PERIODS])
        return fieldnames

    def build_tables(self):
        """
        Yield a single table object. For population exposure a table
        has a form like

          id,taxonomy,lon,lat,number
          asset_01,IT-PV,9.15000,45.16667,7
          asset_02,IT-CE,9.15333,45.12200,7

        whereas for building has a form like

          id,taxonomy,lon,lat,number,area,cost.value,..., occupancy.day
          asset_01,RC/DMRF-D/LR,9.15000,45.16667,7,120,40,.5,...,20
          asset_02,RC/DMRF-D/HR,9.15333,45.12200,7,119,40,,,...,20
          asset_03,RC/DMRF-D/LR,9.14777,45.17999,5,118,,...,,5

        with a variable number of columns depending on the metadata.
        """
        node = self.node
        metadata = Node('exposureModel', node.attrib, nodes=[node.description])
        if node['category'] == 'population':
            data = ([asset['id'], asset['taxonomy'],
                     asset.location['lon'], asset.location['lat'],
                     asset['number']]
                    for asset in node.assets)
        elif node['category'] == 'buildings':
            metadata.append(node.conversions)
            costcolumns = getcostcolumns(node.conversions.costTypes)
            data = ([asset['id'], asset['taxonomy'],
                     asset.location['lon'], asset.location['lat'],
                     asset['number'], asset['area']]
                    + getcosts(asset, costcolumns)
                    + getoccupancies(asset)
                    for asset in node.assets)
        metadata.append(Node('assets'))
        yield EdiTable('', metadata, data)

    def build_node(self, tables):
        """
        Build a Node object containing a full exposure from a set
        of tables. The assets are lazily read.
        """
        assert len(tables) == 1, 'Exposure files must contain a single node'
        table = tables[0]
        em = node_copy(table.metadata)
        ctypes = em.conversions.costTypes \
            if em.attrib['category'] == 'buildings' else []
        em.assets.nodes = assetgenerator(table, ctypes)
        return em


################################# gmf ##################################

class GmfSetModel(BaseConverter):
    """A converter for gmfSet nodes"""

    def get_fields(self):
        """
        The fields in a GMF CSV file (lon, lat, gmv)

        :param self: metadata node object (for API compatibility, but ignored)
        """
        return ['lon', 'lat', 'gmv']

    def build_tables(self):
        """
        Yield a table for each gmf node. The table has a form like

          lon,lat,gmv
          0.0,0.0,0.2
          1.0,0.0,1.4
          0.0,1.0,0.6
        """
        node = self.node
        for gmf in node.getnodes('gmf'):
            imt = gmf['IMT']
            if imt == 'SA':
                imt += '(%s)' % gmf['saPeriod']
            metadata = Node('gmfSet', node.attrib,
                            nodes=[Node('gmf', gmf.attrib)])
            data = ((n['lon'], n['lat'], n['gmv']) for n in gmf)
            yield EdiTable(imt, metadata, data)

    def build_node(self, tables):
        """
        Build a gmfSet node from a list of tables.
        """
        assert len(tables) > 1
        gmfcoll = Node('gmfSet')
        for table in tables:
            md = table.metadata
            gmf = node_copy(md.gmf)
            for record in table:
                gmf.append(Node('node', record))
            gmfcoll.append(gmf)
        return gmfcoll


PropertyList(
    ("IMT", "node.gmf['IMT']"),
    ("saPeriod", "node.gmf['saPeriod']"),
    ("saDamping", "node.gmf['saDamping']"),
).attach(GmfSetModel)


class GmfCollectionModel(BaseConverter):
    """A converter for gmfCollection nodes"""

    def get_fields(self):
        """
        The fields in a GMF CSV file ['lon', 'lat', 'gmv']
        """
        return ['lon', 'lat', 'gmv']

    def build_tables(self):
        """
        Yield a table for each gmf node. The table has a form like

          lon,lat,gmv
          0.0,0.0,0.2
          1.0,0.0,1.4
          0.0,1.0,0.6
        """
        node = self.node
        for gmfset in node.getnodes('gmfSet'):
            for gmf in gmfset.getnodes('gmf'):
                rup = gmf['ruptureId']
                imt = gmf['IMT']
                if imt == 'SA':
                    imt += '(%s)' % gmf['saPeriod']
                metadata = Node('gmfCollection', node.attrib)
                gs = Node('gmfSet', gmfset.attrib,
                          nodes=[Node('gmf', gmf.attrib)])
                metadata.append(gs)
                data = ((n['lon'], n['lat'], n['gmv']) for n in gmf)
                yield EdiTable(imt + ',' + rup, metadata, data)

    def build_node(self, tables):
        """
        Build a gmfCollection node from a list of tables.
        """
        assert len(tables) >= 1
        md = tables[0].metadata
        gmfcoll = Node('gmfCollection', dict(
            sourceModelTreePath=md.attrib['sourceModelTreePath'],
            gsimTreePath=md.attrib['gsimTreePath']))

        def get_ses_id(table):
            return table.metadata.gmfSet.attrib['stochasticEventSetId']
        for ses_id, tablegroup in itertools.groupby(tables, get_ses_id):
            tablelist = list(tablegroup)
            gmfset = Node('gmfSet', tablelist[0].metadata.gmfSet.attrib)
            for table in tablelist:
                gmf = Node('gmf', table.metadata.gmfSet.gmf.attrib,
                           nodes=[Node('node', record) for record in table])
                gmfset.append(gmf)
            gmfcoll.append(gmfset)
        return gmfcoll

PropertyList(
    ("gsimTreePath", "node['gsimTreePath']"),
    ("sourceModelTreePath", "node['sourceModelTreePath']"),
    ("investigationTime", "node.gmfSet['investigationTime']"),
    ("stochasticEventSetId", "node.gmfSet['stochasticEventSetId']"),
    ("IMT", "node.gmfSet.gmf['IMT']"),
    ("ruptureId", "node.gmfSet.gmf['ruptureId']"),
).attach(GmfCollectionModel)
