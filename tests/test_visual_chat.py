import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from visual_chat import checked_messages,checked_review,rendered,parse_json

def sample():
 return {'chat_title':'测试朋友','uncertain':False,'messages':[
 {'id':'m1','side':'me','kind':'text','text':'今晚早睡','bbox':[.6,.15,.9,.25],'uncertain':False},
 {'id':'m2','side':'them','kind':'sticker','text':'','description':'猫咪翻白眼','interpretation':'可能在吐槽','bbox':[.1,.4,.4,.7],'uncertain':False}],
 'last_visible_id':'m2','reply_target_id':'m2'}
class VisualTests(unittest.TestCase):
 def test_wordless_last_sticker_is_the_reply_target(self):
  title,msgs=checked_messages(sample());self.assertEqual(msgs[-1]['id'],'m2');self.assertIn('猫咪',rendered(msgs[-1]))
 def test_redundant_model_target_cannot_select_older_text(self):
  # A redundant advisory pointer used to randomly reject otherwise valid frames.
  data=sample();data['reply_target_id']='m1'
  _,messages=checked_messages(data)
  self.assertEqual(messages[-1]['id'],'m2')
  self.assertEqual(messages[-1]['kind'],'sticker')
 def test_transcript_needs_no_model_selected_reply_target(self):
  data=sample();del data['reply_target_id']
  _,messages=checked_messages(data)
  self.assertEqual(messages[-1]['id'],'m2')
 def test_review_cannot_approve_older_message_as_last(self):
  data=sample();data['reply_target_id']='m1'
  checked_messages(data)
  wrong={'ok':True,'chat_title':'测试朋友','last_visible_id':'m1','last_side':'them','last_kind':'sticker'}
  with self.assertRaisesRegex(ValueError,'校验未通过'):checked_review(data,wrong)
 def test_my_last_message_stops_generation(self):
  data=sample();data['messages'][-1]['side']='me'
  with self.assertRaisesRegex(ValueError,'你发出的'):checked_messages(data)
 def test_order_must_match_geometry(self):
  data=sample();data['messages'].reverse()
  with self.assertRaisesRegex(ValueError,'顺序'):checked_messages(data)
 def test_blank_media_is_not_silently_dropped(self):
  data=sample();data['messages'][-1]['description']=''
  with self.assertRaisesRegex(ValueError,'空白媒体'):checked_messages(data)
 def test_unreadable_latest_media_blocks(self):
  for kind in ('audio','file','card','video','unknown'):
   data=sample();data['messages'][-1]['kind']=kind
   with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'最后一条'):checked_messages(data)
 def test_unknown_side_and_uncertain_block(self):
  for change in ({'side':'unknown'},{'uncertain':True}):
   data=sample();data['messages'][-1].update(change)
   with self.assertRaisesRegex(ValueError,'不确定'):checked_messages(data)
 def test_duplicate_id_rejected(self):
  data=sample();data['messages'][-1]['id']='m1'
  with self.assertRaisesRegex(ValueError,'重复'):checked_messages(data)
 def test_last_pointer_mismatch_rejected(self):
  data=sample();data['last_visible_id']='m1'
  with self.assertRaisesRegex(ValueError,'最后消息'):checked_messages(data)
 def test_quote_remains_context_inside_same_message(self):
  m=sample()['messages'][1];m['quote']='你说你要早睡';self.assertIn('不是新消息',rendered(m))
 def test_review_must_agree_with_target_title_side_and_kind(self):
  data=sample();ok={'ok':True,'chat_title':'测试朋友','last_visible_id':'m2','last_side':'them','last_kind':'sticker','reply_target_id':'m2'}
  checked_review(data,ok)
  for k,v in [('ok',False),('chat_title','其他会话'),('last_visible_id','m1'),('last_side','me'),('last_kind','text')]:
   wrong=ok|{k:v}
   with self.subTest(key=k),self.assertRaisesRegex(ValueError,'校验未通过'):checked_review(data,wrong)
 def test_json_array_is_not_accepted_as_transcript(self):
  with self.assertRaises(ValueError):parse_json('[]')
if __name__=='__main__':unittest.main()
