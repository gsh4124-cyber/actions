#!/usr/bin/env python3
"""12 independent regressions for preserving protected source."""
import importlib.util, pathlib, unittest
path=pathlib.Path(__file__).with_name("revision_lock_gate.py")
spec=importlib.util.spec_from_file_location("revision_lock_gate",path)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class Cases(unittest.TestCase):
 b="protected intro\nSTART\nold issue\nEND\nprotected camera\n"
 r=[{"start":"START\n","end":"END\n"}]
 def blocked(self,s,r=None):
  with self.assertRaises(g.LockError):g.protect(self.b,s,self.r if r is None else r,"example")
 def test_01_unchanged(self):self.assertTrue(g.protect(self.b,self.b,self.r,"example")["same_as_baseline"])
 def test_02_local_fix(self):self.assertFalse(g.protect(self.b,self.b.replace("old issue","fixed issue"),self.r,"example")["same_as_baseline"])
 def test_03_intro_protected(self):self.blocked(self.b.replace("protected intro","other intro"))
 def test_04_camera_protected(self):self.blocked(self.b.replace("protected camera","other camera"))
 def test_05_missing_end(self):self.blocked(self.b.replace("END\n",""))
 def test_06_missing_start(self):self.blocked(self.b.replace("START\n",""))
 def test_07_no_edit_scope(self):self.blocked(self.b.replace("old issue","new issue"),[])
 def test_08_whole_new_video(self):self.blocked("new video entirely")
 def test_09_ambiguous_markers(self):self.blocked(self.b+"START\n")
 def test_10_missing_workflow_guard(self):
  with self.assertRaises(g.LockError):g.normalize_workflow(g.CHECKOUT+"      - name: Install Blender and FFmpeg\n")
 def test_11_guard_before_install(self):
  with self.assertRaises(g.LockError):g.normalize_workflow(g.FULL_CHECKOUT+"      - name: Install Blender and FFmpeg\n"+g.GUARD)
 def test_12_exact_workflow_normalization(self):
  old=g.CHECKOUT+"      - name: Install Blender and FFmpeg\n"
  self.assertEqual(g.normalize_workflow(g.FULL_CHECKOUT+g.GUARD+"      - name: Install Blender and FFmpeg\n"),old)
if __name__=="__main__":unittest.main(verbosity=2)
