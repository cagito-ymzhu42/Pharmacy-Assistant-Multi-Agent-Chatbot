"""Offline regression checks using the real LangGraph and deterministic adapters."""
import ast
import contextlib
import copy
import io
import json
import sys
import types
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

class FakeLLM:
    def __init__(self):
        self.responses = []
    def invoke(self, prompt):
        return types.SimpleNamespace(content=self.responses.pop(0))

class FakeGraph:
    risks = []
    def query(self, query, params=None):
        if 'RETURN p.name as name' in query:
            return [{'name': '孕妇'}, {'name': '成人'}]
        return self.risks

llm, graph = FakeLLM(), FakeGraph()
config = types.ModuleType('core.config')
config.llm, config.graph = llm, graph
config.vectorstore = types.SimpleNamespace(similarity_search=lambda query, k: [])
sys.modules['core.config'] = config
from agents.workflow import app
from agents.agents.profile import profile_agent
from agents.agents.checker import checker_agent
from agents.agents.final_responder import final_responder
from core.catalog import canonical_drug_name, canonical_district
from tools.tools import check_nearby_pharmacy_stock
from agent_server import create_api

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        llm.responses = []
        graph.risks = []
        self.state = {'messages': [('user', 'Headache enquiry')],
                      'profile': {'age': '30', 'condition': 'headache', 'health_background': 'none'},
                      'candidates': [{'drug_name': '必理痛', 'reason': 'Reference candidate', 'score': .8}],
                      'checker_feedback': {'is_safe': True, 'risks': [], 'conclusion': 'Reference review completed.'},
                      'session_complete': False}
    def tearDown(self):
        self.stdout.__exit__(None, None, None)
    def test_profile_change_refreshes_recommendation(self):
        previous = copy.deepcopy(self.state)
        llm.responses = [json.dumps({'health_background': 'pregnant'})]
        update = profile_agent(self.state)
        self.assertEqual(update['candidates'], [])
        self.assertIsNone(update['checker_feedback'])
        self.assertEqual(self.state, previous)
    def test_location_only_preserves_review(self):
        llm.responses = [json.dumps({'region': 'Sha Tin'})]
        update = profile_agent(self.state)
        self.assertEqual(update['profile']['region'], '新界')
        self.assertNotIn('candidates', update)
    def test_graph_risk_overrides_model_approval(self):
        graph.risks = [{'population':'孕妇', 'risk':'Seeded caution'}]
        llm.responses = ['["孕妇"]', '["成人"]', json.dumps(self.state['checker_feedback'])]
        feedback = checker_agent(self.state)['checker_feedback']
        self.assertFalse(feedback['is_safe'])
        self.assertIn('Seeded caution', ' '.join(feedback['risks']))
    def test_tool_preserves_conversation(self):
        self.state['profile']['region'] = '新界'
        llm.responses = [json.dumps(self.state['profile']), 'The simulated inventory lists a store.']
        result = app.invoke(self.state)
        self.assertEqual(result['messages'][0], self.state['messages'][0])
        self.assertEqual(type(result['messages'][-2]).__name__, 'ToolMessage')
        self.assertTrue(result['session_complete'])
    def test_unknown_region_asks_followup(self):
        self.state['profile']['region'] = 'unknown'
        result = final_responder(self.state)
        self.assertIn('Which area', result['messages'][-1])
        self.assertFalse(result.get('session_complete', False))
    def test_aliases_reach_stock(self):
        self.assertEqual(canonical_drug_name('萨隆巴斯止痛贴'), '撒隆巴斯')
        self.assertEqual(canonical_district('Sha Tin'), '新界')
        stock = check_nearby_pharmacy_stock.invoke({'drug_name':'Salonpas', 'district':'Sha Tin'})
        self.assertIn('沙田新城市广场', stock)
    def test_graph_seed_merges_records(self):
        path = Path(__file__).resolve().parents[1] / 'data/neo4j_graph/build_kg.py'
        tree = ast.parse(path.read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        namespace = {'Neo4jGraph':object}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
        calls=[]
        recorder=types.SimpleNamespace(query=lambda query, **kwargs:calls.append(query))
        namespace[function.name](recorder)
        self.assertEqual(len(calls), 69)
        self.assertTrue(all('MERGE' in query and 'DELETE' not in query for query in calls))
    def test_demo_serves_ui_and_reports_mode(self):
        with TestClient(create_api(demo=True)) as client:
            self.assertEqual(client.get('/status').json(), {'mode':'demo','live_chat':False})
            self.assertIn('Care, with context.', client.get('/ui/').text)
            self.assertEqual(client.post('/chat',json={'query':'Hello'}).status_code,503)
    def test_live_api_multiturn_real_graph(self):
        with TestClient(create_api(workflow=app)) as client:
            llm.responses = [json.dumps({'condition':'headache'}), 'How old are you?']
            first = client.post('/chat',json={'query':'I have a headache'}).json()
            self.assertEqual(first['steps'], ['profile_agent','clarification_agent'])
            self.assertFalse(first['session_complete'])
            profile=dict(self.state['profile'], region='Sha Tin')
            llm.responses = [json.dumps(profile), 'Headache reference search',
                             json.dumps({'recommended_drugs':self.state['candidates']}),
                             '[]','["成人"]',json.dumps(self.state['checker_feedback']),
                             'Simulated inventory example. Confirm with the pharmacy.']
            response=client.post('/chat',json={'session_id':first['session_id'],'query':'I am 30, no conditions, in Sha Tin'})
            self.assertEqual(response.status_code,200)
            second=response.json()
            self.assertTrue(second['session_complete'])
            self.assertIn('tool_node',second['steps'])
            self.assertEqual(second['profile']['region'],'新界')
            self.assertEqual(second['session_id'],first['session_id'])
            self.assertEqual(client.delete('/sessions/'+first['session_id']).status_code,200)
    def test_blank_message_is_rejected(self):
        with TestClient(create_api(demo=True)) as client:
            self.assertEqual(client.post('/chat',json={'query':'  '}).status_code,422)

if __name__ == '__main__':
    unittest.main()
