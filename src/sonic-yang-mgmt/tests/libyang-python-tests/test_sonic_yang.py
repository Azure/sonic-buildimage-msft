import sys
import os
import pytest
import sonic_yang as sy
import json
import glob
import logging
from ijson import items as ijson_itmes

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("YANG-TEST")
log.setLevel(logging.INFO)
log.addHandler(logging.NullHandler())

def _load_test_data():
    test_file = "./tests/libyang-python-tests/test_SonicYang.json"
    with open(test_file) as data_file:
        return json.load(data_file)


def _create_yang_s(data):
    yang_dir = str(data['yang_dir'])
    yang_files = glob.glob(yang_dir+"/*.yang")
    yang_s = sy.SonicYang(yang_dir)
    yang_s._load_data_model(yang_dir, yang_files, [str(data['data_file'])])
    yang_s.validate_data_tree()
    return yang_s


class Test_SonicYang_Loading(object):

    @pytest.fixture(autouse=True, scope='class')
    def data(self):
        return _load_test_data()

    @pytest.fixture(autouse=True)
    def yang_s(self, data):
        yang_dir = str(data['yang_dir'])
        yang_s = sy.SonicYang(yang_dir)
        return yang_s

    def load_yang_model_file(self, yang_s, yang_dir, yang_file, module_name):
        yfile = yang_dir + yang_file
        try:
            yang_s._load_schema_module(str(yfile))
        except Exception as e:
            print(e)
            raise

    #test load and get yang module
    def test_load_yang_model_files(self, data, yang_s):
        yang_dir = data['yang_dir']
        for module in data['modules']:
            file = str(module['file'])
            module = str(module['module'])

            self.load_yang_model_file(yang_s, yang_dir, file, module)
            assert yang_s._get_module(module) is not None

    #test load non-exist yang module file
    def test_load_invalid_model_files(self, data, yang_s):
        yang_dir = data['yang_dir']
        file = "invalid.yang"
        module = "invalid"

        with pytest.raises(Exception):
             assert self.load_yang_model_file(yang_s, yang_dir, file, module)

    def test_load_module_str_name(self, data, yang_s):
        with open(os.path.join(data['yang_dir'], 'test-acl.yang')) as f:
            content = f.read()
        assert yang_s.load_module_str_name(content) == "test-acl"
        assert yang_s._get_module("test-acl") is not None

    @pytest.mark.parametrize("content", ["", "not a YANG module"])
    def test_load_module_str_name_invalid(self, yang_s, content):
        with pytest.raises(RuntimeError):
            yang_s.load_module_str_name(content)

    #test load yang modules in directory
    def test_load_yang_model_dir(self, data, yang_s):
        yang_dir = data['yang_dir']
        yang_s._load_schema_modules(str(yang_dir))

        for module_name in data['modules']:
            assert yang_s._get_module(str(module_name['module'])) is not None

    #test load yang modules and data files
    def test_load_yang_model_data(self, data, yang_s):
        yang_dir = str(data['yang_dir'])
        yang_files = glob.glob(yang_dir+"/*.yang")
        data_file = str(data['data_file'])
        data_merge_file = str(data['data_merge_file'])

        data_files = []
        data_files.append(data_file)
        data_files.append(data_merge_file)
        print(yang_files)
        yang_s._load_data_model(yang_dir, yang_files, data_files)

        #validate the data tree from data_merge_file is loaded
        for node in data['merged_nodes']:
            xpath = str(node['xpath'])
            value = str(node['value'])
            val = yang_s._find_data_node_value(xpath)
            assert str(val) == str(value)

    #test load data file
    def test_load_data_file(self, data, yang_s):
        data_file = str(data['data_file'])
        yang_s._load_schema_modules(str(data['yang_dir']))
        yang_s._load_data_file(data_file)


class Test_SonicYang(object):
    # Mutating tests must not change the data seen by dependency lookups.
    @pytest.fixture(autouse=True, scope='class')
    def data(self):
        return _load_test_data()

    @pytest.fixture(autouse=True)
    def yang_s(self, data):
        return _create_yang_s(data)

    """
        Get the JSON input based on func name
        and return jsonInput
    """
    def readIjsonInput(self, yang_test_file, test):
        try:
            # load test specific Dictionary, using Key = func
            # this is to avoid loading very large JSON in memory
            print(" Read JSON Section: " + test)
            jInput = ""
            with open(yang_test_file, 'rb') as f:
                jInst = ijson_itmes(f, test)
                for it in jInst:
                    jInput = jInput + json.dumps(it)
        except Exception as e:
            print("Reading Ijson failed")
            raise(e)
        return jInput

    #test_validate_data_tree():
    def test_validate_data_tree(self, data, yang_s):
        yang_s.validate_data_tree()

    #test find node
    def test_find_node(self, data, yang_s):
        for node in data['data_nodes']:
            expected = node['valid']
            xpath = str(node['xpath'])
            dnode = yang_s._find_data_node(xpath)

            if(expected == "True"):
                 assert dnode is not None
                 assert dnode.path() == xpath
            else:
                 assert dnode is None

    #test add node
    def test_add_node(self, data, yang_s):
        for node in data['new_nodes']:
            xpath = str(node['xpath'])
            value = node['value']
            yang_s._add_data_node(xpath, str(value))

            data_node = yang_s._find_data_node(xpath)
            assert data_node is not None

    #test find node value
    def test_find_data_node_value(self, data, yang_s):
       for node in data['node_values']:
            xpath = str(node['xpath'])
            value = str(node['value'])
            print(xpath)
            print(value)
            val = yang_s._find_data_node_value(xpath)
            assert str(val) == str(value)

    #test delete data node
    def test_delete_node(self, data, yang_s):
        for node in data['delete_nodes']:
            xpath = str(node['xpath'])
            yang_s._deleteNode(xpath)

    #test set node's value
    def test_set_datanode_value(self, data, yang_s):
        for node in data['set_nodes']:
            xpath = str(node['xpath'])
            value = node['value']
            yang_s._set_data_node_value(xpath, value)

            val = yang_s._find_data_node_value(xpath)
            assert str(val) == str(value)

    #test list of members
    def test_find_members(self, yang_s, data):
        for node in data['members']:
            members = node['members']
            xpath = str(node['xpath'])
            list = yang_s._find_data_nodes(xpath)
            assert list.sort() == members.sort()

    #get parent xpath
    def test_get_parent_data_xpath(self, yang_s, data):
        for node in data['parents']:
            xpath = str(node['xpath'])
            expected_xpath = str(node['parent'])
            path = yang_s._get_parent_data_xpath(xpath)
            assert path == expected_xpath

    #test find_data_node_schema_xpath
    def test_find_data_node_schema_xpath(self, yang_s, data):
        for node in data['schema_nodes']:
            xpath = str(node['xpath'])
            schema_xpath = str(node['value'])
            path = yang_s._find_data_node_schema_xpath(xpath)
            assert path == schema_xpath

    #test data dependencies
    def test_find_data_dependencies(self, yang_s, data):
        for node in data['dependencies']:
            xpath = str(node['xpath'])
            list = node['dependencies']
            depend = yang_s.find_data_dependencies(xpath)
            assert set(depend) == set(list)
            assert len(depend) == len(set(depend))

    @pytest.mark.parametrize("xpath", [None, "", "/"])
    def test_find_data_dependencies_global(self, yang_s, data, xpath):
        expected = next(node['dependencies'] for node in data['dependencies']
                        if node['xpath'] == "/")
        dependencies = yang_s.find_data_dependencies(xpath)
        assert set(dependencies) == set(expected)
        assert len(dependencies) == len(set(dependencies))

    @pytest.mark.parametrize("xpath", [
        "/test-acl:test-acl/ACL_TABLE/ACL_TABLE_LIST",
        "/test-acl:test-acl/ACL_TABLE/ACL_TABLE_LIST/ACL_TABLE_NAME",
    ])
    def test_find_data_dependencies_multiple_matches(self, yang_s, data, xpath):
        expected = next(node['dependencies'] for node in data['dependencies']
                        if node['xpath'] == "/test-acl:test-acl/ACL_TABLE")
        assert set(yang_s.find_data_dependencies(xpath)) == set(expected)

    @pytest.mark.parametrize("xpath", [
        "/test-port:test-port/PORT/PORT_LIST[port_name='Ethernet9999']",
        "/test-port:test-port/PORT/invalid",
        "invalid[",
    ])
    def test_find_data_dependencies_missing_node(self, yang_s, xpath):
        assert yang_s.find_data_dependencies(xpath) == []

    @pytest.mark.parametrize("xpath", [None, "", "/", "/test-port:test-port/PORT"])
    def test_find_data_dependencies_empty_tree(self, data, xpath):
        yang_s = sy.SonicYang(str(data['yang_dir']))
        assert yang_s.find_data_dependencies(xpath) == []

    #test data dependencies
    def test_find_schema_dependencies(self, yang_s, data):
        for node in data['schema_dependencies']:
            xpath = str(node['xpath'])
            list = node['schema_dependencies']
            depend = yang_s.find_schema_dependencies(xpath)
            assert set(depend) == set(list)

    #test merge data tree
    def test_merge_data_tree(self, data, yang_s):
        data_merge_file = data['data_merge_file']
        yang_dir = str(data['yang_dir'])
        yang_s._merge_data(data_merge_file, yang_dir)
        #yang_s.root.print_mem(ly.LYD_JSON, ly.LYP_FORMAT)

    #test get module prefix
    def test_get_module_prefix(self, yang_s, data):
        for node in data['prefix']:
            xpath = str(node['module_name'])
            expected = node['module_prefix']
            prefix = yang_s._get_module_prefix(xpath)
            assert expected == prefix

    #test get data type
    def test_get_data_type(self, yang_s, data):
        for node in data['data_type']:
            xpath = str(node['xpath'])
            expected = node['data_type']
            expected_type = yang_s._str_to_type(expected)
            data_type = yang_s._get_data_type(xpath)
            assert expected_type == data_type

    def test_get_leafref_type(self, yang_s, data):
        # libyang1 resolves the leafref value_type when merging data.
        yang_s._merge_data(data['data_merge_file'], str(data['yang_dir']))
        for node in data['leafref_type']:
            xpath = str(node['xpath'])
            expected = node['data_type']
            expected_type = yang_s._str_to_type(expected)
            data_type = yang_s._get_leafref_type(xpath)
            assert expected_type == data_type

    def test_get_leafref_path(self, yang_s, data):
        for node in data['leafref_path']:
            xpath = str(node['xpath'])
            expected_path = node['leafref_path']
            path = yang_s._get_leafref_path(xpath)
            assert expected_path == path

    def test_get_leafref_type_schema(self, yang_s, data):
        for node in data['leafref_type_schema']:
            xpath = str(node['xpath'])
            expected = node['data_type']
            expected_type = yang_s._str_to_type(expected)
            data_type = yang_s._get_leafref_type_schema(xpath)
            assert expected_type == data_type

    def test_configdb_path_to_xpath(self, yang_s, data):
        yang_s.loadYangModel()
        for node in data['configdb_path_to_xpath']:
            configdb_path = str(node['configdb_path'])
            schema_xpath = bool(node['schema_xpath'])
            expected = node['xpath']
            received = yang_s.configdb_path_to_xpath(configdb_path, schema_xpath=schema_xpath)
            assert received == expected

    def test_xpath_to_configdb_path(self, yang_s, data):
        yang_s.loadYangModel()
        for node in data['xpath_to_configdb_path']:
            xpath = str(node['xpath'])
            expected = node['configdb_path']
            received = yang_s.xpath_to_configdb_path(xpath)
            assert received == expected

    def test_configdb_path_split(self, yang_s, data):
        def check(path, tokens):
            expected=tokens
            actual=yang_s.configdb_path_split(path)
            assert expected == actual

        check("", [])
        check("/", [])
        check("/token", ["token"])
        check("/more/than/one/token", ["more", "than", "one", "token"])
        check("/has/numbers/0/and/symbols/^", ["has", "numbers", "0", "and", "symbols", "^"])
        check("/~0/this/is/telda", ["~", "this", "is", "telda"])
        check("/~1/this/is/forward-slash", ["/", "this", "is", "forward-slash"])
        check("/\\\\/no-escaping", ["\\\\", "no-escaping"])
        check("////empty/tokens/are/ok", ["", "", "", "empty", "tokens", "are", "ok"])

    def configdb_path_join(self, yang_s, data):
        def check(tokens, path):
            expected=path
            actual=yang_s.configdb_path_join(tokens)
            assert expected == actual

        check([], "/",)
        check([""], "/",)
        check(["token"], "/token")
        check(["more", "than", "one", "token"], "/more/than/one/token")
        check(["has", "numbers", "0", "and", "symbols", "^"], "/has/numbers/0/and/symbols/^")
        check(["~", "this", "is", "telda"], "/~0/this/is/telda")
        check(["/", "this", "is", "forward-slash"], "/~1/this/is/forward-slash")
        check(["\\\\", "no-escaping"], "/\\\\/no-escaping")
        check(["", "", "", "empty", "tokens", "are", "ok"], "////empty/tokens/are/ok")
        check(["~token", "telda-not-followed-by-0-or-1"], "/~0token/telda-not-followed-by-0-or-1")

    """
    This is helper function to load YANG models for tests cases, which works
    on Real SONiC Yang models. Mainly tests  for translation and reverse
    translation.
    """
    @pytest.fixture(autouse=True)
    def sonic_yang_data(self):
        sonic_yang_dir = "/usr/local/yang-models/"
        sonic_yang_test_file = "../sonic-yang-models/tests/files/sample_config_db.json"

        syc = sy.SonicYang(sonic_yang_dir)
        syc.loadYangModel()

        sonic_yang_data = dict()
        sonic_yang_data['yang_dir'] = sonic_yang_dir
        sonic_yang_data['test_file'] = sonic_yang_test_file
        sonic_yang_data['syc'] = syc

        return sonic_yang_data

    def test_validate_yang_models(self, sonic_yang_data):
        '''
        In this test, we validate yang models
        a.) by converting the config as per RFC 7951 using YANG Models,
        b.) by creating data tree using new YANG models and
        c.) by validating config against YANG models.
        Successful execution of these steps can be treated as
        validation of new Yang models.
        '''
        test_file = sonic_yang_data['test_file']
        syc = sonic_yang_data['syc']
        # Currently only 3 YANG files are not directly related to config, along with event YANG models
        # which are: sonic-extension.yang, sonic-types.yang and sonic-bgp-common.yang. Hard coding
        # it right now.
        # event YANG models do not map directly to config_db and are included to NON_CONFIG_YANG_FILES at run time
        # If any more such helper yang files are added, we need to update here.
        EVENT_YANG_FILES = sum(1 for yang_model in syc.yangFiles if 'sonic-events' in yang_model)
        NON_CONFIG_YANG_FILES = 3 + EVENT_YANG_FILES
        # read config
        jIn = self.readIjsonInput(test_file, 'SAMPLE_CONFIG_DB_JSON')
        jIn = json.loads(jIn)
        numTables = len(jIn)
        # load config and create Data tree
        syc.loadData(jIn)
        # check all tables are loaded and config related to all Yang Models is
        # loaded in Data tree.
        assert len(syc.jIn) == numTables
        print("{}:{}".format(len(syc.xlateJson), len(syc.yangFiles)))
        assert len(syc.xlateJson) == len(syc.yangFiles) - NON_CONFIG_YANG_FILES
        # Validate data tree
        validTree = False
        try:
            syc.validate_data_tree()
            validTree = True
        except Exception as e:
            pass
        assert validTree == True

        return

    def test_xlate_rev_xlate(self, sonic_yang_data):
        # In this test, xlation and revXlation is tested with latest Sonic
        # YANG model.
        test_file = sonic_yang_data['test_file']
        syc = sonic_yang_data['syc']

        jIn = self.readIjsonInput(test_file, 'SAMPLE_CONFIG_DB_JSON')
        jIn = json.loads(jIn)
        numTables = len(jIn)

        syc.loadData(jIn)
        # check all tables are loaded and no tables is without Yang Models
        assert len(syc.jIn) == numTables
        assert len(syc.tablesWithOutYang) == 0

        syc.getData()

        if syc.jIn and syc.jIn == syc.revXlateJson:
            print("Xlate and Rev Xlate Passed")
        else:
            print("Xlate and Rev Xlate failed")
            # print for better debugging, in case of failure.
            from jsondiff import diff
            print(diff(syc.jIn, syc.revXlateJson, syntax='symmetric'))
            # make it fail
            assert False == True

        return

    def test_table_with_no_yang(self, sonic_yang_data):
        # in this test, tables with no YANG models must be stored seperately
        # by this library.
        test_file = sonic_yang_data['test_file']
        syc = sonic_yang_data['syc']

        jIn = self.readIjsonInput(test_file, 'SAMPLE_CONFIG_DB_UNKNOWN')

        syc.loadData(json.loads(jIn))

        ty = syc.tablesWithOutYang

        assert (len(ty) and "UNKNOWN_TABLE" in ty)

        return

    def test_special_json_with_yang(self, sonic_yang_data):
        # in this test, we validate unusual json config and check if
        # loadData works successfully
        test_file = sonic_yang_data['test_file']
        syc = sonic_yang_data['syc']

        # read config
        jIn = self.readIjsonInput(test_file, 'SAMPLE_CONFIG_DB_SPECIAL_CASE')
        jIn = json.loads(jIn)

        # load config and create Data tree
        syc.loadData(jIn)

        return

    def test_loaddata_quiet_suppresses_syslog_on_success(self, sonic_yang_data, monkeypatch):
        # With quiet=True, the informational "Try to load Data" sysLog
        # call must not be emitted. Exception path is covered below.
        # monkeypatch.setattr cleanly reverts the instance-level override
        # on teardown so state does not leak across tests.
        test_file = sonic_yang_data['test_file']
        syc = sonic_yang_data['syc']
        jIn = json.loads(self.readIjsonInput(test_file, 'SAMPLE_CONFIG_DB_JSON'))

        calls = []
        monkeypatch.setattr(syc, 'sysLog',
                            lambda *a, **kw: calls.append((a, kw)))

        syc.loadData(jIn, quiet=True)

        msgs = [kw.get('msg', '') for (_a, kw) in calls] + [
            a[0] for (a, _kw) in calls if a
        ]
        assert not any('Try to load Data' in str(m) for m in msgs), \
            "quiet=True must suppress 'Try to load Data' sysLog: {}".format(msgs)
        assert not any('Data Loading Failed' in str(m) for m in msgs), \
            "quiet=True must suppress 'Data Loading Failed' sysLog: {}".format(msgs)

        return

    def test_loaddata_quiet_suppresses_syslog_on_failure(self, sonic_yang_data, monkeypatch):
        # With quiet=True, the LOG_ERR "Data Loading Failed" sysLog call
        # must not be emitted even when parse_data_mem raises. The
        # SonicYangException must still be raised so the caller sees the
        # failure. monkeypatch.setattr cleanly reverts on teardown.
        test_file = sonic_yang_data['test_file']
        syc = sonic_yang_data['syc']
        jIn = json.loads(self.readIjsonInput(test_file, 'SAMPLE_CONFIG_DB_JSON'))

        calls = []

        def _boom(*a, **kw):
            raise RuntimeError('forced parse failure')

        monkeypatch.setattr(syc, 'sysLog',
                            lambda *a, **kw: calls.append((a, kw)))
        monkeypatch.setattr(syc.ctx, 'parse_data_mem', _boom)

        raised = False
        try:
            syc.loadData(jIn, quiet=True)
        except sy.SonicYangException:
            raised = True
        assert raised, "SonicYangException must still be raised even when quiet=True"

        msgs = [kw.get('msg', '') for (_a, kw) in calls] + [
            a[0] for (a, _kw) in calls if a
        ]
        assert not any('Data Loading Failed' in str(m) for m in msgs), \
            "quiet=True must suppress 'Data Loading Failed' sysLog on failure: {}".format(msgs)

        return

    def test_loaddata_default_logs_syslog_on_success(self, sonic_yang_data, monkeypatch):
        # Default (quiet=False) preserves existing behavior: the
        # "Try to load Data" sysLog call must be emitted on success.
        # monkeypatch.setattr cleanly reverts on teardown.
        test_file = sonic_yang_data['test_file']
        syc = sonic_yang_data['syc']
        jIn = json.loads(self.readIjsonInput(test_file, 'SAMPLE_CONFIG_DB_JSON'))

        calls = []
        monkeypatch.setattr(syc, 'sysLog',
                            lambda *a, **kw: calls.append((a, kw)))

        syc.loadData(jIn)

        msgs = [kw.get('msg', '') for (_a, kw) in calls] + [
            a[0] for (a, _kw) in calls if a
        ]
        assert any('Try to load Data' in str(m) for m in msgs), \
            "default quiet=False must log 'Try to load Data': {}".format(msgs)

        return

    def teardown_class(self):
        pass


class Test_SonicYang_UsesCompilation(object):
    @pytest.fixture
    def yang_s(self):
        yang_s = sy.SonicYang(str(_load_test_data()['yang_dir']))
        yang_s.loadYangModel()
        return yang_s

    @pytest.fixture
    def module(self, yang_s):
        return next(model['module'] for model in yang_s.yJson
                    if model['module']['@name'] == 'test-grouping')

    def _list_node(self, module):
        return module['container']['container']['list']

    @pytest.mark.parametrize("grouping, node_type", [
        ("group-with-container", "container"),
        ("group-with-list", "list"),
        ("nested-uses-group", "uses"),
    ])
    def test_grouping_preprocessing(self, yang_s, grouping, node_type):
        group = yang_s.preProcessedYang['grouping']['test-grouping'][grouping]
        assert node_type in group

    @pytest.mark.parametrize("node_type, name", [
        ("container", "settings"),
        ("list", "member"),
    ])
    def test_uses_clause_merges_children(self, module, node_type, name):
        children = self._list_node(module)[node_type]
        assert [child['@name'] for child in children] == [name]

    def test_uses_clause_merges_nested_uses(self, module):
        leaves = self._list_node(module)['leaf']
        assert {leaf['@name'] for leaf in leaves} == {
            'name', 'description', 'extra'
        }

    def test_uses_clause_removes_uses_key(self, module):
        assert 'uses' not in self._list_node(module)

    def test_uses_clause_in_notification(self, module):
        notification = module['notification']
        assert 'uses' not in notification
        assert {leaf['@name'] for leaf in notification['leaf']} == {
            'description', 'event-data'
        }

    def test_get_yang_model_preserves_uses(self, yang_s, module):
        raw = yang_s.get_yang_model('test-grouping')['module']
        assert [uses['@name'] for uses in self._list_node(raw)['uses']] == [
            'group-with-container', 'group-with-list', 'nested-uses-group'
        ]
        assert 'uses' not in self._list_node(module)

    def test_get_yang_model_returns_fresh_schema(self, yang_s, module):
        raw = yang_s.get_yang_model('test-grouping')['module']
        self._list_node(raw)['leaf']['@name'] = 'changed'
        fresh = yang_s.get_yang_model('test-grouping')['module']
        assert self._list_node(fresh)['leaf']['@name'] == 'name'
        assert self._list_node(module)['leaf'][0]['@name'] == 'name'

    def test_get_yang_model_missing(self, yang_s):
        assert yang_s.get_yang_model('not-a-loaded-module') is None
