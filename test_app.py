import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import main


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'DATABASE_URL':'','APP_PASSWORD':'','VERCEL':''})
        self.env.start()
        self.db_patch = patch.object(main, 'DB', Path(self.folder.name)/'test.sqlite3')
        self.db_patch.start()
        self.client = TestClient(main.app)
        self.client.__enter__()
    def tearDown(self):
        self.client.__exit__(None,None,None)
        main.engine_for.cache_clear()
        self.db_patch.stop()
        self.env.stop()
        self.folder.cleanup()
    def add(self, **overrides):
        r=self.client.post('/api/items',json={'title':'Example',**overrides})
        self.assertEqual(r.status_code,201,r.text)
        return r.json()
    def test_list_create_and_persistence(self):
        self.assertEqual(self.client.get('/api/items').json(),[])
        row=self.add(title='  First  ',body='details',due_date='2026-10-10')
        self.assertEqual(row['title'],'First')
        self.assertEqual(row['due_date'],'2026-10-10')
        note=self.add(kind='note',title='Idea',body='Keep this')
        with TestClient(main.app) as reopened:
            self.assertEqual(len(reopened.get('/api/items').json()),2)
        self.assertEqual(self.client.get('/api/items').headers['cache-control'],'no-store')
    def test_create_validation(self):
        for data in [{'title':' '},{'title':'x','due_date':'2026-02-30'},{'title':'x','kind':'other'},{'title':'x'*201},{'title':'x','body':'x'*20001}]:
            self.assertEqual(self.client.post('/api/items',json=data).status_code,422)
        self.assertEqual(self.client.get('/api/items').json(),[])
    def test_update_and_errors(self):
        row=self.add(due_date='2026-10-10')
        r=self.client.put('/api/items/'+str(row['id']),json={**row,'title':'Edited','done':True,'due_date':None})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['done'],1)
        self.assertIsNone(r.json()['due_date'])
        self.assertEqual(self.client.put('/api/items/'+str(row['id']),json={'title':'x','kind':'note'}).status_code,400)
        self.assertEqual(self.client.put('/api/items/'+str(row['id']),json={'title':' '}).status_code,422)
        self.assertEqual(self.client.put('/api/items/999999',json={'title':'x'}).status_code,404)
        note=self.add(kind='note')
        self.assertEqual(self.client.put('/api/items/'+str(note['id']),json={**note,'body':'Edited note'}).json()['body'],'Edited note')
    def test_reorder_and_conflicts(self):
        a=self.add();b=self.add();n=self.add(kind='note')
        self.assertEqual(self.client.put('/api/order',json={'kind':'task','ids':[b['id'],a['id']]}).status_code,200)
        for ids in [[a['id'],a['id']],[a['id']],[a['id'],n['id']],[999999,a['id']]]:
            self.assertEqual(self.client.put('/api/order',json={'kind':'task','ids':ids}).status_code,409)
        self.assertEqual([r['id'] for r in self.client.get('/api/items').json() if r['kind']=='task'],[b['id'],a['id']])
        self.assertEqual(self.client.put('/api/order',json={'kind':'note','ids':[n['id']]}).status_code,200)
        self.assertEqual(self.client.put('/api/order',json={'kind':'bad','ids':[]}).status_code,422)
    def test_delete(self):
        row=self.add()
        r=self.client.delete('/api/items/'+str(row['id']))
        self.assertEqual(r.status_code,204)
        self.assertEqual(r.content,b'')
        self.assertEqual(self.client.get('/api/items').json(),[])
        self.assertEqual(self.client.delete('/api/items/'+str(row['id'])).status_code,404)
    def test_public_editing_across_visitors(self):
        # Even a leftover password setting must not lock this public app.
        with patch.dict(os.environ,{'APP_PASSWORD':'old-unused-password'}):
            row=self.add()
            with TestClient(main.app) as visitor:
                self.assertEqual(visitor.get('/api/items').status_code,200)
                edited=visitor.put('/api/items/'+str(row['id']),json={'title':'Changed by visitor','done':True})
                self.assertEqual(edited.status_code,200)
                self.assertEqual(self.client.get('/api/items').json()[0]['done'],1)
                self.assertEqual(visitor.put('/api/order',json={'kind':'task','ids':[row['id']]}).status_code,200)
                self.assertEqual(visitor.delete('/api/items/'+str(row['id'])).status_code,204)
                self.assertEqual(self.client.get('/api/items').json(),[])
                self.assertEqual(visitor.post('/api/items',json={'kind':'note','title':'Public note'}).status_code,201)
    def test_cloud_requires_database(self):
        with patch.dict(os.environ,{'VERCEL':'1','DATABASE_URL':''}):
            self.assertEqual(self.client.get('/api/items').status_code,503)
        with patch.dict(os.environ,{'DATABASE_URL':'sqlite:///bad'}):
            self.assertEqual(self.client.get('/api/items').status_code,503)
        with patch.dict(os.environ,{'VERCEL':'1','DATABASE_URL':'postgresql://unused','APP_PASSWORD':''}):
            self.assertEqual(main.settings(),'postgresql://unused')
    def test_static_frontend(self):
        r=self.client.get('/')
        self.assertEqual(r.status_code,200)
        self.assertIn('Little List',r.text)

@unittest.skipUnless(os.environ.get('TEST_DATABASE_URL'),'No disposable PostgreSQL test database configured')
class PostgresEndpointTests(EndpointTests):
    def setUp(self):
        super().setUp()
        os.environ['DATABASE_URL']=os.environ['TEST_DATABASE_URL']
        with main.database() as conn:
            conn.execute(main.items.delete())

if __name__=='__main__': unittest.main()
